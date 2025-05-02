# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import http
import io
import logging
import os
from typing import Any
from zipfile import ZipFile, ZipInfo

from communication.exceptions import ModelStorageNotActivableException, PurgedModelException, TaskNotFoundException
from communication.model_registration_utils import ModelMapper, ProjectMapper
from communication.rest_views.model_rest_views import ModelRestInfo, ModelRESTViews
from communication.rest_views.statistics_rest_views import StatisticsRESTViews
from service.label_schema_service import LabelSchemaService
from usecases.statistics import StatisticsUseCase

from geti_fastapi_tools.exceptions import BadRequestException, GetiBaseException, ModelNotFoundException
from geti_kafka_tools import publish_event
from geti_telemetry_tools import ENABLE_METRICS, unified_tracing
from geti_telemetry_tools.metrics import ModelExportsCounterAttributes, model_exports_counter
from geti_types import CTX_SESSION_VAR, ID, ProjectIdentifier
from grpc_interfaces.model_registration.client import ModelRegistrationClient
from iai_core_py.entities.label_schema import LabelSchema
from iai_core_py.entities.model import Model, ModelFormat, ModelOptimizationType, NullModel
from iai_core_py.entities.model_storage import ModelStorageIdentifier
from iai_core_py.entities.project import Project
from iai_core_py.repos import DatasetRepo, LabelSchemaRepo, ModelRepo, ModelStorageRepo, ProjectRepo
from iai_core_py.repos.model_repo import ModelStatusFilter
from iai_core_py.services import ModelService
from iai_core_py.utils.exceptions import (
    PurgeActiveModelException,
    PurgeLatestModelException,
    PurgeOptimizedModelException,
    SDKModelNotFoundException,
)

logger = logging.getLogger(__name__)

# This value is determined by the optimization team.
FILTER_PRUNING_ENABLED_LIMIT = 1000

MODEL_FORMAT_TO_TITLE = {
    ModelFormat.BASE_FRAMEWORK: "PyTorch",
    ModelFormat.ONNX: "ONNX",
    ModelFormat.OPENVINO: "OpenVINO",
}

MODEL_REGISTRATION_SERVICE_GRPC_ADDRESS = os.getenv("MODEL_REGISTRATION_SERVICE", "localhost:5555")


