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
"""This module tests commands to create task train dataset"""

from unittest.mock import MagicMock, patch

import pytest
from jobs_common.exceptions import DatasetCreationFailedException
from jobs_common.utils.dataset_helpers import DatasetHelpers
from sc_sdk.repos.dataset_entity_repo import PipelineDatasetRepo

from job.commands.create_task_train_dataset_command import CreateTaskTrainDatasetCommand


def raise_exception(*args, **kwargs):
    raise Exception("Test Exception")


@pytest.mark.JobsComponent
class TestCreateDatasetCommand:
    def test_create_train_dataset_command(
        self, fxt_project, fxt_dataset_storage, fxt_detection_node, fxt_dataset
    ) -> None:
        # Arrange
        mock_pipeline_dataset = MagicMock()
        mock_task_dataset = MagicMock()
        mock_pipeline_dataset.task_datasets = {fxt_detection_node.id_: mock_task_dataset}

        # Act
        with (
            patch.object(
                DatasetHelpers,
                "construct_and_save_train_dataset_for_task",
                return_value=fxt_dataset,
            ) as mock_construct_dataset,
            patch.object(
                PipelineDatasetRepo,
                "get_or_create",
                return_value=mock_pipeline_dataset,
            ) as mock_get_pipeline_dataset,
        ):
            command = CreateTaskTrainDatasetCommand(
                project=fxt_project,
                dataset_storage=fxt_dataset_storage,
                task_node=fxt_detection_node,
                max_training_dataset_size=100,
                reshuffle_subsets=False,
            )
            command.execute()

            # Assert
            mock_get_pipeline_dataset.assert_called_once_with(fxt_dataset_storage.identifier)
            mock_construct_dataset.assert_called_once_with(
                task_dataset_entity=mock_task_dataset,
                project_id=fxt_project.id_,
                dataset_storage=fxt_dataset_storage,
                task_node=fxt_detection_node,
                max_training_dataset_size=100,
                reshuffle_subsets=False,
            )

    def test_create_train_dataset_command_error(
        self, fxt_project, fxt_dataset_storage, fxt_detection_node, fxt_dataset
    ) -> None:
        # Arrange
        mock_pipeline_dataset = MagicMock()
        mock_task_dataset = MagicMock()
        mock_pipeline_dataset.task_datasets = {fxt_detection_node.id_: mock_task_dataset}

        # Act
        with (
            patch.object(
                DatasetHelpers,
                "construct_and_save_train_dataset_for_task",
                return_value=fxt_dataset,
            ) as mock_construct_dataset,
            patch.object(
                PipelineDatasetRepo,
                "get_or_create",
                return_value=mock_pipeline_dataset,
            ),
        ):
            mock_construct_dataset.side_effect = raise_exception
            command = CreateTaskTrainDatasetCommand(
                project=fxt_project,
                dataset_storage=fxt_dataset_storage,
                task_node=fxt_detection_node,
                max_training_dataset_size=100,
                reshuffle_subsets=False,
            )
            with pytest.raises(DatasetCreationFailedException):
                command.execute()
