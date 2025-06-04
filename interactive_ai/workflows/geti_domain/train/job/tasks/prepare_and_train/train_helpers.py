# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module contains the FlyteTaskTrainCommands"""

import logging

import iai_core.configuration.helper as otx_config_helper
from geti_telemetry_tools import unified_tracing
from iai_core.configuration.elements.hyper_parameters import HyperParameters
from iai_core.entities.datasets import Dataset
from iai_core.entities.label_schema import LabelSchema
from iai_core.entities.model import (
    Model,
    ModelConfiguration,
    ModelFormat,
    ModelOptimizationType,
    ModelPrecision,
    ModelStatus,
    TrainingFramework,
)
from iai_core.entities.model_storage import ModelStorage
from iai_core.entities.project import Project
from iai_core.entities.subset import Subset
from iai_core.entities.task_node import TaskNode
from iai_core.repos import ModelRepo
from jobs_common.exceptions import CommandInitializationFailedException, TrainingPodFailedException
from jobs_common.features.feature_flag_provider import FeatureFlag, FeatureFlagProvider
from jobs_common.tasks.utils.secrets import JobMetadata
from jobs_common_extras.mlflow.adapters.geti_otx_interface import GetiOTXInterfaceAdapter
from jobs_common_extras.mlflow.utils.train_output_models import TrainOutputModelIds, TrainOutputModels

from job.utils.train_workflow_data import TrainWorkflowData

logger = logging.getLogger(__name__)

__all__ = [
    "finalize_train",
    "prepare_train",
]


def validate_training_dataset(dataset: Dataset, task_node: TaskNode) -> None:
    """
    Perform sanity checks on the input dataset.

    :param dataset: Input dataset to validate
    :param task_node: TaskNode for which the dataset should be validated
    :raises CommandInitializationFailedException: if the dataset has issues
    """

    # Check that the dataset is not empty
    if len(dataset) == 0:
        logger.error("Empty train dataset %s for task %s", dataset.id_, task_node.title)
        raise CommandInitializationFailedException("Empty training dataset")

    for item in dataset:
        # Check that the subset is one of the train-valid-test ones
        if item.subset not in (Subset.TRAINING, Subset.VALIDATION, Subset.TESTING):
            logger.error(
                "An item (media %s) of dataset %s doesn't have a valid subset: "
                "found %s, expected one of TRAINING, VALIDATION or TESTING).",
                item.media.name,
                dataset.id_,
                item.subset.name,
            )
            raise CommandInitializationFailedException(
                "Inconsistent training dataset, not all items have a valid subset."
            )


class _ModelBuilder:
    """Helper class to create a new iai-core `Model` entity and save it to the repository."""

    def __init__(  # noqa: PLR0913
        self,
        model_repo: ModelRepo,
        project: Project,
        model_storage: ModelStorage,
        dataset: Dataset,
        label_schema: LabelSchema,
        hyper_parameters: HyperParameters,
        model_version: int,
        revamped_hyperparameters: dict,
    ):
        self._model_repo = model_repo
        self._project = project
        self._model_storage = model_storage
        self._dataset = dataset
        self._model_configuration = ModelConfiguration(
            configurable_parameters=hyper_parameters.data,
            label_schema=label_schema,
            display_only_configuration=revamped_hyperparameters,
        )
        self._model_version = model_version

    @unified_tracing
    def create_model(
        self,
        model_format: ModelFormat,
        has_xai_head: bool = False,
        precision: list[ModelPrecision] | None = None,
        model_optimization_type: ModelOptimizationType = ModelOptimizationType.NONE,
        previous_revision: Model | None = None,
        previous_trained_revision: Model | None = None,
    ) -> Model:
        """Create a new iai-core `Model` entity and save it to the repository."""
        # If fine-tuning, use the same trainer as the original model, else use the default one (latest OTX)
        training_framework = (
            previous_trained_revision.training_framework
            if previous_trained_revision
            else TrainingFramework.get_default()
        )
        model = Model(
            project=self._project,
            model_storage=self._model_storage,
            train_dataset=self._dataset,
            configuration=self._model_configuration,
            id_=ModelRepo.generate_id(),
            previous_trained_revision=previous_trained_revision,
            previous_revision=previous_revision,
            training_framework=training_framework,
            model_status=ModelStatus.NOT_READY,
            model_format=model_format,
            has_xai_head=has_xai_head,
            precision=precision,
            optimization_type=model_optimization_type,
            version=self._model_version,
        )
        self._model_repo.save(model)

        return model


