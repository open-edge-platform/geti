# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from unittest.mock import MagicMock, call, patch

import pytest
from flyteidl.core.execution_pb2 import WorkflowExecution
from flytekit.exceptions.user import FlyteUserException
from flytekit.remote import FlyteWorkflowExecution

from model.job_state import JobState
from scheduler.flyte import Flyte
from scheduler.loops.cancellation import cancel_execution, cancel_main_job, run_cancellation_loop
from scheduler.state_machine import StateMachine

from geti_types import ID

job_id = ID("test_job")


def mock_flyte_client(self, *args, **kwargs) -> None:
    self.client = MagicMock()
    self.client.client = MagicMock()


def mock_flyte_execution(self, *args, **kwargs) -> None:
    self._closure = MagicMock()
    self._id = MagicMock()


def mock_state_machine(self, *args, **kwargs) -> None:
    return None


def reset_singletons() -> None:
    Flyte._instance = None  # type: ignore[attr-defined]
    StateMachine._instance = None  # type: ignore[attr-defined]


@patch(
    "scheduler.loops.cancellation.cancel_main_job",
)
@patch(
    "scheduler.loops.cancellation.session_context",
)
@patch.object(StateMachine, "set_and_publish_cancelled_state")
@patch.object(StateMachine, "get_cancelled_job")
@patch.object(StateMachine, "find_and_lock_job_for_canceling")
@patch.object(StateMachine, "__init__", new=mock_state_machine)
def test_run_cancellation_loop_none(
    mock_find_and_lock_job_for_canceling,
    mock_get_cancelled_job,
    mock_set_and_publish_cancelled_state,
    mock_session_context,
    mock_cancel_main_job,
    request,
) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    mock_find_and_lock_job_for_canceling.return_value = None
    mock_get_cancelled_job.return_value = None

    # Act
    run_cancellation_loop()

    # Assert
    mock_find_and_lock_job_for_canceling.assert_called_once_with()
    mock_get_cancelled_job.assert_called_once_with(job_states=(JobState.SUBMITTED, JobState.READY_FOR_SCHEDULING))
    mock_session_context.assert_not_called()
    mock_cancel_main_job.assert_not_called()
    mock_set_and_publish_cancelled_state.assert_not_called()


@patch(
    "scheduler.loops.cancellation.cancel_main_job",
)
@patch(
    "scheduler.loops.cancellation.session_context",
)
@patch.object(StateMachine, "set_and_publish_cancelled_state")
@patch.object(StateMachine, "get_cancelled_job")
@patch.object(StateMachine, "find_and_lock_job_for_canceling")
@patch.object(StateMachine, "__init__", new=mock_state_machine)
def test_run_cancellation_loop_cancel_main_job(
    mock_find_and_lock_job_for_canceling,
    mock_get_cancelled_job,
    mock_set_and_publish_cancelled_state,
    mock_session_context,
    mock_cancel_main_job,
    request,
) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    job = MagicMock()
    mock_find_and_lock_job_for_canceling.side_effect = [job, None]
    mock_get_cancelled_job.return_value = None

    # Act
    run_cancellation_loop()

    # Assert
    mock_find_and_lock_job_for_canceling.assert_has_calls([call(), call()])
    mock_get_cancelled_job.assert_called_once_with(job_states=(JobState.SUBMITTED, JobState.READY_FOR_SCHEDULING))
    mock_session_context.assert_called_once_with(session=job.session)
    mock_cancel_main_job.assert_called_once_with(job_id=job.id)
    mock_set_and_publish_cancelled_state.assert_not_called()


@patch(
    "scheduler.loops.cancellation.cancel_main_job",
)
@patch(
    "scheduler.loops.cancellation.session_context",
)
@patch.object(StateMachine, "set_and_publish_cancelled_state")
@patch.object(StateMachine, "get_cancelled_job")
@patch.object(StateMachine, "find_and_lock_job_for_canceling")
@patch.object(StateMachine, "__init__", new=mock_state_machine)
def test_run_cancellation_loop_set_and_publish_cancelled_state(
    mock_find_and_lock_job_for_canceling,
    mock_get_cancelled_job,
    mock_set_and_publish_cancelled_state,
    mock_session_context,
    mock_cancel_main_job,
    request,
) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    job = MagicMock()
    mock_find_and_lock_job_for_canceling.return_value = None
    mock_get_cancelled_job.side_effect = [job, None]

    # Act
    run_cancellation_loop()

    # Assert
    mock_find_and_lock_job_for_canceling.assert_called_once_with()
    mock_get_cancelled_job.assert_has_calls(
        [
            call(job_states=(JobState.SUBMITTED, JobState.READY_FOR_SCHEDULING)),
            call(job_states=(JobState.SUBMITTED, JobState.READY_FOR_SCHEDULING)),
        ]
    )
    mock_session_context.assert_called_once_with(session=job.session)
    mock_cancel_main_job.assert_not_called()
    mock_set_and_publish_cancelled_state.assert_called_once_with(job_id=job.id)


