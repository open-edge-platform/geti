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

"""This module tests export workflow"""

import pytest
from flytekit.core.testing import task_mock

from job.tasks.export_tasks.export_dataset_task import export_dataset_task
from job.workflows.export_workflow import export_dataset_workflow

ORGANIZATION_ID = "organization_id"
PROJECT_ID = "project_id"
DATASET_ID = "dataset_id"
EXPORT_FORMAT = "coco"


@pytest.mark.JobsComponent
class TestExportWorkflow:
    def test_export_workflow(self) -> None:
        with task_mock(export_dataset_task) as mock_export_dataset_task:
            mock_export_dataset_task.return_value = "dataset_id"
            export_dataset_workflow(
                organization_id=ORGANIZATION_ID,
                project_id=PROJECT_ID,
                dataset_storage_id=DATASET_ID,
                include_unannotated=True,
                export_format=EXPORT_FORMAT,
                save_video_as_images=True,
            )
        mock_export_dataset_task.assert_called_with(
            organization_id=ORGANIZATION_ID,
            project_id=PROJECT_ID,
            dataset_storage_id=DATASET_ID,
            include_unannotated=True,
            export_format=EXPORT_FORMAT,
            save_video_as_images=True,
        )
