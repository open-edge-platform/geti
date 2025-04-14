# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import pytest
from flytekit.core.testing import task_mock

from job.tasks.import_project import import_project
from job.workflows.import_project_workflow import import_project_workflow


@pytest.mark.JobsComponent
class TestImportWorkflow:
    def test_import_workflow(self) -> None:
        # Arrange
        file_id = "dummy_file_id"
        project_name = "new_project_name"
        user_id = "dummy_user_id"

        # Act
        with task_mock(import_project) as mock_import_project_task:
            import_project_workflow(
                file_id=file_id,
                keep_original_dates=False,
                project_name=project_name,
                user_id=user_id,
            )

        # Assert
        mock_import_project_task.assert_called_with(
            file_id=file_id,
            keep_original_dates=False,
            project_name=project_name,
            user_id=user_id,
        )