@patch(
    "scheduler.loops.cancellation.cancel_execution",
)
@patch.object(StateMachine, "set_ready_for_revert_state")
@patch.object(StateMachine, "drop_cancelled_flag")
@patch.object(StateMachine, "reset_canceling_job")
@patch.object(StateMachine, "get_by_id")
@patch.object(StateMachine, "__init__", new=mock_state_machine)
def test_cancel_main_job_not_found(
    mock_get_by_id,
    mock_reset_canceling_job,
    mock_drop_cancelled_flag,
    mock_set_ready_for_revert_state,
    mock_cancel_execution,
    fxt_job,
    request,
) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    mock_get_by_id.return_value = None

    # Act
    cancel_main_job(job_id=job_id)

    # Assert
    mock_get_by_id.assert_called_once_with(job_id=job_id)
    mock_reset_canceling_job.assert_not_called()
    mock_drop_cancelled_flag.assert_not_called()
    mock_set_ready_for_revert_state.assert_not_called()
    mock_cancel_execution.assert_not_called()


@patch(
    "scheduler.loops.cancellation.cancel_execution",
    side_effect=FlyteUserException("Failed to cancel execution"),
)
@patch.object(StateMachine, "set_ready_for_revert_state")
@patch.object(StateMachine, "drop_cancelled_flag")
@patch.object(StateMachine, "reset_canceling_job")
@patch.object(StateMachine, "get_by_id")
@patch.object(StateMachine, "__init__", new=mock_state_machine)
def test_cancel_main_job_failure(
    mock_get_by_id,
    mock_reset_canceling_job,
    mock_drop_cancelled_flag,
    mock_set_ready_for_revert_state,
    mock_cancel_execution,
    fxt_job,
    request,
) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    fxt_job.executions.main.execution_id = "execution_id"
    mock_get_by_id.return_value = fxt_job

    # Act
    cancel_main_job(job_id=job_id)

    # Assert
    mock_get_by_id.assert_called_once_with(job_id=job_id)
    mock_reset_canceling_job.assert_called_once_with(job_id=job_id)
    mock_drop_cancelled_flag.assert_not_called()
    mock_set_ready_for_revert_state.assert_not_called()
    mock_cancel_execution.assert_called_once_with(execution_name="execution_id")


@patch(
    "scheduler.loops.cancellation.cancel_execution",
)
@patch.object(StateMachine, "set_ready_for_revert_state")
@patch.object(StateMachine, "drop_cancelled_flag")
@patch.object(StateMachine, "reset_canceling_job")
@patch.object(StateMachine, "get_by_id")
@patch.object(StateMachine, "__init__", new=mock_state_machine)
def test_cancel_main_job_success(
    mock_get_by_id,
    mock_reset_canceling_job,
    mock_drop_cancelled_flag,
    mock_set_ready_for_revert_state,
    mock_cancel_execution,
    fxt_job,
    request,
) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    fxt_job.executions.main.execution_id = "execution_id"
    mock_get_by_id.return_value = fxt_job

    # Act
    cancel_main_job(job_id=job_id)

    # Assert
    mock_get_by_id.assert_called_once_with(job_id=job_id)
    mock_reset_canceling_job.assert_not_called()
    mock_drop_cancelled_flag.assert_not_called()
    mock_set_ready_for_revert_state.assert_called_once_with(job_id=job_id)
    mock_cancel_execution.assert_called_once_with(execution_name="execution_id")


