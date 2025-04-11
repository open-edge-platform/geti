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

from unittest.mock import MagicMock, call, patch

from scheduler.flyte import Flyte
from scheduler.loops.recovery import (
    check_and_recover_organization_if_needed,
    check_and_recover_organization_jobs_if_needed,
    run_recovery_loop,
)
from scheduler.state_machine import StateMachine

from geti_types import ID

ORG = ID("00000000-0000-0000-0000-000000000001")
WORK = ID("00000000-0000-0000-0000-000000000002")
job_id = ID("test_job")


def mock_flyte_client(self, *args, **kwargs) -> None:
    self.client = MagicMock()
    self.client.client = MagicMock()


def mock_state_machine(self, *args, **kwargs) -> None:
    return None


def reset_singletons() -> None:
    Flyte._instance = None  # type: ignore[attr-defined]
    StateMachine._instance = None  # type: ignore[attr-defined]


@patch(
    "scheduler.loops.recovery.check_and_recover_organization_if_needed",
)
@patch.object(StateMachine, "get_session_ids_with_jobs_not_in_final_state")
@patch.object(StateMachine, "__init__", new=mock_state_machine)
def test_run_recovery_loop_none(
    mock_get_session_ids_with_jobs_not_in_final_state,
    mock_check_and_recover_organization_if_needed,
    request,
) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    mock_get_session_ids_with_jobs_not_in_final_state.return_value = []

    # Act
    run_recovery_loop()

    # Assert
    mock_check_and_recover_organization_if_needed.assert_not_called()


@patch(
    "scheduler.loops.recovery.check_and_recover_organization_if_needed",
)
@patch.object(StateMachine, "get_session_ids_with_jobs_not_in_final_state")
@patch.object(StateMachine, "__init__", new=mock_state_machine)
def test_run_recovery_loop_org(
    mock_get_session_ids_with_jobs_not_in_final_state,
    mock_check_and_recover_organization_if_needed,
    request,
) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    mock_get_session_ids_with_jobs_not_in_final_state.return_value = {ORG: WORK}

    # Act
    run_recovery_loop()

    # Assert
    mock_check_and_recover_organization_if_needed.assert_called_once_with(organization_id=ORG, workspace_id=WORK)


@patch("scheduler.loops.recovery.check_and_recover_organization_jobs_if_needed")
@patch.object(StateMachine, "get_scheduled_jobs_not_in_final_state")
@patch.object(StateMachine, "__init__", new=mock_state_machine)
def test_check_and_recover_workspace_if_needed_empty_list(
    mock_get_scheduled_jobs_not_in_final_state,
    mock_check_and_recover_organization_jobs_if_needed,
    request,
) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    mock_get_scheduled_jobs_not_in_final_state.return_value = []

    # Act
    check_and_recover_organization_if_needed(organization_id=ORG, workspace_id=WORK)

    # Assert
    mock_get_scheduled_jobs_not_in_final_state.assert_called_once_with()
    mock_check_and_recover_organization_jobs_if_needed.assert_not_called()


@patch("scheduler.loops.recovery.check_and_recover_organization_jobs_if_needed")
@patch.object(StateMachine, "get_scheduled_jobs_not_in_final_state")
@patch.object(StateMachine, "__init__", new=mock_state_machine)
def test_check_and_recover_workspace_if_needed(
    mock_get_scheduled_jobs_not_in_final_state,
    mock_check_and_recover_organization_jobs_if_needed,
    request,
) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    active_jobs = range(116)
    mock_get_scheduled_jobs_not_in_final_state.return_value = active_jobs

    # Act
    check_and_recover_organization_if_needed(organization_id=ORG, workspace_id=WORK)

    # Assert
    mock_get_scheduled_jobs_not_in_final_state.assert_called_once_with()
    mock_check_and_recover_organization_jobs_if_needed.assert_has_calls(
        [
            call(jobs=list(active_jobs)[0:50]),
            call(jobs=list(active_jobs)[50:100]),
            call(jobs=list(active_jobs)[100:116]),
        ]
    )


@patch.object(Flyte, "list_workflow_executions")
@patch.object(StateMachine, "reset_job_to_submitted_state")
@patch.object(StateMachine, "__init__", new=mock_state_machine)
def test_check_and_recover_workspace_jobs_if_needed_empty_list(
    mock_reset_job_to_submitted_state,
    mock_list_workflow_executions,
    request,
) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    mock_list_workflow_executions.return_value = []

    # Act
    check_and_recover_organization_jobs_if_needed(jobs=[])

    # Assert
    mock_list_workflow_executions.assert_called_once_with(execution_names=[])
    mock_reset_job_to_submitted_state.assert_not_called()


@patch.object(Flyte, "list_workflow_executions")
@patch.object(StateMachine, "reset_job_to_submitted_state")
@patch.object(StateMachine, "__init__", new=mock_state_machine)
def test_check_and_recover_workspace_jobs_if_needed_job_found(
    mock_reset_job_to_submitted_state,
    mock_list_workflow_executions,
    request,
) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    execution_id = "execution"
    job = MagicMock()
    job.executions.main.execution_id = execution_id

    execution = MagicMock()
    execution.id.name = "execution"
    mock_list_workflow_executions.return_value = [execution]

    # Act
    check_and_recover_organization_jobs_if_needed(jobs=[job])

    # Assert
    mock_list_workflow_executions.assert_called_once_with(execution_names=["execution"])
    mock_reset_job_to_submitted_state.assert_not_called()


@patch.object(Flyte, "list_workflow_executions")
@patch.object(StateMachine, "reset_job_to_submitted_state")
@patch.object(StateMachine, "__init__", new=mock_state_machine)
def test_check_and_recover_workspace_jobs_if_needed_job_not_found(
    mock_reset_job_to_submitted_state,
    mock_list_workflow_executions,
    request,
) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    execution_id = "execution"
    job = MagicMock()
    job.executions.main.execution_id = execution_id

    mock_list_workflow_executions.return_value = []

    # Act
    check_and_recover_organization_jobs_if_needed(jobs=[job])

    # Assert
    mock_list_workflow_executions.assert_called_once_with(execution_names=["execution"])
    mock_reset_job_to_submitted_state.assert_called_once_with(job_id=job.id)
