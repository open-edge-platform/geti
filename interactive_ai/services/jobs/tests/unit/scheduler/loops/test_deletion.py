# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from unittest.mock import MagicMock, patch

from scheduler.flyte import Flyte
from scheduler.loops.deletion import run_deletion_loop
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


@patch.object(StateMachine, "delete_job")
@patch.object(StateMachine, "get_job_to_delete")
@patch.object(StateMachine, "__init__", new=mock_state_machine)
def test_run_deletion_loop_none(
    mock_get_job_to_delete,
    mock_delete_job,
    request,
) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    mock_get_job_to_delete.return_value = None

    # Act
    run_deletion_loop()

    # Assert
    mock_delete_job.assert_not_called()


@patch(
    "scheduler.loops.deletion.session_context",
)
@patch.object(StateMachine, "delete_job")
@patch.object(StateMachine, "get_job_to_delete")
@patch.object(StateMachine, "__init__", new=mock_state_machine)
def test_run_deletion_loop_delete_job(
    mock_get_job_to_delete,
    mock_delete_job,
    mock_session_context,
    request,
) -> None:
    request.addfinalizer(reset_singletons)

    # Arrange
    job = MagicMock()
    mock_get_job_to_delete.side_effect = [job, None]

    # Act
    run_deletion_loop()

    # Assert
    mock_session_context.assert_called_once_with(session=job.session)
    mock_delete_job.assert_called_once_with(job_id=job.id)