class ModelRESTController:
    @staticmethod
    @unified_tracing
    def get_model_statistics(
        project_id: ID,
        model_storage_id: ID,
        model_id: ID,
    ) -> dict[str, list[dict]]:
        """
        Returns model statistics such as performance, training curves and other metrics.

        :param project_id: ID of the project the model belongs to
        :param model_storage_id: ID of the ModelStorage that the model belongs to
        :param model_id: ID of the model to get stats for
        """
        project = ProjectRepo().get_by_id(project_id)
        model_storage_identifier = ModelStorageIdentifier(
            workspace_id=project.workspace_id,
            project_id=project.id_,
            model_storage_id=model_storage_id,
        )
        model = ModelRepo(model_storage_identifier).get_by_id(model_id)
        if isinstance(model, NullModel):
            raise ModelNotFoundException(model_id=model_id)

        statistics_items = StatisticsUseCase.get_model_stats(project, model)
        rest_output = []

        labels = model.get_label_schema().get_labels(include_empty=True)

        for item in statistics_items:
            rest_output.extend(StatisticsRESTViews.metrics_groups_to_rest(metrics_groups=item.charts, labels=labels))
        return {"model_statistics": rest_output}

    @staticmethod
    @unified_tracing
    def get_all_models(project_id: ID, active_only: bool) -> dict[str, list[dict[str, Any]]]:
        """
        Get a REST view of all models for a project. In the current implementation, this endpoint only works if
        the flag 'active_only' is set to True.

        :param project_id: ID of the project the models belong to
        :param active_only: If set to True, return only the active inference models for the project
        :return: REST view of the model storage
        """
        if not active_only:
            raise NotImplementedError(
                "Getting all models is currently not supported, this endpoint is only supportedfor active_only=true."
            )
        project = ProjectRepo().get_by_id(id_=project_id)

        task_nodes = project.get_trainable_task_nodes()

        model_rest_views = []
        for task_node in task_nodes:
            active_model = ModelService.get_inference_active_model(
                project_identifier=project.identifier,
                task_node_id=task_node.id_,
            )
            task_node_schema = LabelSchemaService.get_latest_label_schema_for_task(
                project_identifier=project.identifier,
                task_node_id=task_node.id_,
            )
            requested_models = [active_model] if not isinstance(active_model, NullModel) else []
            # Here the implementation can be added to return all models once active_only=False is allowed.

            for model in requested_models:
                is_label_schema_in_sync = ModelRESTController._compare_labels_sync_status(
                    project_identifier=project.identifier,
                    label_schema_1=task_node_schema,
                    label_schema_id_2=model.label_schema_id,
                )
                model_rest_views.append(
                    ModelRESTViews.model_to_rest(
                        model=model,
                        model_performance=StatisticsUseCase.get_model_performance(
                            model=model, project_identifier=project.identifier
                        ),
                        is_label_schema_in_sync=is_label_schema_in_sync,
                        task_node_id=task_node.id_,
                        active_model=active_model,
                    )
                )

        return {"models": model_rest_views}

    @staticmethod
    @unified_tracing
    def get_all_model_groups(
        project_id: ID,
        task_id: ID | None = None,
        include_lifecycle_stage: bool = False,  # TODO CVS-159532 remove this parameter
    ) -> dict[str, Any]:
        """
        Get a REST view of the active model storages (one per-task) of a given project.

        It includes the full history of models, but it excludes the optimized ones.

        :param project_id: ID of the project the models belong to
        :param task_id: Optional, ID of the task to get the model groups for
        :param include_lifecycle_stage: Whether to include the lifecycle stage in the rest view
        :return: REST view of the list of model storages
        """
        project = ProjectRepo().get_by_id(project_id)

        task_nodes = project.get_trainable_task_nodes()
        if task_id is not None:
            task_nodes = [task for task in task_nodes if task.id_ == task_id]
            if not task_nodes:
                raise TaskNotFoundException(task_id)

        model_storage_info: list[dict] = []
        for task_node in task_nodes:
            base_active_model = ModelService.get_inference_active_model(
                project_identifier=project.identifier,
                task_node_id=task_node.id_,
            ).get_base_model()
            model_storages = list(
                ModelStorageRepo(project_identifier=project.identifier).get_by_task_node_id(task_node_id=task_node.id_)
            )
            for model_storage in model_storages:
                per_model_info = ModelRESTController._get_per_model_info(
                    task_node_id=task_node.id_,
                    model_storage_identifier=model_storage.identifier,
                )
                if len(per_model_info) > 0:
                    model_storage_dict = ModelRESTViews.model_storage_to_rest(
                        model_storage=model_storage,
                        per_model_info=per_model_info,
                        task_node_id=task_node.id_,
                        active_model=base_active_model,
                        include_lifecycle_stage=include_lifecycle_stage,
                    )
                    model_storage_info.append(model_storage_dict)
        return {"model_groups": model_storage_info}

    @staticmethod
    @unified_tracing
    def get_model_group(
        project_id: ID,
        model_storage_id: ID,
        include_lifecycle_stage: bool = False,  # TODO CVS-159532 remove this parameter
    ) -> dict[str, Any]:
        """
        Get a REST view of a model storage and its models.

        It includes all the revisions of that model (base framework only).
        It doesn't include optimized models.

        :param project_id: ID of the project the models belong to
        :param model_storage_id: ID of the model storage
        :param include_lifecycle_stage: Whether to include the lifecycle stage in the rest view
        :return: REST view of the model storage
        """
        project = ProjectRepo().get_by_id(project_id)

        # Check that model storage exists and fetch it
        model_storage = ModelStorageRepo(project.identifier).get_by_id(model_storage_id)
        task_node = next(task for task in project.get_trainable_task_nodes() if task.id_ == model_storage.task_node_id)
        if task_node is None:
            raise BadRequestException(
                f"Model storage `{model_storage.name}` is not "
                f"connected to any task in project `{project.name}`."
                f"Model Storage ID: `{model_storage.id_}`, Project ID `{project.id_}`."
            )
        task_node = next(task for task in project.get_trainable_task_nodes() if task.id_ == model_storage.task_node_id)
        if task_node is None:
            raise BadRequestException(
                f"Model storage `{model_storage.name}` is not "
                f"connected to any task in project `{project.name}`."
                f"Model Storage ID: `{model_storage.id_}`, Project ID `{project.id_}`."
            )
        base_active_model = ModelService.get_inference_active_model(
            project_identifier=project.identifier,
            task_node_id=task_node.id_,
        ).get_base_model()

        per_model_info = ModelRESTController._get_per_model_info(
            task_node_id=task_node.id_,
            model_storage_identifier=model_storage.identifier,
        )

        return ModelRESTViews.model_storage_to_rest(
            model_storage=model_storage,
            per_model_info=per_model_info,
            task_node_id=task_node.id_,
            active_model=base_active_model,
            include_lifecycle_stage=include_lifecycle_stage,
        )

    @staticmethod
    @unified_tracing
    def get_model_detail(
        project_id: ID,
        model_storage_id: ID,
        model_id: ID,
    ) -> dict[str, Any]:
        """
        Gets detailed information for a model.

        It includes all the revisions of that model (base framework only)
        It includes the final optimized models that derive from this model,
        but not the intermediate optimized models used to produce these.

        :param project_id: ID of the project the model belongs to
        :param model_storage_id: ID of the ModelStorage that the model belongs to
        :param model_id: ID of the model to be pulled
        :return: REST view of the model details
        """
        project = ProjectRepo().get_by_id(project_id)
        dataset_storage = project.get_training_dataset_storage()

        model_storage_identifier = ModelStorageIdentifier(
            workspace_id=project.workspace_id,
            project_id=project.id_,
            model_storage_id=model_storage_id,
        )
        model = ModelRepo(model_storage_identifier).get_by_id(model_id)
        if isinstance(model, NullModel):
            raise ModelNotFoundException(model_id=model_id)

        base_model_id = (
            model.id_ if model.optimization_type == ModelOptimizationType.NONE else model.previous_trained_revision_id
        )

        optimized_models = ModelRepo(model.model_storage_identifier).get_optimized_models_by_trained_revision_id(
            trained_revision_id=base_model_id,
        )
        task_node = next(
            (task for task in project.get_trainable_task_nodes() if task.id_ == model.model_storage.task_node_id),
            None,
        )
        if task_node is None:
            raise BadRequestException(
                f"Model storage `{model.model_storage.name}` is not "
                f"connected to any task in project `{project.name}`."
                f"Model Storage ID: `{model.model_storage.id_}`, Project ID `{project.id_}`."
            )

        performance = StatisticsUseCase.get_model_performance(model=model, project_identifier=project.identifier)
        dataset_counts = DatasetRepo(dataset_storage.identifier).count_per_media_type(dataset_id=model.train_dataset_id)
        optimized_per_model_performance = tuple(
            (
                opt_model,
                StatisticsUseCase.get_model_performance(
                    model=opt_model,
                    project_identifier=project.identifier,
                ),
            )
            for opt_model in optimized_models
        )

        task_node_schema = LabelSchemaService.get_latest_label_schema_for_task(
            project_identifier=project.identifier,
            task_node_id=task_node.id_,
        )
        is_label_schema_in_sync = ModelRESTController._compare_labels_sync_status(
            project_identifier=project.identifier,
            label_schema_1=task_node_schema,
            label_schema_id_2=model.label_schema_id,
        )

        model_storage_identifier = ModelStorageIdentifier(
            workspace_id=project.workspace_id,
            project_id=project.id_,
            model_storage_id=model_storage_id,
        )
        return ModelRESTViews.model_info_to_rest(
            model=model,
            model_performance=performance,
            is_label_schema_in_sync=is_label_schema_in_sync,
            dataset_storage_id=dataset_storage.id_,
            dataset_counts=dataset_counts,
            optimized_per_model_performance=optimized_per_model_performance,
            total_disk_size=ModelService.get_model_size(model=model, model_storage_identifier=model_storage_identifier),
        )

    @staticmethod
    @unified_tracing
    def export_model(project_id: ID, model_storage_id: ID, model_id: ID, model_only: bool) -> tuple[io.BytesIO, str]:
        """
        Exports model/code from 3 different model types: OpenVINO, PyTorch, and ONNX.
        OpenVINO and ONNX are optimized models, whereas PyTorch is a base model.

        Exportable code can only come from an OpenVINO optimized model.
        ONNX is considered an optimized model and belongs in the optimized/models/export
        endpoint, however it does not support exportable code.

        Since PyTorch is a base model, it is only reachable through the models/export
        endpoint. This will always export just the model.

        Which model exports what is shown in the grid below

                         | OpenVINO | PyTorch | ONNX
        ________________________________________________
        model_only=True  | MODEL    | MODEL   | MODEL
        model_only=False | CODE     | *       | MODEL

        *this scenario is not possible as PyTorch always exports with model_only=True

        :param project_id: ID of the project the model belongs to
        :param model_storage_id: ID of the ModelStorage that the model belongs to
        :param model_id: ID of the model to be exported.
        :param model_only: If True, export only the model files without the sample code to run it
        :return: Exported model zip file
        """
        project = ProjectRepo().get_by_id(project_id)

        model_storage_identifier = ModelStorageIdentifier(
            workspace_id=project.workspace_id,
            project_id=project.id_,
            model_storage_id=model_storage_id,
        )
        model = ModelRepo(model_storage_identifier).get_by_id(model_id)
        if isinstance(model, NullModel):
            raise ModelNotFoundException(model_id=model_id)
        if model.purge_info.is_purged:
            raise PurgedModelException("Can not export a purged model since its weights are deleted.")
        try:
            model_title = MODEL_FORMAT_TO_TITLE[model.model_format]
        except ValueError:
            raise ValueError(f"Exporting in {model.model_format.name} format is not supported")
        if model.model_format is ModelFormat.OPENVINO and not model_only:
            output_bytes = io.BytesIO(model.exportable_code)  # type: ignore
            file_name = f"{model_title}_exportable_code.zip"
        else:
            output_bytes = io.BytesIO()
            with ZipFile(output_bytes, "w") as zf:
                files_to_export = model.model_adapters.items()
                for filename, adapter in files_to_export:
                    info = ZipInfo(filename)
                    zf.writestr(info, adapter.data)
            output_bytes.seek(0)
            file_name = f"{model_title}_model.zip"

        if ENABLE_METRICS:
            model_exports_counter.add(
                1,
                ModelExportsCounterAttributes(
                    model_architecture=model.model_storage.model_template.name,
                    format=model.model_format.name,
                    precision=model.precision[0].name,
                ).to_dict(),
            )

        return output_bytes, file_name

    @staticmethod
    @unified_tracing
    def _get_per_model_info(
        task_node_id: ID,
        model_storage_identifier: ModelStorageIdentifier,
    ) -> tuple[ModelRestInfo, ...]:
        """
        Get all the models in the model storage and bundles them with their performance.

        :param task_node_id: ID of the task node relative to the models
        :param model_storage_identifier: Identifier of the model storage which contains the models
        :return: a sequence of tuples that maps each model, contained in the model
            storage, to its (equivalent) performance, to its label schema sync status and to its
        """
        project_identifier = ProjectIdentifier(
            workspace_id=model_storage_identifier.workspace_id,
            project_id=model_storage_identifier.project_id,
        )
        task_node_schema = LabelSchemaService.get_latest_label_schema_for_task(
            project_identifier=project_identifier,
            task_node_id=task_node_id,
        )
        models = ModelRepo(model_storage_identifier).get_all_by_status_and_type(
            model_status_filter=ModelStatusFilter.IMPROVED,
            include_optimized_models=False,
        )

        return tuple(
            ModelRestInfo(
                model=model,
                performance=StatisticsUseCase.get_model_performance(model=model, project_identifier=project_identifier),
                is_label_schema_in_sync=ModelRESTController._compare_labels_sync_status(
                    project_identifier=project_identifier,
                    label_schema_1=task_node_schema,
                    label_schema_id_2=model.label_schema_id,
                ),
            )
            for model in models
        )

    @classmethod
    def activate_model_storage(
        cls,
        workspace_id: ID,
        project_id: ID,
        model_storage_id: ID,
        include_lifecycle_stage: bool = False,  # TODO CVS-159532 remove this parameter
    ) -> dict[str, Any]:
        """
        Sets the model storage as the active one for its task node.
        Registers the newly activated model using the inference gateway if "ModelMesh" is active;
        otherwise, a Kafka event "model_activated" is produced to notify the director MS of the activation.

        :param workspace_id: ID of the workspace the project belongs to
        :param project_id: ID of the project
        :param model_storage_id: ID of the model storage to activate
        :param include_lifecycle_stage: Whether to include the lifecycle stage in the rest view
        :return: REST view of the newly activated model storage
        """
        project = ProjectRepo().get_by_id(project_id)
        model_storage = ModelStorageRepo(project.identifier).get_by_id(model_storage_id)
        task_node_id = model_storage.task_node_id

        # Validate model storage belongs to project
        if project.get_trainable_task_node_by_id(task_node_id) is None:
            raise TaskNotFoundException(task_node_id)

        if not ModelService.is_model_storage_activable(model_storage):
            raise ModelStorageNotActivableException(model_storage.id_)
        ModelService.activate_model_storage(model_storage=model_storage)

        base_active_model = ModelService.get_inference_active_model(
            project_identifier=project.identifier,
            task_node_id=task_node_id,
        ).get_base_model()
        inference_active_model = ModelService.get_inference_active_model(
            project_identifier=project.identifier,
            task_node_id=task_node_id,
        )

        cls._register_model(
            project=project,
            model=base_active_model,
            optimized_model_id=inference_active_model.id_,
            task_id=task_node_id,
        )

        publish_event(
            topic="model_activated",
            body={
                "workspace_id": str(workspace_id),
                "project_id": str(project_id),
                "task_node_id": str(model_storage.task_node_id),
                "model_storage_id": str(model_storage_id),
                "base_model_id": str(base_active_model.id_),
                "inference_model_id": str(inference_active_model.id_),
            },
            headers_getter=lambda: CTX_SESSION_VAR.get().as_list_bytes(),
        )

        per_model_info = ModelRESTController._get_per_model_info(
            task_node_id=task_node_id,
            model_storage_identifier=model_storage.identifier,
        )
        return ModelRESTViews.model_storage_to_rest(
            model_storage=model_storage,
            per_model_info=per_model_info,
            task_node_id=task_node_id,
            active_model=base_active_model,
            include_lifecycle_stage=include_lifecycle_stage,
        )

    @staticmethod
    def _register_model(
        project: Project,
        model: Model,
        optimized_model_id: ID,
        task_id: ID,
    ) -> None:
        """
        Registers a trained model using the model registration service. If necessary, a pipeline is also registered.

        :param project: Project containing the model.
        :param model: Trained model to register.
        :param optimized_model_id: ID of the MO optimized model, used for inference.
        :param task_id: ID of the task associated with the model.
        """
        logger.info(
            "Registering model with ID `%s` for task node with ID `%s`.",
            model.id_,
            task_id,
        )
        session = CTX_SESSION_VAR.get()
        trainable_task_ids = [node.id_ for node in project.get_trainable_task_nodes()]

        with ModelRegistrationClient(metadata_getter=lambda: session.as_tuple()) as client:
            proto_project = ProjectMapper.forward(project)
            proto_model = ModelMapper.forward(
                model=model,
                organization_id=session.organization_id,
                workspace_id=session.workspace_id,
                project_id=project.id_,
                task_id=task_id,
                optimized_model_id=optimized_model_id,
            )
            if len(trainable_task_ids) == 1:
                # Single task project: only register '-active' model
                client.register(
                    name=f"{str(project.id_)}-active",
                    project=proto_project,
                    models=[proto_model],
                    override=True,
                )
                return

            # Task-chain project: register both the model for the task (-<task>) and for the pipeline ('-active')
            client.register(
                name=f"{str(project.id_)}-{str(task_id)}",
                project=proto_project,
                models=[proto_model],
                override=True,
            )

            other_task_id = trainable_task_ids[0] if trainable_task_ids[0] != task_id else trainable_task_ids[1]
            other_task_active_model = ModelService.get_inference_active_model(
                project_identifier=project.identifier,
                task_node_id=other_task_id,
            ).get_base_model()

            other_task_inference_active_model = ModelService.get_inference_active_model(
                project_identifier=project.identifier,
                task_node_id=other_task_id,
            )
            other_task_proto_model = ModelMapper.forward(
                model=other_task_active_model,
                organization_id=session.organization_id,
                workspace_id=session.workspace_id,
                project_id=project.id_,
                task_id=other_task_id,
                optimized_model_id=other_task_inference_active_model.id_,
            )

            if isinstance(other_task_inference_active_model, NullModel):
                if task_id == trainable_task_ids[0]:
                    # Downstream task has no model yet, we register the model for the
                    # first task as the full active pipeline ('-active')
                    logger.info(
                        "The downstream model in the task chain is not trained yet, "
                        "registering the available upstream model as active pipeline."
                    )
                    client.register(
                        name=f"{str(project.id_)}-active",
                        project=proto_project,
                        models=[proto_model],
                        override=True,
                    )
                else:
                    # Only the downstream task has a trained model, normally this should never happen
                    logger.warning(
                        "Unexpected scenario: neither model in the chain is trained. Skipping pipeline registration."
                    )
                return
            client.register(
                name=f"{str(project.id_)}-active",
                project=proto_project,
                models=[other_task_proto_model, proto_model],
                override=True,
            )

    @staticmethod
    def purge_model(
        workspace_id: ID,
        project_id: ID,
        model_storage_id: ID,
        model_id: ID,
        user_id: ID,
    ) -> None:
        """
        Purges the binaries of a model and its optimized models and saves the updated models in a purged state. This
        entails model weights, linked optimized model weights and exportable code. Only allowed on base models which are
        not the active model or the latest model.

        :param workspace_id: ID of the workspace containing the model.
        :param project_id: ID of the project containing the model.
        :param model_storage_id: ID of the model storage containing the model to purge.
        :param model_id: ID of the model to purge
        :param user_id: ID of the user that requested to purge the model
        """
        try:
            ModelService.purge_model_binaries(
                workspace_id=workspace_id,
                project_id=project_id,
                model_storage_id=model_storage_id,
                model_id=model_id,
                user_id=user_id,
            )
        except (
            PurgeOptimizedModelException,
            PurgeActiveModelException,
            PurgeLatestModelException,
        ) as e:
            raise PurgedModelException(message=str(e))
        except SDKModelNotFoundException as e:
            raise GetiBaseException(
                str(e),
                error_code="model_not_found",
                http_status=http.HTTPStatus.NOT_FOUND,
            )

    @staticmethod
    @unified_tracing
    def _compare_labels_sync_status(
        project_identifier: ProjectIdentifier,
        label_schema_1: LabelSchema,
        label_schema_id_2: ID,
    ) -> bool:
        """
        Checks if two LabelSchemas are in sync.

        Objects are in sync if their IDs match, or their label IDs match.
        Sync is not dependent on label attributes such as color or hotkey.

        :param project_identifier: Identifier of the project containing the LabelSchemas
        :param label_schema_1: the first LabelSchema
        :param label_schema_id_2: ID of the second LabelSchema
        :return: True if objects are in sync, False otherwise
        """
        if label_schema_1.id_ == label_schema_id_2:  # fast path for identity
            return True

        repo = LabelSchemaRepo(project_identifier)
        label_schema_2 = repo.get_by_id(label_schema_id_2)
        label_groups_1 = label_schema_1.get_groups(include_empty=True)
        label_groups_2 = label_schema_2.get_groups(include_empty=True)

        if len(label_groups_1) != len(label_groups_2):  # fast path for groups added/removed
            return False

        # General case: verify that the label groups and their labels match
        group_to_labels_1 = {group.name: {label.id_ for label in group.labels} for group in label_groups_1}
        group_to_labels_2 = {group.name: {label.id_ for label in group.labels} for group in label_groups_2}
        return group_to_labels_1 == group_to_labels_2
