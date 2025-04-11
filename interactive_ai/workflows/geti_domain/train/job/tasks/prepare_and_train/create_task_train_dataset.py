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

"""This module defines Flyte task to create task train dataset"""

import logging

from geti_telemetry_tools import unified_tracing
from sc_sdk.entities.datasets import Dataset

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
