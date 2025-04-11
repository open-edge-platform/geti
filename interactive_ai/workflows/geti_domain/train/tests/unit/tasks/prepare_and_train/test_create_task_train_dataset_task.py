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

import os
from unittest.mock import MagicMock, patch

import pytest
from geti_types import ID
from sc_sdk.entities.datasets import Dataset

from job.tasks.prepare_and_train.create_task_train_dataset import create_task_train_dataset
from job.utils.train_workflow_data import TrainWorkflowData
from tests.unit.tasks.utils import TEST_ENV_VARS

PROJECT_ID = "project_id"
TASK_ID = "task_id"
DATASET_ID = "dataset_id"


def mock_command(self, *args, **kwargs) -> None:
    self.dataset = Dataset(ID(DATASET_ID))
    return


def return_none(self, *args, **kwargs) -> None:
    return None


@pytest.fixture
def fxt_mock_project():
    return MagicMock()


@pytest.mark.JobsComponent
class TestCreateTrainDataset:
    @patch.dict(os.environ, TEST_ENV_VARS)
    @patch.object(TrainWorkflowData, "get_common_entities")
    @patch("job.tasks.prepare_and_train.create_task_train_dataset.CreateTaskTrainDatasetCommand")
    @patch("jobs_common.tasks.utils.progress.task_progress", new=return_none)
    @patch("jobs_common.tasks.utils.secrets.set_env_vars", new=return_none)
    def test_create_task_train_dataset_node_found(
        self, patched_command_init, mock_get_entities, fxt_mock_project, fxt_train_data
    ) -> None:
        # Arrange
        task_node = MagicMock()
        dataset_storage = MagicMock()
        mock_get_entities.return_value = (fxt_mock_project, task_node)
        fxt_mock_project.get_trainable_task_node_by_id.return_value = task_node
        fxt_mock_project.get_training_dataset_storage.return_value = dataset_storage
        train_data = fxt_train_data(
            project_id=PROJECT_ID,
            task_id=TASK_ID,
        )
        patched_command = MagicMock()
        patched_command.dataset = Dataset(ID(DATASET_ID))
        patched_command_init.return_value = patched_command

        # Act
        dataset = create_task_train_dataset(train_data=train_data, max_training_dataset_size=100)

        # Assert
        fxt_mock_project.get_training_dataset_storage.assert_called_once_with()
        patched_command_init.assert_called_once_with(
            project=fxt_mock_project,
            dataset_storage=dataset_storage,
            task_node=task_node,
            max_training_dataset_size=100,
            reshuffle_subsets=False,
        )
        patched_command.execute.assert_called_once_with()

        assert dataset.id_ == DATASET_ID, "Command dataset is returned"
