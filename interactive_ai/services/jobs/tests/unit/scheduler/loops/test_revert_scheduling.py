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

from unittest.mock import MagicMock, patch

from flytekit.exceptions.user import FlyteUserException

from model.job import JobRevertFlyteExecution
from scheduler.flyte import ExecutionType, Flyte
from scheduler.loops.revert_scheduling import (
    run_revert_scheduling_loop,
    schedule_revert_job,
    start_execution,
    start_revert_execution,
)
from scheduler.state_machine import StateMachine

from geti_types import ID

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
    "scheduler.loops.revert_scheduling.schedule_revert_job",
)
@patch.object(StateMachine, "find_and_lock_job_for_reverting")
@patch.object(StateMachine, "__init__", new=mock_state_machine)
def test_run_revert_scheduling_loop_none(
    mock_find_and_lock_job_for_reverting,
    mock_schedule_revert_job,
    request,
) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    mock_find_and_lock_job_for_reverting.return_value = None

    # Act
    run_revert_scheduling_loop()

    # Assert
    mock_schedule_revert_job.assert_not_called()


@patch(
    "scheduler.loops.revert_scheduling.schedule_revert_job",
)
@patch(
    "scheduler.loops.revert_scheduling.session_context",
)
@patch.object(StateMachine, "find_and_lock_job_for_reverting")
@patch.object(StateMachine, "__init__", new=mock_state_machine)
def test_run_revert_scheduling_loop_schedule_revert_job(
    mock_find_and_lock_job_for_reverting,
    mock_session_context,
    mock_schedule_revert_job,
    request,
) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    job = MagicMock()
    mock_find_and_lock_job_for_reverting.side_effect = [job, None]

    # Act
    run_revert_scheduling_loop()

    # Assert
    mock_session_context.assert_called_once_with(session=job.session)
    mock_schedule_revert_job.assert_called_once_with(job_id=job.id)


@patch(
    "scheduler.loops.revert_scheduling.start_revert_execution",
)
@patch.object(StateMachine, "set_and_publish_failed_state")
@patch.object(StateMachine, "set_and_publish_cancelled_state")
@patch.object(StateMachine, "set_revert_scheduled_state")
@patch.object(StateMachine, "reset_revert_scheduling_job")
@patch.object(StateMachine, "get_by_id")
@patch.object(StateMachine, "__init__", new=mock_state_machine)
def test_schedule_revert_job_not_found(
    mock_js_get_by_id,
    mock_js_reset_revert_scheduling_job,
    mock_js_set_scheduled_state,
    mock_js_set_and_publish_cancelled_state,
    mock_js_set_and_publish_failed_state,
    mock_start_revert_execution,
    fxt_job,
    request,
) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    mock_js_get_by_id.return_value = None

    # Act
    schedule_revert_job(job_id=job_id)

    # Assert
    mock_js_get_by_id.assert_called_once_with(job_id=job_id)
    mock_js_reset_revert_scheduling_job.assert_not_called()
    mock_js_set_scheduled_state.assert_not_called()
    mock_js_set_and_publish_cancelled_state.assert_not_called()
    mock_js_set_and_publish_failed_state.assert_not_called()
    mock_start_revert_execution.assert_not_called()


@patch(
    "scheduler.loops.revert_scheduling.start_revert_execution",
    side_effect=FlyteUserException("Failed to start execution"),
)
@patch.object(StateMachine, "set_and_publish_failed_state")
@patch.object(StateMachine, "set_and_publish_cancelled_state")
@patch.object(StateMachine, "set_revert_scheduled_state")
@patch.object(StateMachine, "reset_revert_scheduling_job")
@patch.object(StateMachine, "get_by_id")
@patch.object(StateMachine, "__init__", new=mock_state_machine)
def test_schedule_revert_job_failure(
    mock_js_get_by_id,
    mock_js_reset_revert_scheduling_job,
    mock_js_set_revert_scheduled_state,
    mock_js_set_and_publish_cancelled_state,
    mock_js_set_and_publish_failed_state,
    mock_start_revert_execution,
    fxt_job,
    request,
) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    mock_js_get_by_id.return_value = fxt_job

    # Act
    schedule_revert_job(job_id=job_id)

    # Assert
    mock_js_get_by_id.assert_called_once_with(job_id=job_id)
    mock_js_reset_revert_scheduling_job.assert_called_once_with(job_id=job_id)
    mock_js_set_revert_scheduled_state.assert_not_called()
    mock_js_set_and_publish_cancelled_state.assert_not_called()
    mock_js_set_and_publish_failed_state.assert_not_called()
    mock_start_revert_execution.assert_called_once_with(job=fxt_job)


