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
from unittest.mock import patch

import pytest

from scheduler.jobs_templates import JobsTemplates, _JobTemplate


def mock_jobs_templates(self, *args, **kwargs) -> None:
    return None


def reset_singletons() -> None:
    JobsTemplates._instance = None  # type: ignore[attr-defined]


@patch.object(JobsTemplates, "__init__", new=mock_jobs_templates)
def test_get_job_steps_missing(request) -> None:
    request.addfinalizer(lambda: reset_singletons())

    # Arrange
    JobsTemplates().templates = []

    # Act
    with pytest.raises(RuntimeError):
        JobsTemplates().get_job_steps("train")

    # Assert


@patch.object(JobsTemplates, "__init__", new=mock_jobs_templates)
def test_get_job_steps(request) -> None:
    request.addfinalizer(lambda: reset_singletons())

    # Arrange
    steps = [{"name": "step", "task_id": "step"}]
    JobsTemplates().templates = [_JobTemplate(job_type="train", steps=steps)]

    # Act
    job_steps = JobsTemplates().get_job_steps("train")

    # Assert
    assert len(job_steps) == 1 and job_steps[0].name == "step" and job_steps[0].task_id == "step"
