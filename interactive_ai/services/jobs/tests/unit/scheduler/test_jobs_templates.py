# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
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
