# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import logging
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from communication.exceptions import NotEnoughSpaceException
from communication.model_registration_utils import ModelMapper, ProjectMapper
from communication.rest_data_validator import DeploymentPackageRESTValidator
from communication.rest_views.project_rest_views import ProjectRESTViews
from entities.deployment import ModelIdentifier
from managers.project_manager import ProjectManager
from resource_management.deployment_package_manager import DeploymentPackageManager
from service.label_schema_service import LabelSchemaService

from geti_fastapi_tools.exceptions import BadRequestException, ModelNotFoundException
from geti_telemetry_tools import unified_tracing
from geti_types import CTX_SESSION_VAR, ID, ProjectIdentifier
from grpc_interfaces.model_registration.client import ModelRegistrationClient
from sc_sdk.entities.label_schema import LabelSchemaView
from sc_sdk.entities.model import NullModel
from sc_sdk.entities.model_storage import ModelStorageIdentifier
from sc_sdk.entities.project import Project
from sc_sdk.repos import ModelRepo
from sc_sdk.utils.filesystem import check_free_space_for_operation

export_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="Deployment_package_worker")
logger = logging.getLogger(__name__)

DEPLOYMENT_FILENAME_TEMPLATE = "Deployment-%s"


class DeploymentPackageRESTController:
    @staticmethod
    def _check_space_and_validate(deployment_package_json: dict) -> None:
        check_free_space_for_operation(operation="Deployment Package", exception_type=NotEnoughSpaceException)

        DeploymentPackageRESTValidator().validate_deployment_package(deployment_package_json)

    @staticmethod
    def _parse_model_ids(deployment_package_json: dict) -> list[ModelIdentifier]:
        model_identifiers = []
        for model_dict in deployment_package_json["models"]:
            model_identifiers.append(
                ModelIdentifier(
                    model_storage_id=ID(model_dict["model_group_id"]),
                    model_id=ID(model_dict["model_id"]),
                )
            )
        return model_identifiers

    @staticmethod
    @unified_tracing
    def download_ovms_package(
        project_identifier: ProjectIdentifier,
        deployment_package_json: dict,
    ) -> Path:
        """
        Collects the models to be included in the deployment package
        Triggers the asynchronous zip file preparation

        :param project_identifier: the ID of the project of the models
        :param deployment_package_json: the REST request containing the models to export and type of deployment package
        :return: ovms package file path
        """
        DeploymentPackageRESTController._check_space_and_validate(deployment_package_json)

        model_identifiers = DeploymentPackageRESTController._parse_model_ids(deployment_package_json)
        project: Project = ProjectManager.get_project_by_id(project_identifier.project_id)
        models_task_nodes_pairs = []
        for model_identifier in model_identifiers:
            model_storage_identifier = ModelStorageIdentifier(
                workspace_id=project.workspace_id,
                project_id=project.id_,
                model_storage_id=model_identifier.model_storage_id,
            )
            model = ModelRepo(model_storage_identifier).get_by_id(model_identifier.model_id)
            if isinstance(model, NullModel):
                raise ModelNotFoundException(model_id=model_identifier.model_id)
            task_node = project.get_trainable_task_node_by_id(model.model_storage.task_node_id)
            if task_node is None:
                raise BadRequestException(
                    f"Model storage `{model.model_storage.name}` is not "
                    f"connected to any task in project `{project.name}`."
                    f"Model Storage ID: `{model.model_storage.id_}`, Project ID `{project.id_}`."
                )
            models_task_nodes_pairs.append((model, task_node))

        session = CTX_SESSION_VAR.get()
        proto_project = ProjectMapper.forward(project)
        proto_models = [
            ModelMapper.forward(
                model=model,
                organization_id=session.organization_id,
                workspace_id=session.workspace_id,
                project_id=project.id_,
                task_id=task_node.id_,
                optimized_model_id=model.id_,
            )
            for model, task_node in models_task_nodes_pairs
        ]

        tmp_dir = tempfile.mkdtemp()
        with ModelRegistrationClient(metadata_getter=lambda: session.as_tuple()) as client:
            output_dir = Path(tmp_dir)
            output_archive = output_dir.joinpath(DEPLOYMENT_FILENAME_TEMPLATE % f"{proto_project.name}.zip")
            client.download_graph(project=proto_project, models=proto_models, output_path=output_archive)

        return output_archive

    @staticmethod
    @unified_tracing
    def download_geti_sdk_package(
        project_identifier: ProjectIdentifier,
        deployment_package_json: dict,
    ) -> Path:
        """
        Collects the models to be included in the deployment package
        Triggers the asynchronous zip file preparation

        :param project_identifier: the ID of the project of the models
        :param organization_id: the ID of the organization
        :param deployment_package_json: the REST request containing the models to export and type of deployment package
        :return: geti sdk package file path
        """
        DeploymentPackageRESTController._check_space_and_validate(deployment_package_json)

        model_identifiers = DeploymentPackageRESTController._parse_model_ids(deployment_package_json)
        project: Project = ProjectManager.get_project_by_id(project_identifier.project_id)

        label_schema_per_task = DeploymentPackageRESTController._get_label_schema_per_task(project)
        project_rest_view = ProjectRESTViews.project_to_rest(
            organization_id=CTX_SESSION_VAR.get().organization_id,
            project=project,
            label_schema_per_task=label_schema_per_task,
            storage_info={},
        )

        return DeploymentPackageManager.prepare_geti_sdk_package(
            project=project,
            project_rest_view=project_rest_view,
            model_identifiers=model_identifiers,
        )

    @staticmethod
    def _get_label_schema_per_task(project: Project) -> dict[ID, LabelSchemaView]:
        label_schema_per_task = {}
        for task_node in project.task_graph.tasks:
            if task_node.task_properties.is_trainable:
                label_schema_per_task[task_node.id_] = LabelSchemaService.get_latest_label_schema_for_task(
                    project_identifier=project.identifier,
                    task_node_id=task_node.id_,
                )
        return label_schema_per_task
