# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module defines Flyte task to create task train dataset"""

import logging
from collections.abc import Callable

from geti_telemetry_tools import unified_tracing
from iai_core.entities.datasets import Dataset
from jobs_common_extras.shard_dataset.tasks.shard_dataset import shard_dataset

from job.utils.train_workflow_data import TrainWorkflowData

logger = logging.getLogger(__name__)


@unified_tracing
def shard_dataset_for_train(
    train_data: TrainWorkflowData,
    dataset: Dataset,
    max_shard_size: int,
    progress_callback: Callable[[float, str], None],
    num_image_pulling_threads: int = 10,
    num_upload_threads: int = 2,
) -> str:
    """
    Shard SC Dataset

    :param train_data: TrainWorkflowData
    :param dataset: Dataset created for training
    :param max_shard_size: Maximum number of DatasetItems that can be contained in each shard
    :param progress_callback: A callback function to report sharding progress
    :param num_image_pulling_threads: Number of threads used for pulling image bytes
    :param num_upload_threads: Number of threads used for uploading shard files
    :return: compiled dataset shards id
    """
    project, _ = train_data.get_common_entities()
    label_schema = train_data.get_label_schema()

    return shard_dataset(
        project=project,
        label_schema=label_schema,
        train_dataset=dataset,
        max_shard_size=max_shard_size,
        num_image_pulling_threads=num_image_pulling_threads,
        num_upload_threads=num_upload_threads,
        progress_callback=progress_callback,
        min_annotation_size=train_data.min_annotation_size,
        max_number_of_annotations=train_data.max_number_of_annotations,
    )
