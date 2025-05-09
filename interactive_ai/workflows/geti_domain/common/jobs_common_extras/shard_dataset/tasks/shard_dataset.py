# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module defines Flyte task to create task train dataset"""

import logging
from collections.abc import Callable
from multiprocessing.pool import AsyncResult, ThreadPool
from queue import Queue

import flytekit
from geti_telemetry_tools import unified_tracing
from geti_types import DatasetStorageIdentifier
from iai_core.entities.compiled_dataset_shards import CompiledDatasetShard
from iai_core.entities.datasets import Dataset
from iai_core.entities.label_schema import LabelSchema
from iai_core.entities.project import Project
from kubernetes.client.models import V1ResourceRequirements

from jobs_common.tasks.primary_container_task import get_flyte_pod_spec
from jobs_common.utils.annotation_filter import AnnotationFilter
from jobs_common.utils.progress_helper import noop_progress_callback
from jobs_common_extras.shard_dataset.commands.create_and_save_compiled_dataset_shards_command import (
    CreateAndSaveCompiledDatasetShardsCommand,
)
from jobs_common_extras.shard_dataset.commands.create_shard_file_command import CreateShardFileCommand
from jobs_common_extras.shard_dataset.commands.map_items_to_shards_command import MapItemsToShardsCommand
from jobs_common_extras.shard_dataset.commands.upload_shard_file_command import UploadShardFileCommand

logger = logging.getLogger(__name__)

__all__ = ["SHARD_DATASET_TASK_POD_SPEC", "shard_dataset"]

SHARD_DATASET_TASK_POD_SPEC = get_flyte_pod_spec(
    resources=V1ResourceRequirements(
        limits={"cpu": "100", "memory": "8000Mi", "ephemeral-storage": "100Gi"},
        requests={"cpu": "1", "memory": "2000Mi", "ephemeral-storage": "2000Mi"},
    )
)

TIMEOUT = 600  # 10 minutes


class CanCreateTicket:
    """Object to count the number of shard files in the local disk at the same time"""


@unified_tracing
def shard_dataset(  # noqa: PLR0913
    project: Project,
    label_schema: LabelSchema,
    train_dataset: Dataset,
    max_shard_size: int,
    num_image_pulling_threads: int = 10,
    num_upload_threads: int = 2,
    progress_callback: Callable[[float, str], None] = noop_progress_callback,
    max_number_of_annotations: int | None = None,
    min_annotation_size: int | None = None,
) -> str:
    """
    Shard SC Dataset

    :param project: Project containing LabelSchema and train Dataset
    :param label_schema: LabelSchema used for the training
    :param train_dataset: Dataset used for the training
    :param max_shard_size: Maximum number of DatasetItems that can be contained in each shard
    :param progress_callback: A callback function to report sharding progress
    :param num_image_pulling_threads: Number of threads used for pulling image bytes
    :param num_upload_threads: Number of threads used for uploading shard files
    :param max_number_of_annotations: Number of threads used for uploading shard files
    :param min_annotation_size: Minimum size of an annotation in pixels. Any annotation smaller than this will be
        ignored during training
    :param max_number_of_annotations: Maximum number of annotation allowed in one annotation scene. If exceeded, the
    annotation scene will be ignored during training.
    :return: ID of CompiledDatasetShards entity
    """
    progress_callback(0, "Preparing dataset")

    dataset_id = str(train_dataset.id_)

    filtered_dataset = AnnotationFilter.apply_annotation_filters(
        dataset=train_dataset,
        max_number_of_annotations=max_number_of_annotations,
        min_annotation_size=min_annotation_size,
    )
    map_items_to_shards_command = MapItemsToShardsCommand(
        train_dataset=filtered_dataset,
        max_shard_size=max_shard_size,
    )
    map_items_to_shards_command.execute()

    work_dir = flytekit.current_context().working_directory

    futures: list[AsyncResult[CompiledDatasetShard]] = []

    n_complete = 0
    total_num_shards = len(map_items_to_shards_command.shards)

    queue: Queue = Queue(maxsize=num_upload_threads + 1)

    # Maximum number of files in the local disk at the same time := num_upload_threads + 1
    logger.info(f"Num upload threads: {num_upload_threads}  Num image pulling threads: {num_image_pulling_threads}")
    for _ in range(num_upload_threads + 1):
        queue.put(CanCreateTicket(), timeout=TIMEOUT)

    dataset_storage_identifier = DatasetStorageIdentifier(
        workspace_id=project.workspace_id,
        project_id=project.id_,
        dataset_storage_id=project.get_training_dataset_storage().id_,
    )

    with ThreadPool(processes=num_upload_threads) as pool:
        for shard_idx, dataset_items in enumerate(map_items_to_shards_command.shards):
            can_create_ticket = queue.get(timeout=TIMEOUT)
            logger.debug(f"Acquired can_create_ticket: {can_create_ticket}")

            create_command = CreateShardFileCommand(
                dataset_storage_identifier=dataset_storage_identifier,
                dataset_id=dataset_id,
                dataset_items=dataset_items,
                label_schema=label_schema,
                work_dir=work_dir,
                shard_idx=shard_idx,
                total_num_shards=total_num_shards,
                num_threads=num_image_pulling_threads,
            )
            create_command.execute()
            upload_command = UploadShardFileCommand(
                dataset_id=dataset_id,
                project_identifier=project.identifier,
                fpath=create_command.fpath,
            )

            future = pool.apply_async(
                func=upload_shard_file,
                kwds={
                    "upload_command": upload_command,
                    "create_command": create_command,
                    "queue": queue,
                },
            )
            futures.append(future)

            n_complete += 1
            msg = f"Preparing dataset: processed {n_complete}/{total_num_shards} shards"
            logger.info(msg)
            progress_callback(100.0 * n_complete / total_num_shards, msg)

        compiled_shard_files = [future.get(timeout=TIMEOUT) for future in futures]

    command = CreateAndSaveCompiledDatasetShardsCommand(
        dataset_id=dataset_id,
        label_schema=label_schema,
        compiled_shard_files=compiled_shard_files,
        dataset_storage_identifier=dataset_storage_identifier,
    )

    command.execute()
    progress_callback(100.0, "Dataset is ready")
    return command.compiled_dataset_shards_id


@unified_tracing
def upload_shard_file(
    upload_command: UploadShardFileCommand,
    create_command: CreateShardFileCommand,
    queue: Queue,
) -> CompiledDatasetShard:
    upload_command.execute()
    # File is removed from the local disk
    # Now you can create a new file
    queue.put(CanCreateTicket(), timeout=TIMEOUT)

    return CompiledDatasetShard(
        filename=create_command.fname,
        binary_filename=upload_command.binary_filename,
        size=create_command.fsize,
        checksum=create_command.fchecksum,
    )