@patch("scheduler.loops.revert_scheduling.start_revert_execution")
@patch.object(StateMachine, "set_and_publish_failed_state")
@patch.object(StateMachine, "set_and_publish_cancelled_state")
@patch.object(StateMachine, "set_revert_scheduled_state")
@patch.object(StateMachine, "reset_revert_scheduling_job")
@patch.object(StateMachine, "get_by_id")
@patch.object(StateMachine, "__init__", new=mock_state_machine)
def test_schedule_revert_job_no_revert_cancelled(
    mock_js_get_by_id,
    mock_js_reset_revert_scheduling_job,
    mock_js_set_revert_scheduled_state,
    mock_js_set_and_publish_cancelled_state,
    mock_js_set_and_publish_failed_state,
    mock_start_revert_execution,
    fxt_job,
    request,
) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    fxt_job.cancellation_info.is_cancelled = True
    mock_js_get_by_id.return_value = fxt_job

    mock_start_revert_execution.return_value = None

    # Act
    schedule_revert_job(job_id=job_id)

    # Assert
    mock_js_get_by_id.assert_called_once_with(job_id=job_id)
    mock_js_reset_revert_scheduling_job.assert_not_called()
    mock_js_set_revert_scheduled_state.assert_not_called()
    mock_js_set_and_publish_cancelled_state.assert_called_once_with(job_id=job_id)
    mock_js_set_and_publish_failed_state.assert_not_called()
    mock_start_revert_execution.assert_called_once_with(job=fxt_job)


@patch("scheduler.loops.revert_scheduling.start_revert_execution")
@patch.object(StateMachine, "set_and_publish_failed_state")
@patch.object(StateMachine, "set_and_publish_cancelled_state")
@patch.object(StateMachine, "set_revert_scheduled_state")
@patch.object(StateMachine, "reset_revert_scheduling_job")
@patch.object(StateMachine, "get_by_id")
@patch.object(StateMachine, "__init__", new=mock_state_machine)
def test_schedule_revert_job_no_revert_failed(
    mock_js_get_by_id,
    mock_js_reset_revert_scheduling_job,
    mock_js_set_revert_scheduled_state,
    mock_js_set_and_publish_cancelled_state,
    mock_js_set_and_publish_failed_state,
    mock_start_revert_execution,
    fxt_job,
    request,
) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    fxt_job.cancellation_info.is_cancelled = False
    mock_js_get_by_id.return_value = fxt_job

    mock_start_revert_execution.return_value = None

    # Act
    schedule_revert_job(job_id=job_id)

    # Assert
    mock_js_get_by_id.assert_called_once_with(job_id=job_id)
    mock_js_reset_revert_scheduling_job.assert_not_called()
    mock_js_set_revert_scheduled_state.assert_not_called()
    mock_js_set_and_publish_cancelled_state.assert_not_called()
    mock_js_set_and_publish_failed_state.assert_called_once_with(job_id=job_id)
    mock_start_revert_execution.assert_called_once_with(job=fxt_job)


@patch("scheduler.loops.revert_scheduling.start_revert_execution")
@patch.object(StateMachine, "set_and_publish_failed_state")
@patch.object(StateMachine, "set_and_publish_cancelled_state")
@patch.object(StateMachine, "set_revert_scheduled_state")
@patch.object(StateMachine, "reset_revert_scheduling_job")
@patch.object(StateMachine, "get_by_id")
@patch.object(StateMachine, "__init__", new=mock_state_machine)
def test_schedule_revert_job_revert(
    mock_js_get_by_id,
    mock_js_reset_revert_scheduling_job,
    mock_js_set_revert_scheduled_state,
    mock_js_set_and_publish_cancelled_state,
    mock_js_set_and_publish_failed_state,
    mock_start_revert_execution,
    fxt_job,
    request,
) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    fxt_job.cancellation_info.is_cancelled = False
    mock_js_get_by_id.return_value = fxt_job

    execution = MagicMock()
    mock_start_revert_execution.return_value = execution

    # Act
    schedule_revert_job(job_id=job_id)

    # Assert
    mock_js_get_by_id.assert_called_once_with(job_id=job_id)
    mock_js_reset_revert_scheduling_job.assert_not_called()
    mock_js_set_revert_scheduled_state.assert_called_once_with(
        job_id=job_id,
        flyte_execution_id=execution.id.name,
    )
    mock_js_set_and_publish_cancelled_state.assert_not_called()
    mock_js_set_and_publish_failed_state.assert_not_called()
    mock_start_revert_execution.assert_called_once_with(job=fxt_job)


