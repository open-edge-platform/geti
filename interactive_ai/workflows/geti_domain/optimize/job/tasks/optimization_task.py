# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module defines Flyte dynamic subworkflow to shard dataset, prepare models and start optimization"""

import logging
from typing import Optional

from geti_telemetry_tools.tracing.common import tracer
from geti_types import CTX_SESSION_VAR, ID
from iai_core.entities.model_storage import ModelStorageIdentifier
from iai_core.repos import ModelRepo, ProjectRepo
from jobs_common.jobs.helpers.project_helpers import lock_project
from jobs_common.k8s_helpers.trainer_pod_definition import create_flyte_container_task
from jobs_common.tasks import flyte_multi_container_dynamic as dynamic
from jobs_common.tasks.utils.logging import init_logger
from jobs_common.tasks.utils.progress import task_progress
from jobs_common.tasks.utils.secrets import SECRETS, env_vars
from jobs_common.tasks.utils.telemetry import task_telemetry
from jobs_common.utils.annotation_filter import AnnotationFilter
from jobs_common_extras.shard_dataset.tasks.shard_dataset import SHARD_DATASET_TASK_POD_SPEC, shard_dataset

from job.models import OptimizationTrainerContext
from job.tasks.constants import NULL_COMPILED_DATASET_SHARDS_ID
from job.tasks.helpers import prepare_optimize

logger = logging.getLogger(__name__)


@dynamic(pod_spec=SHARD_DATASET_TASK_POD_SPEC, secret_requests=SECRETS)
@env_vars
@init_logger(package_name=__name__)
@task_telemetry
@task_progress(
    start_message="Starting dataset sharding and optimized model preparation",
    finish_message="Dataset sharding is done and model is prepared",
    failure_message="Training dataset and optimized model preparation failed",
)
def shard_dataset_prepare_models_and_start_optimization(  # noqa: PLR0913
    project_id: str,
    model_storage_id: str,
    model_id: str,
    max_shard_size: int,
    optimization_type: str,
    command: list[str],
    num_image_pulling_threads: int = 10,
    num_upload_threads: int = 2,
    enable_optimize_from_dataset_shard: bool = False,
    min_annotation_size: Optional[int] = None,  # noqa: UP007
    max_number_of_annotations: Optional[int] = None,  # noqa: UP007
) -> OptimizationTrainerContext:
    """
    Shard dataset, prepare models for optimization and start optimization pod

    :param project_id: project ID
    :param model_storage_id: model storage ID
    :param model_id: base model ID
    :param max_shard_size: Maximum number of DatasetItems that can be contained in each shard
    :param optimization_type: name of the optimization type
    :param num_image_pulling_threads: Number of threads used for pulling image bytes
    :param num_upload_threads: Number of threads used for uploading shard files
    :param min_annotation_size: Minimum size of an annotation in pixels. Any annotation smaller than this will be
    ignored
    :param max_number_of_annotations: Maximum number of annotation allowed in one annotation scene. If exceeded, the
    annotation scene will be ignored
    :param enable_optimize_from_dataset_shard: Whether to enable model optimization from dataset shard
    :param command: Command to be executed on the primary container, e.g., OTX2 trainer pod.
    :return: ID of CompiledDatasetShards entity
    """
    # Update compiled_dataset_shards_id
    if enable_optimize_from_dataset_shard:
        # Lock the project to prevent data race conditions
        project_id_ = ID(project_id)
        lock_project(job_type=f"optimize_{optimization_type.lower()}", project_id=project_id_)

        project = ProjectRepo().get_by_id(project_id_)
        model_storage_identifier = ModelStorageIdentifier(
            workspace_id=project.workspace_id,
            project_id=project_id_,
            model_storage_id=ID(model_storage_id),
        )
        model = ModelRepo(model_storage_identifier).get_by_id(ID(model_id))

        train_dataset = model.get_train_dataset()
        filtered_train_dataset = AnnotationFilter.apply_annotation_filters(
            dataset=train_dataset,
            max_number_of_annotations=max_number_of_annotations,
            min_annotation_size=min_annotation_size,
        )
        label_schema = model.get_label_schema()

        compiled_dataset_shards_id = shard_dataset(
            project=project,
            label_schema=label_schema,
            train_dataset=filtered_train_dataset,
            max_shard_size=max_shard_size,
            num_image_pulling_threads=num_image_pulling_threads,
            num_upload_threads=num_upload_threads,
        )
    else:
        compiled_dataset_shards_id = NULL_COMPILED_DATASET_SHARDS_ID

    optimization_ctx = prepare_optimize(
        project_id=project_id,
        model_storage_id=model_storage_id,
        model_id=model_id,
        compiled_dataset_shards_id=compiled_dataset_shards_id,
        min_annotation_size=min_annotation_size,
        max_number_of_annotations=max_number_of_annotations,
    )

    optimize_task = create_flyte_container_task(
        session=CTX_SESSION_VAR.get(),
        project_id=optimization_ctx.project_id,
        job_id=optimization_ctx.job_id,
        compute_resources=optimization_ctx.compute_resources,
        ephemeral_storage_resources=optimization_ctx.ephemeral_storage_resources,
        trainer_image_info=optimization_ctx.trainer_image_info,
        command=command,
        container_name="optimize",
    )

    with tracer.start_as_current_span("optimize_task"):
        optimize_task()

    return optimization_ctx
