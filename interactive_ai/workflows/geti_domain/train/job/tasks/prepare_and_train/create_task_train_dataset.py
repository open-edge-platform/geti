# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module defines Flyte task to create task train dataset"""

import logging

from geti_telemetry_tools import unified_tracing
from iai_core.entities.datasets import Dataset

from job.commands.create_task_train_dataset_command import CreateTaskTrainDatasetCommand
from job.utils.train_workflow_data import TrainWorkflowData

logger = logging.getLogger(__name__)


@unified_tracing
def create_task_train_dataset(
    train_data: TrainWorkflowData,
    max_training_dataset_size: int | None = None,
) -> Dataset:
    """
    Creates a task train dataset
    :param train_data: train workflow data
    :param max_training_dataset_size: maximum training dataset size
    return: training dataset
    """
    project, task_node = train_data.get_common_entities()

    dataset_storage = project.get_training_dataset_storage()

    command = CreateTaskTrainDatasetCommand(
        project=project,
        dataset_storage=dataset_storage,
        task_node=task_node,
        max_training_dataset_size=max_training_dataset_size,
        reshuffle_subsets=train_data.reshuffle_subsets,
    )
    command.execute()

    return command.dataset