@unified_tracing
def _prepare_mlflow_s3_bucket(
    project: Project,
    label_schema: LabelSchema,
    model_template_id: str,
    input_model: Model | None,
    hyper_parameters: dict,
    export_parameters: dict[str, str | bool] | list[dict[str, str | bool]],
    optimization_type: ModelOptimizationType = ModelOptimizationType.NONE,
) -> None:
    """Prepare files required for MLFlow based model training, optimize.

    It constructs a directory structure to the following S3 path:
    `mlflowexperiments/organizations/<org-id>/workspaces/<ws-id>/projects/<proj-id>/jobs/<job-id>`

    This is a list of files which is created by this function:

    - <root>: metadata.json, project.json, run_info.json
    - <root>/inputs: .placeholder, config.json, model.pth
    - <root>/live_metrics: .placeholder
    - <root>/outputs/models: .placeholder
    - <root>/outputs/exportable-codes: .placeholder
    - <root>/outputs/configurations: .placeholder

    :param project: Project owning this job
    :param model_template_id: ID of model template for this job (obtained from CRD)
    :param input_model: Model to use as a checkpoint to reload weights for training.
        If None, training will be from scratch
    :param hyper_parameters: Hyperparameters for this job (obtained from CRD)
    :param export_parameters: Exportparameters for this job (obtained from CRD)
    :param optimization_type: Model optimization type enum. It is only used for the model optimize job.
    :param label_schema: If not `None`, it is used to create `ClsSubTaskType`
        used to distinguish classification tasks.
        Otherwise, do not add `ClsSubTaskType` value to the configuration file.
    """
    adapter = GetiOTXInterfaceAdapter(project_identifier=project.identifier, job_metadata=JobMetadata.from_env_vars())
    adapter.push_placeholders()
    adapter.push_metadata()
    adapter.push_input_configuration(
        model_template_id=model_template_id,
        hyper_parameters=hyper_parameters,
        export_parameters=export_parameters,
        optimization_type=optimization_type,
        label_schema=label_schema,
    )
    if input_model:
        adapter.push_input_model(model=input_model)


@unified_tracing
def _get_export_parameters(
    train_output_models: TrainOutputModels,
) -> list[dict[str, str | bool]]:
    export_parameters: list[dict[str, str | bool]] = []
    for model in train_output_models.get_all_models():
        if model.optimization_type in {
            ModelOptimizationType.MO,
            ModelOptimizationType.ONNX,
        }:
            export_parameters.append(
                {
                    "type": model.model_format.name.lower(),
                    "output_model_id": str(model.id_),
                    "precision": model.precision[0].name if model.precision else "null",
                    "with_xai": model.has_xai_head,
                }
            )
    return export_parameters