@patch("scheduler.loops.revert_scheduling.start_revert_execution")
@patch.object(StateMachine, "set_and_publish_failed_state")
@patch.object(StateMachine, "set_and_publish_cancelled_state")
@patch.object(StateMachine, "set_revert_scheduled_state")
@patch.object(StateMachine, "reset_revert_scheduling_job")
@patch.object(StateMachine, "get_by_id")
@patch.object(StateMachine, "__init__", new=mock_state_machine)
def test_schedule_revert_job_max_retry_counter_cancelled(
    mock_js_get_by_id,
    mock_js_reset_revert_scheduling_job,
    mock_js_set_revert_scheduled_state,
    mock_js_set_and_publish_cancelled_state,
    mock_js_set_and_publish_failed_state,
    mock_start_revert_execution,
    fxt_job,
    request,
) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    fxt_job.executions.revert = JobRevertFlyteExecution(start_retry_counter=10)
    fxt_job.cancellation_info.is_cancelled = True
    mock_js_get_by_id.return_value = fxt_job

    execution = MagicMock()
    mock_start_revert_execution.return_value = execution

    # Act
    schedule_revert_job(job_id=job_id)

    # Assert
    mock_js_get_by_id.assert_called_once_with(job_id=job_id)
    mock_js_reset_revert_scheduling_job.assert_not_called()
    mock_js_set_revert_scheduled_state.assert_not_called()
    mock_js_set_and_publish_failed_state.assert_not_called()
    mock_js_set_and_publish_cancelled_state.assert_called_once_with(job_id=job_id)
    mock_start_revert_execution.assert_not_called()


@patch("scheduler.loops.revert_scheduling.start_revert_execution")
@patch.object(StateMachine, "set_and_publish_failed_state")
@patch.object(StateMachine, "set_and_publish_cancelled_state")
@patch.object(StateMachine, "set_revert_scheduled_state")
@patch.object(StateMachine, "reset_revert_scheduling_job")
@patch.object(StateMachine, "get_by_id")
@patch.object(StateMachine, "__init__", new=mock_state_machine)
def test_schedule_revert_job_max_retry_counter_failed(
    mock_js_get_by_id,
    mock_js_reset_revert_scheduling_job,
    mock_js_set_revert_scheduled_state,
    mock_js_set_and_publish_cancelled_state,
    mock_js_set_and_publish_failed_state,
    mock_start_revert_execution,
    fxt_job,
    request,
) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    fxt_job.executions.revert = JobRevertFlyteExecution(start_retry_counter=10)
    fxt_job.cancellation_info.is_cancelled = False
    mock_js_get_by_id.return_value = fxt_job

    execution = MagicMock()
    mock_start_revert_execution.return_value = execution

    # Act
    schedule_revert_job(job_id=job_id)

    # Assert
    mock_js_get_by_id.assert_called_once_with(job_id=job_id)
    mock_js_reset_revert_scheduling_job.assert_not_called()
    mock_js_set_revert_scheduled_state.assert_not_called()
    mock_js_set_and_publish_failed_state.assert_called_once_with(job_id=job_id)
    mock_js_set_and_publish_cancelled_state.assert_not_called()
    mock_start_revert_execution.assert_not_called()


@patch(
    "scheduler.loops.revert_scheduling.start_execution",
)
@patch(
    "scheduler.loops.revert_scheduling.resolve_revert_job",
)
@patch(
    "scheduler.loops.revert_scheduling.get_revert_execution_name",
)
@patch.object(Flyte, "fetch_workflow")
@patch.object(Flyte, "__init__", new=mock_flyte_client)
def test_start_revert_execution_no_workflow_env_vars(
    mock_flyte_fetch_workflow,
    mock_get_revert_execution_name,
    mock_resolve_revert_job,
    mock_start_execution,
    fxt_job,
    request,
) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    mock_get_revert_execution_name.return_value = "execution_name"
    mock_resolve_revert_job.return_value = None

    # Act
    result = start_revert_execution(job=fxt_job)

    # Assert
    mock_flyte_fetch_workflow.assert_not_called()
    mock_get_revert_execution_name.assert_called_once_with(job_id=fxt_job.id)
    mock_resolve_revert_job.assert_called_once_with(job_type=fxt_job.type)
    mock_start_execution.assert_not_called()
    assert result is None


