# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from unittest.mock import patch

import pytest
from iai_core_py.repos import DatasetRepo
from jobs_common.utils.dataset_helpers import DatasetHelpers

from job.commands.create_testing_dataset_command import CreateTaskTestingDatasetCommand


@pytest.mark.JobsComponent
class TestCreateDatasetCommand:
    def test_create_task_testing_dataset_command(
        self,
        fxt_project_with_anomaly_classification_task,
        fxt_dataset_non_empty_2,
    ) -> None:
        # Arrange
        project = fxt_project_with_anomaly_classification_task

        # Act
        with (
            patch.object(
                DatasetHelpers,
                "construct_testing_dataset",
                return_value=fxt_dataset_non_empty_2,
            ) as mock_dataset_factory_testing_dataset,
            patch.object(DatasetRepo, "__init__", return_value=None),
            patch.object(DatasetRepo, "save_deep", return_value=None),
        ):
            CreateTaskTestingDatasetCommand(
                project,
                project.get_training_dataset_storage(),
                project.task_ids[0],
            ).execute()

        # Assert
        mock_dataset_factory_testing_dataset.assert_called_once()