@unified_tracing
def prepare_train(train_data: TrainWorkflowData, dataset: Dataset) -> TrainOutputModels:
    """Function should be called in prior to model training Flyte task.

    It creates iai-core model entities and prepares MLFlow experiment buckets for
    the subsequent model training Flyte task.

    :param train_data: Data class defining data used for training and providing helpers to get
        frequently used objects
    :param dataset: dataset to train on
    """
    project, task_node = train_data.get_common_entities()

    validate_training_dataset(dataset=dataset, task_node=task_node)

    label_schema = train_data.get_label_schema()
    model_storage = train_data.get_model_storage()
    input_model = train_data.get_input_model()
    hyper_parameters = train_data.get_hyper_parameters()

    model_repo = ModelRepo(model_storage.identifier)
    model_version = model_repo.get_latest_successful_version() + 1
    model_builder = _ModelBuilder(
        model_repo=model_repo,
        project=project,
        model_storage=model_storage,
        dataset=dataset,
        label_schema=label_schema,
        hyper_parameters=hyper_parameters,
        model_version=model_version,
        revamped_hyperparameters=train_data.hyperparameters,
    )

    output_base_model = model_builder.create_model(
        model_format=ModelFormat.BASE_FRAMEWORK,
        has_xai_head=True,
        previous_revision=input_model,
        previous_trained_revision=input_model,
    )
    use_fp16 = FeatureFlagProvider.is_enabled(FeatureFlag.FEATURE_FLAG_FP16_INFERENCE)
    output_models = TrainOutputModels(
        base=output_base_model,
        mo_with_xai=model_builder.create_model(
            model_format=ModelFormat.OPENVINO,
            has_xai_head=True,
            precision=[ModelPrecision.FP16 if use_fp16 else ModelPrecision.FP32],
            model_optimization_type=ModelOptimizationType.MO,
            previous_revision=output_base_model,
            previous_trained_revision=output_base_model,
        ),
        mo_fp32_without_xai=model_builder.create_model(
            model_format=ModelFormat.OPENVINO,
            has_xai_head=False,
            precision=[ModelPrecision.FP32],
            model_optimization_type=ModelOptimizationType.MO,
            previous_revision=output_base_model,
            previous_trained_revision=output_base_model,
        ),
        mo_fp16_without_xai=model_builder.create_model(
            model_format=ModelFormat.OPENVINO,
            has_xai_head=False,
            precision=[ModelPrecision.FP16],
            model_optimization_type=ModelOptimizationType.MO,
            previous_revision=output_base_model,
            previous_trained_revision=output_base_model,
        ),
        onnx=model_builder.create_model(
            model_format=ModelFormat.ONNX,
            model_optimization_type=ModelOptimizationType.ONNX,
            precision=[ModelPrecision.FP32],
            previous_revision=output_base_model,
            previous_trained_revision=output_base_model,
        ),
    )

    model_configuration = ModelConfiguration(
        configurable_parameters=hyper_parameters.data,
        label_schema=label_schema,
    )

    hyper_parameter_dict = otx_config_helper.convert(
        model_configuration.configurable_parameters,
        target=dict,
        enum_to_str=True,
        id_to_str=True,
    )

    _prepare_mlflow_s3_bucket(
        project=project,
        label_schema=label_schema,
        model_template_id=model_storage.model_template.model_template_id,
        input_model=input_model,
        hyper_parameters=hyper_parameter_dict,
        export_parameters=_get_export_parameters(train_output_models=output_models),
    )

    return output_models


@unified_tracing
def finalize_train(
    train_data: TrainWorkflowData,
    train_output_model_ids: TrainOutputModelIds,
    keep_mlflow_artifacts: bool = False,
) -> None:
    """Function should be called after model training Flyte task.

    It decides whether the model training is failed or not. If succeeded, update
    iai-core model entity status and clean the directory in the MLFLow experiment bucket.

    :param train_data: Data class defining data used for training and providing helpers to get
        frequently used objects
    :param train_output_model_ids: IDs of output models created from the previous command,
        PrepareFlyteTaskTrainCommand
    :param keep_mlflow_artifacts: If true, do not remove the artifacts in mlflow bucket even if training succeeds.
        It would be useful for debugging.
    """
    try:
        project, _ = train_data.get_common_entities()
        model_storage = train_data.get_model_storage()

        train_output_models = TrainOutputModels.from_train_output_model_ids(
            train_output_model_ids=train_output_model_ids,
            model_storage_identifier=model_storage.identifier,
        )

        train_output_models.reload_models(from_bucket=True)
        train_output_models.set_models_training_duration()

        # Mark the model as successfully trained, but not evaluated
        train_output_models.set_models_status(model_status=ModelStatus.TRAINED_NO_STATS)

        adapter = GetiOTXInterfaceAdapter(
            project_identifier=project.identifier,
            job_metadata=JobMetadata.from_env_vars(),
        )

        # If succeeded, clean the directory under the mlflowexperiments bucket
        if keep_mlflow_artifacts:
            logger.warning(
                "Parameter `keep_mlflow_artifacts` is set to true, so the bucket will not be cleaned up. "
                "If you see this warning outside of a development environment, please report it as a bug."
            )
        else:
            adapter.clean()
    except Exception as exc:
        logger.exception(exc)
        train_output_models.set_models_status(model_status=ModelStatus.FAILED)
        raise TrainingPodFailedException from exc
