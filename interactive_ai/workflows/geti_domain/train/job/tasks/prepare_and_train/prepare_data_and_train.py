# INTEL CONFIDENTIAL
#
# Copyright (C) 2023 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and
# your use of them is governed by the express license under which they were provided to
# you ("License"). Unless the License provides otherwise, you may not use, modify, copy,
# publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is,
# with no express or implied warranties, other than those that are expressly stated
# in the License.

"""
Prepare training data task
"""

import logging
import os
import typing

from geti_telemetry_tools.tracing.common import tracer
from geti_types import CTX_SESSION_VAR, ID
from jobs_common.jobs.helpers.project_helpers import lock_project
from jobs_common.k8s_helpers.k8s_resources_calculation import ComputeResources, EphemeralStorageResources
from jobs_common.k8s_helpers.trainer_image_info import TrainerImageInfo
from jobs_common.k8s_helpers.trainer_pod_definition import create_flyte_container_task
from jobs_common.tasks import flyte_multi_container_dynamic as dynamic
from jobs_common.tasks.utils.logging import init_logger
from jobs_common.tasks.utils.progress import publish_consumed_resources, report_task_step_progress, task_progress
from jobs_common.tasks.utils.secrets import SECRETS, JobMetadata, env_vars
from jobs_common.tasks.utils.telemetry import task_telemetry
from jobs_common_extras.shard_dataset.tasks.shard_dataset import SHARD_DATASET_TASK_POD_SPEC
from sc_sdk.utils.type_helpers import str2bool

from job.tasks.prepare_and_train.create_task_train_dataset import create_task_train_dataset
from job.tasks.prepare_and_train.get_train_data import get_train_data
from job.tasks.prepare_and_train.shard_dataset import shard_dataset_for_train
from job.tasks.prepare_and_train.train_helpers import prepare_train
from job.utils.train_workflow_data import TrainWorkflowDataForFlyteTaskTrainer

IDX_STEP_RETRIEVE_TRAIN_DATA = 0
IDX_STEP_CREATE_TRAIN_DATASET = 1
IDX_STEP_SHARD_DATASET = 2
STEPS_COUNT = 3

logger = logging.getLogger(__name__)


def report_retrieve_train_data_progress(progress: float, message: str) -> None:
    """
    Function to report train data retrieving progress
    """
    report_task_step_progress(
        step_index=IDX_STEP_RETRIEVE_TRAIN_DATA,
        steps_count=STEPS_COUNT,
        step_progress=progress,
        step_message=message,
    )


def report_create_train_dataset_progress(progress: float, message: str) -> None:
    """
    Function to report train dataset creating progress
    """
    report_task_step_progress(
        step_index=IDX_STEP_CREATE_TRAIN_DATASET,
        steps_count=STEPS_COUNT,
        step_progress=progress,
        step_message=message,
    )


def report_shard_progress(progress: float, message: str) -> None:
    """
    Function to report dataset sharding progress
    """
    report_task_step_progress(
        step_index=IDX_STEP_SHARD_DATASET,
        steps_count=STEPS_COUNT,
        step_progress=progress,
        step_message=message,
    )


