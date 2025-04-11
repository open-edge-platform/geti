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
from unittest.mock import patch

import pytest
from jobs_common.utils.dataset_helpers import DatasetHelpers
from sc_sdk.repos import DatasetRepo, ModelTestResultRepo, ProjectRepo

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
                is_local_anomaly_test=False,
            )

        mock_lock_project.assert_called_once()
        assert result == fxt_dataset