@patch(
    "scheduler.loops.revert_scheduling.start_execution",
)
@patch(
    "scheduler.loops.revert_scheduling.resolve_revert_job",
)
@patch(
    "scheduler.loops.revert_scheduling.get_revert_execution_name",
)
@patch.object(Flyte, "fetch_workflow")
@patch.object(Flyte, "__init__", new=mock_flyte_client)
def test_start_revert_execution_no_workflow(
    mock_flyte_fetch_workflow,
    mock_get_revert_execution_name,
    mock_resolve_revert_job,
    mock_start_execution,
    fxt_job,
    request,
) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    mock_get_revert_execution_name.return_value = "execution_name"
    mock_resolve_revert_job.return_value = ("workflow_name", "workflow_version")
    mock_flyte_fetch_workflow.return_value = None

    # Act
    result = start_revert_execution(job=fxt_job)

    # Assert
    mock_flyte_fetch_workflow.assert_called_once_with(
        workflow_name="workflow_name", workflow_version="workflow_version"
    )
    mock_get_revert_execution_name.assert_called_once_with(job_id=fxt_job.id)
    mock_resolve_revert_job.assert_called_once_with(job_type=fxt_job.type)
    mock_start_execution.assert_not_called()
    assert result is None


@patch(
    "scheduler.loops.revert_scheduling.start_execution",
)
@patch(
    "scheduler.loops.revert_scheduling.resolve_revert_job",
)
@patch(
    "scheduler.loops.revert_scheduling.get_revert_execution_name",
)
@patch.object(Flyte, "fetch_workflow")
@patch.object(Flyte, "__init__", new=mock_flyte_client)
def test_start_revert_execution(
    mock_flyte_fetch_workflow,
    mock_get_revert_execution_name,
    mock_resolve_revert_job,
    mock_start_execution,
    fxt_job,
    request,
) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    mock_get_revert_execution_name.return_value = "execution_name"
    mock_resolve_revert_job.return_value = ("workflow_name", "workflow_version")

    workflow = MagicMock()
    mock_flyte_fetch_workflow.return_value = workflow

    execution = MagicMock()
    mock_start_execution.return_value = execution

    # Act
    result = start_revert_execution(job=fxt_job)

    # Assert
    mock_flyte_fetch_workflow.assert_called_once_with(
        workflow_name="workflow_name", workflow_version="workflow_version"
    )
    mock_get_revert_execution_name.assert_called_once_with(job_id=fxt_job.id)
    mock_resolve_revert_job.assert_called_once_with(job_type=fxt_job.type)
    mock_start_execution.assert_called_once_with(
        job=fxt_job,
        workflow=workflow,
        execution_type=ExecutionType.REVERT,
        execution_name="execution_name",
        payload={},
    )
    assert result == execution


@patch.object(Flyte, "start_workflow_execution")
@patch.object(Flyte, "fetch_workflow_execution")
@patch.object(Flyte, "__init__", new=mock_flyte_client)
def test_start_execution_existing(
    mock_flyte_fetch_workflow_execution,
    mock_flyte_start_workflow_execution,
    fxt_job,
    request,
) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    workflow = MagicMock()

    execution = MagicMock()
    mock_flyte_fetch_workflow_execution.return_value = execution

    # Act
    result = start_execution(
        job=fxt_job,
        workflow=workflow,
        execution_type=ExecutionType.MAIN,
        execution_name="execution_name",
        payload={"key": "value"},
    )

    # Assert
    mock_flyte_fetch_workflow_execution.assert_called_once_with(execution_name="execution_name")
    mock_flyte_start_workflow_execution.assert_not_called()
    assert result == execution


@patch.object(Flyte, "start_workflow_execution")
@patch.object(Flyte, "fetch_workflow_execution")
@patch.object(Flyte, "__init__", new=mock_flyte_client)
def test_start_execution_new(
    mock_flyte_fetch_workflow_execution,
    mock_flyte_start_workflow_execution,
    fxt_job,
    request,
) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    workflow = MagicMock()
    execution = MagicMock()

    mock_flyte_fetch_workflow_execution.return_value = None
    mock_flyte_start_workflow_execution.return_value = execution

    # Act
    result = start_execution(
        job=fxt_job,
        workflow=workflow,
        execution_type=ExecutionType.MAIN,
        execution_name="execution_name",
        payload={"key": "value"},
    )

    # Assert
    mock_flyte_fetch_workflow_execution.assert_called_once_with(execution_name="execution_name")
    mock_flyte_start_workflow_execution.assert_called_once_with(
        workspace_id=fxt_job.workspace_id,
        job=fxt_job,
        project_id=fxt_job.project_id,
        execution_type=ExecutionType.MAIN,
        execution_name="execution_name",
        workflow=workflow,
        payload={"key": "value"},
        telemetry=fxt_job.telemetry,
        session=fxt_job.session,
    )
    assert result == execution