@dynamic(
    pod_spec=SHARD_DATASET_TASK_POD_SPEC,
    secret_requests=SECRETS,
)
@env_vars
@init_logger(package_name=__name__)
@task_telemetry
@task_progress(
    start_message="Starting training data preparation",
    finish_message="Training data prepared",
    failure_message="Training dataset preparation failed",
)
def prepare_training_data_model_and_start_training(  # noqa: PLR0913
    project_id: str,
    task_id: str,
    from_scratch: bool,
    should_activate_model: bool,
    infer_on_pipeline: bool,
    command: list[str],
    model_storage_id: str = "",
    hyper_parameters_id: str = "",
    enable_training_from_dataset_shard: bool = True,
    max_shard_size: int = 1000,
    num_image_pulling_threads: int = 10,
    num_upload_threads: int = 2,
    max_training_dataset_size: typing.Optional[int] = None,  # noqa: UP007
    min_annotation_size: typing.Optional[int] = None,  # noqa: UP007
    max_number_of_annotations: typing.Optional[int] = None,  # noqa: UP007
    reshuffle_subsets: bool = False,
) -> TrainWorkflowDataForFlyteTaskTrainer:
    """
    Prepare data and model for the consecutive model training Flyte task.

    :param project_id: Project ID
    :param task_id: Task ID
    :param from_scratch: Whether to train the task from scratch.
    :param should_activate_model: Whether to activate model after training
    :param infer_on_pipeline: Whether to infer on pipeline
    :param command: Command to be executed on the primary container, e.g., OTX2 trainer pod.
    :param model_storage_id: ID of model storage to train model in, use active model if empty string
    :param hyper_parameters_id: ID of the hyper-parameters configuration to use for this job.
        If unspecified, it defaults to the current configuration of the model storage.
    :param enable_training_from_dataset_shard: Whether to enable model training from dataset shard
    :param max_shard_size: Maximum number of dataset items in each shard file
    :param num_image_pulling_threads: Number of threads used for pulling image bytes
    :param num_upload_threads: Number of threads used for uploading shard files
    :param max_training_dataset_size: maximum training dataset size
    :param min_annotation_size: Minimum size of an annotation in pixels. Any annotation smaller than this will be
    ignored during training
    :param max_number_of_annotations: Maximum number of annotation allowed in one annotation scene. If exceeded, the
    annotation scene will be ignored during training.
    :param reshuffle_subsets: Whether to reassign/shuffle all the items to subsets including Test set from scratch
    :return TrainWorkflowDataForFlyteTaskTrainer: train workflow data class and others needed
        the next model training Flyte task.
    """
    ############################ NOTE ############################
    # It was inevitable to copy and paste `prepare_training_data()`
    # because we want to reuse Python object such as project, dataset, etc...
    # Pulling them from DB is also expensive (especially dataset),
    # so that we need to reuse them.
    # This can bring a code divergence between both functions.
    # However, we can deprecate `prepare_training_data()` in the future
    # if we successfully move to Flyte task based model training.
    ##############################################################

    # Lock the project to prevent data race conditions
    lock_project(job_type="train", project_id=ID(project_id))

    # Step 1 - Retrieve train data
    report_retrieve_train_data_progress(progress=0, message="Starting train data retrieval")
    train_data = get_train_data(
        project_id=project_id,
        task_id=task_id,
        from_scratch=from_scratch,
        should_activate_model=should_activate_model,
        infer_on_pipeline=infer_on_pipeline,
        model_storage_id=model_storage_id,
        hyper_parameters_id=hyper_parameters_id,
        min_annotation_size=min_annotation_size,
        max_number_of_annotations=max_number_of_annotations,
        reshuffle_subsets=reshuffle_subsets,
    )
    report_retrieve_train_data_progress(progress=100, message="Train data retrieved")

    # Step 2 - Create train dataset
    report_create_train_dataset_progress(progress=0, message="Starting train dataset creation")
    dataset = create_task_train_dataset(train_data=train_data, max_training_dataset_size=max_training_dataset_size)
    report_create_train_dataset_progress(progress=100, message="Train dataset is created")

    # Step 3 - Shard dataset (if needed)
    if enable_training_from_dataset_shard:
        report_shard_progress(progress=0, message="Starting dataset sharding")
        train_data.compiled_dataset_shards_id = shard_dataset_for_train(
            train_data=train_data,
            dataset=dataset,
            max_shard_size=max_shard_size,
            num_image_pulling_threads=num_image_pulling_threads,
            num_upload_threads=num_upload_threads,
            progress_callback=report_shard_progress,
        )
        report_shard_progress(progress=100, message="Dataset sharding is done")
    else:
        report_shard_progress(progress=100, message="Training from sharded dataset is disabled")

    # Step 4 - model entity and mlflow bucket preparation
    train_output_models = prepare_train(train_data=train_data, dataset=dataset)

    train_output_model_ids = train_output_models.to_train_output_model_ids()

    job_metadata = JobMetadata.from_env_vars()
    session = CTX_SESSION_VAR.get()

    otx2_task = create_flyte_container_task(
        session=session,
        project_id=train_data.project_id,
        job_id=str(job_metadata.id),
        compute_resources=ComputeResources.from_node_resources(),
        ephemeral_storage_resources=(
            EphemeralStorageResources.create_from_compiled_dataset_shards(
                compiled_dataset_shards=train_data.get_compiled_dataset_shards(),
                ephemeral_storage_safety_margin=5 * (1024**3),  # 5Gi
            )
        ),
        trainer_image_info=TrainerImageInfo.create(train_output_models.base.training_framework),
        command=command,
        container_name="train",
    )

    report_resources_consumption = str2bool(os.environ.get("REPORT_RESOURCES_CONSUMPTION", "false"))
    if report_resources_consumption:
        publish_consumed_resources(amount=len(dataset), unit="images", service="training")

    with tracer.start_as_current_span("otx2_task"):
        otx2_task()

    return TrainWorkflowDataForFlyteTaskTrainer(
        train_data=train_data,
        dataset_id=dataset.id_,
        organization_id=str(session.organization_id),
        job_id=str(job_metadata.id),
        train_output_model_ids=train_output_model_ids,
    )
