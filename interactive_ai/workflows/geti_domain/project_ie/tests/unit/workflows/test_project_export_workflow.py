# INTEL CONFIDENTIAL
#
# Copyright (C) 2024 Intel Corporation
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
