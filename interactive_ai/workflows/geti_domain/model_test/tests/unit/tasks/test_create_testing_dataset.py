# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from unittest.mock import patch

import pytest
from iai_core.repos import DatasetRepo, ModelTestResultRepo, ProjectRepo
from jobs_common.utils.dataset_helpers import DatasetHelpers

from job.tasks.model_testing import create_testing_dataset

WORKSPACE_ID = "workspace_id"
PROJECT_ID = "project_id"
MODEL_TEST_RESULT_ID = "model_test_result_id"
DATASET_STORAGE_ID = "dataset_storage_id"
MODEL_ID = "model_id"


@pytest.mark.JobsComponent
class TestCreateTestingDataset:
    def test_create_testing_dataset(
        self,
        fxt_empty_project,
        fxt_model_test_result,
        fxt_dataset,
    ) -> None:
        with (
            patch.object(ProjectRepo, "get_by_id", return_value=fxt_empty_project),
            patch.object(ModelTestResultRepo, "get_by_id", return_value=fxt_model_test_result),
            patch.object(ModelTestResultRepo, "save", return_value=None),
            patch.object(DatasetHelpers, "construct_testing_dataset", return_value=fxt_dataset),
            patch.object(ProjectRepo, "__init__", return_value=None),
            patch.object(DatasetRepo, "__init__", return_value=None),
            patch.object(DatasetRepo, "save_deep", return_value=None),
            patch.object(
                ModelTestResultRepo,
                "__init__",
                return_value=None,
            ),
            patch.object(ProjectRepo, "mark_locked") as mock_lock_project,
        ):
            result = create_testing_dataset(
                project_id=PROJECT_ID,
                model_test_result_id=MODEL_TEST_RESULT_ID,
            )

        mock_lock_project.assert_called_once()
        assert result == fxt_dataset
