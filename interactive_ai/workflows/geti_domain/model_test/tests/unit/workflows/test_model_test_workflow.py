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
