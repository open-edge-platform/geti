# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import pytest
from flytekit.core.testing import task_mock

from job.tasks.export_project import export_project
from job.workflows.export_project_workflow import export_project_workflow


@pytest.mark.JobsComponent
class TestExportWorkflow:
    def test_export_workflow(self) -> None:
        project_id = "project_id"
        with task_mock(export_project) as mock_export_project_task:
            export_project_workflow(
                project_id=project_id,
            )
        mock_export_project_task.assert_called_with(
            project_id=project_id,
        )
