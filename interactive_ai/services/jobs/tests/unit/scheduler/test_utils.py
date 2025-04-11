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

import os
from unittest.mock import patch

import pytest

from scheduler.utils import get_main_execution_name, get_revert_execution_name, resolve_main_job, resolve_revert_job


@pytest.mark.parametrize(
    "workflow_name, workflow_version, expected_exception, expected_result",
    [
        (None, None, True, None),
        ("job.train_job.workflow", None, True, None),
        (None, "v1", True, None),
        ("job.train_job.workflow", "v1", False, ("job.train_job.workflow", "v1")),
    ],
    ids=["no_env_vars", "no_version", "no_name", "correct"],
)
def test_resolve_main_job(
    workflow_name: str | None,
    workflow_version: str | None,
    expected_exception,
    expected_result,
) -> None:
    # Arrange
    env_vars = {}
    if workflow_name is not None:
        env_vars["JOB_TRAIN_FLYTE_WORKFLOW_NAME"] = workflow_name
    if workflow_version is not None:
        env_vars["JOB_TRAIN_FLYTE_WORKFLOW_VERSION"] = workflow_version

    # Act
    with patch.dict(os.environ, env_vars):
        exception = False
        result = ("", "")
        try:
            result = resolve_main_job(job_type="train")
        except Exception:
            exception = True

    # Assert
    assert exception == expected_exception
    if not expected_exception:
        assert result == expected_result


@pytest.mark.parametrize(
    "workflow_name, workflow_version, expected_result",
    [
        (None, None, None),
        ("job.train_job.workflow_revert", None, None),
        (None, "v1", None),
        (
            "job.train_job.workflow_revert",
            "v1",
            ("job.train_job.workflow_revert", "v1"),
        ),
    ],
    ids=["no_env_vars", "no_version", "no_name", "correct"],
)
def test_resolve_revert_job(
    workflow_name: str | None,
    workflow_version: str | None,
    expected_result,
) -> None:
    # Arrange
    env_vars = {}
    if workflow_name is not None:
        env_vars["JOB_TRAIN_REVERT_FLYTE_WORKFLOW_NAME"] = workflow_name
    if workflow_version is not None:
        env_vars["JOB_TRAIN_REVERT_FLYTE_WORKFLOW_VERSION"] = workflow_version

    # Act
    with patch.dict(os.environ, env_vars):
        result = resolve_revert_job(job_type="train")

    # Assert
    assert result == expected_result


def test_get_main_execution_name() -> None:
    # Arrange

    # Act
    execution_name = get_main_execution_name(job_id="jobid")

    # Assert
    assert execution_name == "ex-jobid"


def test_get_revert_execution_name() -> None:
    # Arrange

    # Act
    execution_name = get_revert_execution_name(job_id="jobid")

    # Assert
    assert execution_name == "ex-jobid-revert"
