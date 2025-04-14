# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
