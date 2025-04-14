# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import pytest
from flytekit.core.testing import task_mock

from job.tasks.model_testing import run_model_test
from job.workflows.model_test_workflow import model_test_workflow


@pytest.mark.JobsComponent
class TestModelTest:
    def test_model_test(self) -> None:
        with (
            task_mock(run_model_test) as mock_model_test,
        ):
            model_test_workflow(
                project_id="project_id",
                model_test_result_id="model_test_result_id",
                is_local_anomaly_test=False,
            )
        mock_model_test.assert_called_once()
