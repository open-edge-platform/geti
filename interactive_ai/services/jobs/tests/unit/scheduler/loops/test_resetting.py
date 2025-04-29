# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from unittest.mock import ANY, patch

from scheduler.loops.resetting import reset_timed_out_jobs_processings, run_resetting_loop
from scheduler.state_machine import StateMachine


def mock_state_machine(self, *args, **kwargs) -> None:
    return None


def reset_singletons() -> None:
    StateMachine._instance = None  # type: ignore[attr-defined]


@patch(
    "scheduler.loops.resetting.reset_timed_out_jobs_processings",
)
@patch.object(StateMachine, "__init__", new=mock_state_machine)
def test_run_resetting_loop(
    mock_reset_timed_out_jobs_processings,
    request,
) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange

    # Act
    run_resetting_loop()

    # Assert
    mock_reset_timed_out_jobs_processings.assert_called_once_with()


@patch.object(StateMachine, "reset_revert_scheduling_jobs")
@patch.object(StateMachine, "reset_scheduling_jobs")
@patch.object(StateMachine, "reset_canceling_jobs")
@patch.object(StateMachine, "__init__", new=mock_state_machine)
def test_reset_timed_out_jobs_processings(
    mock_js_reset_canceling_jobs,
    mock_js_reset_scheduling_jobs,
    mock_js_reset_revert_scheduling_jobs,
    request,
) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    mock_js_reset_canceling_jobs.return_value = 2
    mock_js_reset_scheduling_jobs.return_value = 3
    mock_js_reset_revert_scheduling_jobs.return_value = 4

    # Act
    reset_timed_out_jobs_processings()

    # Assert
    mock_js_reset_canceling_jobs.assert_called_once_with(threshold=ANY)
    mock_js_reset_scheduling_jobs.assert_called_once_with(threshold=ANY)
    mock_js_reset_revert_scheduling_jobs.assert_called_once_with(threshold=ANY)
