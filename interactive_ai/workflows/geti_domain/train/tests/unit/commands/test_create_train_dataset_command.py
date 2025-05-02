# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""This module tests commands to create task train dataset"""

from unittest.mock import MagicMock, patch

import pytest
from iai_core_py.repos.dataset_entity_repo import PipelineDatasetRepo
from jobs_common.exceptions import DatasetCreationFailedException
from jobs_common.utils.dataset_helpers import DatasetHelpers

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
