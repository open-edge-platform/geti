# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import time
from unittest.mock import Mock, call, patch

import pytest

from app.core.jobs.models import JobParams
from app.core.run import ExecutionContext
from app.execution.base import Execution, ExecutionErr, step


class TestStepDecorator:
    """Test suite for the @step decorator."""

    @pytest.mark.parametrize("percent", [0, 50])
    def test_step_calls_report_progress_on_success(self, percent):
        """Test that the decorator calls report_progress when the step starts and completes."""

        # Arrange
        class MockTrainer(Execution[JobParams]):
            def execute(self, params: JobParams) -> None:
                pass

            @step("Test Step", percent)
            def test_method(self) -> str:
                return "result"

        trainer = MockTrainer()
        with (
            patch.object(trainer, "update_message") as mock_update_message,
            patch.object(trainer, "_report_progress") as mock_report_progress,
        ):
            # Act
            result = trainer.test_method()

            # Assert
            assert result == "result"
            mock_update_message.assert_called_once_with("Started: Test Step")
            mock_report_progress.assert_called_once_with("Completed: Test Step", percent=percent)

    def test_step_decorator_reports_failure_on_exception(self):
        """Test that the decorator reports failure when an exception occurs."""

        # Arrange
        class CustomException(Exception):
            pass

        class MockTrainer(Execution[JobParams]):
            def execute(self, params: JobParams) -> None:
                pass

            @step("Failing Step")
            def failing_method(self) -> None:
                raise CustomException("Custom error")

        trainer = MockTrainer()

        with (
            pytest.raises(CustomException, match="Custom error"),
            patch.object(trainer, "update_message") as mock_update_message,
        ):
            # Act
            trainer.failing_method()

        # Assert
        mock_update_message.assert_has_calls(
            [call("Started: Failing Step"), call("Failed: Failing Step", level="ERROR")]
        )

    def test_step_decorator_reports_failure_on_execution_error(self):
        """Test that the decorator reports failure with the message from the error."""

        # Arrange
        class MockTrainer(Execution[JobParams]):
            def execute(self, params: JobParams) -> None:
                pass

            @step("Failing Step")
            def failing_method(self) -> None:
                raise ExecutionErr("Execution error")

        trainer = MockTrainer()

        with (
            pytest.raises(ExecutionErr, match="Execution error"),
            patch.object(trainer, "update_message") as mock_update_message,
        ):
            # Act
            trainer.failing_method()

        # Assert
        mock_update_message.assert_has_calls([call("Started: Failing Step"), call("Execution error", level="ERROR")])

    def test_step_decorator_pinned_message(self):
        """Test that the decorator doesn't override pinned message."""

        # Arrange
        class MockTrainer(Execution[JobParams]):
            def execute(self, params: JobParams) -> None:
                pass

            @step("Pinning Step")
            def pin_method(self) -> None:
                self.pin_message("Pinned message")

        trainer = MockTrainer()

        with (
            patch.object(trainer, "update_message") as mock_update_message,
            patch.object(trainer, "pin_message") as mock_pin_message,
        ):
            # Act
            trainer.pin_method()

            # Assert
            mock_update_message.assert_called_once_with("Started: Pinning Step")
            mock_pin_message.assert_called_once_with("Pinned message")


class TestHeartbeat:
    """Test suite for the heartbeat/liveness-signaling mechanism."""

    class _DummyExecution(Execution[JobParams]):
        def execute(self, params: JobParams) -> None:
            pass

    def test_heartbeat_forwards_to_context(self):
        """heartbeat() delegates to the execution context's heartbeat callback, when set."""
        execution = self._DummyExecution()
        mock_ctx = Mock(spec=ExecutionContext)
        execution._ctx = mock_ctx

        execution.heartbeat()

        mock_ctx.heartbeat.assert_called_once_with()

    def test_heartbeat_noop_without_context(self):
        """heartbeat() is a no-op when no execution context has been attached yet."""
        execution = self._DummyExecution()
        assert execution._ctx is None

        execution.heartbeat()  # must not raise

    def test_heartbeat_during_emits_periodic_heartbeats(self):
        """heartbeat_during() emits heartbeats on an interval while the wrapped block runs."""
        execution = self._DummyExecution()

        with (
            patch.object(execution, "heartbeat") as mock_heartbeat,
            execution.heartbeat_during(interval=0.01),
        ):
            time.sleep(0.06)

        assert mock_heartbeat.call_count >= 2

    def test_heartbeat_during_stops_emitting_after_context_exits(self):
        """No further heartbeats are emitted once the context manager has exited."""
        execution = self._DummyExecution()

        with (
            patch.object(execution, "heartbeat") as mock_heartbeat,
            execution.heartbeat_during(interval=0.01),
        ):
            time.sleep(0.03)

        count_at_exit = mock_heartbeat.call_count
        time.sleep(0.05)
        assert mock_heartbeat.call_count == count_at_exit

    def test_heartbeat_during_propagates_exceptions_from_wrapped_block(self):
        """Exceptions raised inside the wrapped block propagate, and heartbeats stop."""
        execution = self._DummyExecution()

        class CustomError(Exception):
            pass

        with pytest.raises(CustomError), execution.heartbeat_during(interval=0.01):
            raise CustomError("boom")

    def test_heartbeat_during_swallows_reporting_errors(self):
        """A failure while emitting a heartbeat must not crash the wrapped block."""
        execution = self._DummyExecution()

        with (
            patch.object(execution, "heartbeat", side_effect=RuntimeError("pipe closed")),
            execution.heartbeat_during(interval=0.01),
        ):
            time.sleep(0.03)
        # No exception should have propagated from the context manager despite the failures above.

    def test_heartbeat_during_stops_emitting_once_max_duration_elapses(self):
        """A genuinely hung block must stop being vouched for once max_duration is exceeded.

        This is the safeguard against a heartbeat being emitted forever for a call that has
        actually deadlocked/hung rather than one that's merely slow: the ceiling bounds how long
        heartbeat_during() may keep the job looking alive without any corroborating progress.
        """
        execution = self._DummyExecution()

        with (
            patch.object(execution, "heartbeat") as mock_heartbeat,
            execution.heartbeat_during(interval=0.01, max_duration=0.03),
        ):
            # Simulate a hung wrapped block that never returns on its own within the test window.
            time.sleep(0.09)

        count_after_ceiling = mock_heartbeat.call_count
        assert count_after_ceiling >= 2  # some heartbeats before the ceiling was hit

        # No further heartbeats should be emitted even though the (simulated hung) block kept the
        # context open well past max_duration.
        time.sleep(0.03)
        assert mock_heartbeat.call_count == count_after_ceiling

    def test_heartbeat_during_none_max_duration_disables_ceiling(self):
        """Passing max_duration=None restores the old unbounded-heartbeat behavior."""
        execution = self._DummyExecution()

        with (
            patch.object(execution, "heartbeat") as mock_heartbeat,
            execution.heartbeat_during(interval=0.01, max_duration=None),
        ):
            time.sleep(0.06)

        assert mock_heartbeat.call_count >= 2