@patch(
    "scheduler.loops.cancellation.cancel_execution",
)
@patch.object(StateMachine, "set_ready_for_revert_state")
@patch.object(StateMachine, "drop_cancelled_flag")
@patch.object(StateMachine, "reset_canceling_job")
@patch.object(StateMachine, "get_by_id")
@patch.object(StateMachine, "__init__", new=mock_state_machine)
def test_cancel_main_job_max_retry_counter(
    mock_get_by_id,
    mock_reset_canceling_job,
    mock_drop_cancelled_flag,
    mock_set_ready_for_revert_state,
    mock_cancel_execution,
    fxt_job,
    request,
) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    fxt_job.executions.main.cancel_retry_counter = 10
    fxt_job.executions.main.execution_id = "execution_id"
    mock_get_by_id.return_value = fxt_job

    # Act
    cancel_main_job(job_id=job_id)

    # Assert
    mock_get_by_id.assert_called_once_with(job_id=job_id)
    mock_reset_canceling_job.assert_not_called()
    mock_drop_cancelled_flag.assert_called_once_with(job_id=job_id)
    mock_set_ready_for_revert_state.assert_not_called()
    mock_cancel_execution.assert_not_called()


@patch.object(Flyte, "cancel_workflow_execution")
@patch.object(Flyte, "fetch_workflow_execution")
@patch.object(Flyte, "__init__", new=mock_flyte_client)
def test_cancel_execution_not_found(
    mock_flyte_fetch_workflow_execution,
    mock_flyte_cancel_workflow_execution,
    request,
) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    mock_flyte_fetch_workflow_execution.return_value = None

    # Act
    cancel_execution(execution_name="execution_name")

    # Assert
    mock_flyte_fetch_workflow_execution.assert_called_once_with(execution_name="execution_name")
    mock_flyte_cancel_workflow_execution.assert_not_called()


@pytest.mark.parametrize("phase", [WorkflowExecution.ABORTED, WorkflowExecution.ABORTING])
@patch.object(Flyte, "cancel_workflow_execution")
@patch.object(Flyte, "fetch_workflow_execution")
@patch.object(Flyte, "__init__", new=mock_flyte_client)
def test_cancel_execution_aborted_or_aborting(
    mock_flyte_fetch_workflow_execution,
    mock_flyte_cancel_workflow_execution,
    request,
    phase,
) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    execution = MagicMock()
    execution.closure.phase = phase
    mock_flyte_fetch_workflow_execution.return_value = execution

    # Act
    cancel_execution(execution_name="execution_name")

    # Assert
    mock_flyte_fetch_workflow_execution.assert_called_once_with(execution_name="execution_name")
    mock_flyte_cancel_workflow_execution.assert_not_called()


@patch.object(Flyte, "cancel_workflow_execution")
@patch.object(Flyte, "fetch_workflow_execution")
@patch.object(Flyte, "__init__", new=mock_flyte_client)
def test_cancel_execution(
    mock_flyte_fetch_workflow_execution,
    mock_flyte_cancel_workflow_execution,
    request,
) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    execution = MagicMock()
    execution.is_done = False
    mock_flyte_fetch_workflow_execution.return_value = execution

    # Act
    cancel_execution(execution_name="execution_name")

    # Assert
    mock_flyte_fetch_workflow_execution.assert_called_once_with(execution_name="execution_name")
    mock_flyte_cancel_workflow_execution.assert_called_once_with(execution=execution)


@pytest.mark.parametrize(
    "phase",
    [WorkflowExecution.SUCCEEDED, WorkflowExecution.FAILING, WorkflowExecution.FAILED, WorkflowExecution.TIMED_OUT],
)
@patch.object(Flyte, "cancel_workflow_execution")
@patch.object(Flyte, "fetch_workflow_execution")
@patch.object(Flyte, "__init__", new=mock_flyte_client)
@patch.object(FlyteWorkflowExecution, "__init__", new=mock_flyte_execution)
def test_cancel_execution_terminated_or_terminating(
    mock_flyte_fetch_workflow_execution,
    mock_flyte_cancel_workflow_execution,
    request,
    phase,
) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    execution = FlyteWorkflowExecution()
    execution._closure.phase = phase
    execution._id.name = "mock_execution_name"
    mock_flyte_fetch_workflow_execution.return_value = execution

    # Act
    cancel_execution(execution_name="execution_name")

    # Assert
    mock_flyte_fetch_workflow_execution.assert_called_once_with(execution_name="execution_name")
    mock_flyte_cancel_workflow_execution.assert_not_called()
