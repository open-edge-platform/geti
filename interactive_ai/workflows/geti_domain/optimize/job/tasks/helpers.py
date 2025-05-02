# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging
from typing import Optional

import iai_core_py.configuration.helper as otx_config_helper
from geti_telemetry_tools.tracing.common import unified_tracing
from geti_types import ID, ProjectIdentifier
from iai_core_py.entities.model import (
    Model,
    ModelConfiguration,
    ModelFormat,
    ModelOptimizationType,
    ModelPrecision,
    ModelStatus,
    OptimizationMethod,
)
from iai_core_py.entities.model_storage import ModelStorageIdentifier
from iai_core_py.repos import CompiledDatasetShardsRepo, ModelRepo, ProjectRepo
from jobs_common.jobs.helpers.project_helpers import lock_project
from jobs_common.tasks.utils.progress import publish_metadata_update
from jobs_common.tasks.utils.secrets import JobMetadata
from jobs_common.utils.annotation_filter import AnnotationFilter
from jobs_common_extras.mlflow.adapters.geti_otx_interface import GetiOTXInterfaceAdapter

from job.models import OptimizationConfig, OptimizationTrainerContext

logger = logging.getLogger(__name__)


def _prepare_mlflow_s3_bucket(
    project_identifier: ProjectIdentifier,
    optimization_cfg: OptimizationConfig,
) -> None:
    input_model = optimization_cfg.input_model
    model_template = input_model.model_storage.model_template
    hyper_parameters = input_model.get_previous_trained_revision().configuration.configurable_parameters
    hyper_parameter_dict = otx_config_helper.convert(hyper_parameters, target=dict, enum_to_str=True, id_to_str=True)

    adapter = GetiOTXInterfaceAdapter(
        project_identifier=project_identifier,
        job_metadata=JobMetadata.from_env_vars(),
    )
    adapter.push_placeholders()
    adapter.push_metadata()
    adapter.push_input_configuration(
        model_template_id=model_template.model_template_id,
        hyper_parameters=hyper_parameter_dict,
        export_parameters=[
            {
                "type": "openvino",
                "output_model_id": input_model.id_,
                "precision": ModelPrecision.INT8.name,
                "with_xai": False,
            },
        ],
        optimization_type=optimization_cfg.model_to_optimize.optimization_type,
        label_schema=optimization_cfg.input_model.get_label_schema(),
    )
    adapter.push_input_model(model=optimization_cfg.input_model)


@unified_tracing
def prepare_optimize(
    project_id: str,
    model_storage_id: str,
    model_id: str,
    compiled_dataset_shards_id: str,
    min_annotation_size: Optional[int] = None,  # noqa: UP007
    max_number_of_annotations: Optional[int] = None,  # noqa: UP007
) -> OptimizationTrainerContext:
    """Function should be called in prior to model optimization task.

    It creates Geti model entities (dataset shards with model placeholder) and prepares MLFlow experiment buckets for
    the subsequent model optimization task.

    :param project_id: project ID
    :param model_storage_id: model storage ID
    :param model_id: base model ID
    :param compiled_dataset_shards_id: Id of CompiledDatasetShards entity.
        If it is NULL_COMPILED_DATASET_SHARDS_ID, do not use dataset shard files for the model optimization.
    :param min_annotation_size: Minimum size of an annotation in pixels. Any annotation smaller than this will be
    ignored
    :param max_number_of_annotations: Maximum number of annotation allowed in one annotation scene. If exceeded, the
    annotation scene will be ignored
    """
    project_id_ = ID(project_id)
    optimization_type = ModelOptimizationType.POT.name
    lock_project(job_type=f"optimize_{optimization_type.lower()}", project_id=project_id_)

    project = ProjectRepo().get_by_id(project_id_)
    model_storage_identifier = ModelStorageIdentifier(
        workspace_id=project.workspace_id, project_id=project_id_, model_storage_id=ID(model_storage_id)
    )
    model_repo = ModelRepo(model_storage_identifier)
    optimized_models = (
        mo
        for mo in model_repo.get_optimized_models_by_base_model_id(ID(model_id))
        if mo.model_format == ModelFormat.OPENVINO and ModelPrecision.FP32 in mo.precision and not mo.has_xai_head
    )
    model = next(optimized_models, None)
    if not model:
        raise ValueError("Model doesn't have optimized OpenVINO FP32 version")
    hyper_parameters = model.configuration.configurable_parameters

    train_dataset = model.get_train_dataset()
    filtered_train_dataset = AnnotationFilter.apply_annotation_filters(
        dataset=train_dataset,
        max_number_of_annotations=max_number_of_annotations,
        min_annotation_size=min_annotation_size,
    )
    label_schema = model.get_label_schema()
    compiled_dataset_shards = CompiledDatasetShardsRepo(
        dataset_storage_identifier=project.get_training_dataset_storage().identifier
    ).get_by_id(ID(compiled_dataset_shards_id))

    model_to_optimize: Model = Model(
        project=project,
        model_storage=model.model_storage,
        train_dataset=filtered_train_dataset,
        configuration=ModelConfiguration(
            configurable_parameters=hyper_parameters,
            label_schema=label_schema,  # type: ignore
        ),
        id_=ModelRepo.generate_id(),
        previous_trained_revision=model.get_base_model(),
        training_framework=model.training_framework,
        model_status=ModelStatus.NOT_READY,
        model_format=ModelFormat.OPENVINO,
        precision=[ModelPrecision.INT8],
        optimization_type=ModelOptimizationType.POT,
        optimization_methods=[OptimizationMethod.QUANTIZATION],
        version=model.version,
    )

    model_to_optimize.set_previous_revision(model.get_base_model())
    model_repo.save(model_to_optimize)

    metadata = {"optimized_model_id": model_to_optimize.id_}
    publish_metadata_update(metadata=metadata)

    optimization_config = OptimizationConfig(
        project=project,
        input_model=model,
        model_to_optimize=model_to_optimize,
        compiled_dataset_shards=compiled_dataset_shards,
        model_storage_identifier=model_storage_identifier,
    )

    trainer_ctx = OptimizationTrainerContext.create_from_config(optimization_cfg=optimization_config)

    _prepare_mlflow_s3_bucket(project_identifier=trainer_ctx.project_identifier, optimization_cfg=optimization_config)

    return trainer_ctx


@unified_tracing
def finalize_optimize(
    trainer_ctx: OptimizationTrainerContext,
    keep_mlflow_artifacts: bool = False,
) -> None:
    """Function should be called after model optimization task.

    It updates iai-core-py model entity and clean the directory in the MLFLow experiment bucket.

    :param trainer_ctx: Data class defining data used for optimization and providing helpers to get
        frequently used objects
    :param keep_mlflow_artifacts: If true, do not remove the artifacts in mlflow bucket even if training succeeds.
        It would be useful for debugging.
    """
    adapter = GetiOTXInterfaceAdapter(
        project_identifier=trainer_ctx.project_identifier,
        job_metadata=JobMetadata.from_env_vars(),
    )
    model_to_optimize = trainer_ctx.model_to_optimize

    adapter.update_output_model_for_optimize(model_to_optimize)

    model_repo = ModelRepo(model_storage_identifier=trainer_ctx.model_storage_identifier)
    model_repo.save(model_to_optimize)

    if keep_mlflow_artifacts:
        logger.warning(
            "Parameter `keep_mlflow_artifacts` is set to true, so the bucket will not be cleaned up. "
            "If you see this warning outside of a development environment, please report it as a bug."
        )

    else:
        adapter.clean()
