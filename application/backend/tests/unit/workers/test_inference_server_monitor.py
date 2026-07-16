# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
from unittest.mock import MagicMock, patch
from uuid import uuid4

from app.models import BatchInferenceInput, BatchInferenceResult, Label
from app.workers import InferenceServerMonitorThread


class TestInferenceServerMonitorThread:
    def test_set_inference_model_success(self) -> None:
        project_id = uuid4()
        model_id = uuid4()
        mock_server = MagicMock()
        orig_set_inference_model = mock_server.set_inference_model
        orig_set_inference_model.return_value = True

        monitor_thread = InferenceServerMonitorThread(server=mock_server, stop_event=MagicMock())
        monitor_thread.setup()

        # Simulate loading a model with a TTL
        ttl_value = 60
        returned_result = mock_server.set_inference_model(
            project_id=project_id, model_id=model_id, device="AUTO", ttl=ttl_value
        )

        assert returned_result is True
        assert monitor_thread._ttl == ttl_value
        assert monitor_thread._ttl_start_time > 0
        orig_set_inference_model.assert_called_once_with(
            project_id=project_id, model_id=model_id, device="AUTO", ttl=ttl_value, model_variant_id=None
        )

    def test_set_inference_model_not_loaded(self) -> None:
        project_id = uuid4()
        model_id = uuid4()
        mock_server = MagicMock()
        orig_set_inference_model = mock_server.set_inference_model
        orig_set_inference_model.return_value = False

        monitor_thread = InferenceServerMonitorThread(server=mock_server, stop_event=MagicMock())
        monitor_thread.setup()

        # Simulate loading a model with a TTL
        returned_result = mock_server.set_inference_model(
            project_id=project_id, model_id=model_id, device="AUTO", ttl=60
        )

        assert returned_result is False
        assert monitor_thread._ttl == 0
        assert monitor_thread._ttl_start_time < 0
        orig_set_inference_model.assert_called_once_with(
            project_id=project_id, model_id=model_id, device="AUTO", ttl=60, model_variant_id=None
        )

    def test_infer_batch(self) -> None:
        label = MagicMock(spec=Label)
        input = MagicMock(spec=BatchInferenceInput)
        result = MagicMock(spec=BatchInferenceResult)
        mock_server = MagicMock()
        orig_infer_batch = mock_server.infer_batch
        orig_infer_batch.return_value = result

        monitor_thread = InferenceServerMonitorThread(server=mock_server, stop_event=MagicMock())
        monitor_thread.setup()

        # Simulate inference request
        returned_result = mock_server.infer_batch(labels=[label], inputs=[input])

        assert returned_result == result
        assert monitor_thread._ttl_start_time > 0
        orig_infer_batch.assert_called_once_with(labels=[label], inputs=[input])

    def test_stop(self) -> None:
        mock_server = MagicMock()
        orig_stop = mock_server.stop

        monitor_thread = InferenceServerMonitorThread(server=mock_server, stop_event=MagicMock())
        monitor_thread.setup()

        # Simulate stop request
        mock_server.stop()

        assert monitor_thread._ttl_start_time < 0
        orig_stop.assert_called_once_with()

    def test_run_loop_ttl_expired(self) -> None:
        mock_server = MagicMock()
        stop_method = mock_server.stop

        stop_event = MagicMock()
        stop_event.is_set.side_effect = [False, True]  # Run loop once then stop
        monitor_thread = InferenceServerMonitorThread(server=mock_server, stop_event=stop_event)
        monitor_thread.setup()
        monitor_thread._ttl = 1
        monitor_thread._ttl_start_time = 1

        with patch("time.perf_counter", return_value=100):
            monitor_thread.run_loop()

        assert monitor_thread._ttl_start_time < 0  # Check that TTL countdown is reset
        stop_method.assert_called_once_with()  # Check that server stop was called on TTL expiration

    def test_run_loop_ttl_not_expired(self) -> None:
        mock_server = MagicMock()
        stop_method = mock_server.stop

        stop_event = MagicMock()
        stop_event.is_set.side_effect = [False, True]  # Run loop once then stop
        monitor_thread = InferenceServerMonitorThread(server=mock_server, stop_event=stop_event)
        monitor_thread.setup()
        monitor_thread._ttl = 1000
        monitor_thread._ttl_start_time = 1

        with patch("time.perf_counter", return_value=100):
            monitor_thread.run_loop()

        assert monitor_thread._ttl_start_time > 0
        stop_method.assert_not_called()

    def test_run_loop_survives_stop_error(self) -> None:
        """A failure while unloading the model must not kill the monitor thread, and must keep the
        countdown armed so the idle model is not left loaded indefinitely."""
        mock_server = MagicMock()

        stop_event = MagicMock()
        stop_event.is_set.side_effect = [False, True]  # Run loop once then stop
        monitor_thread = InferenceServerMonitorThread(server=mock_server, stop_event=stop_event)
        monitor_thread.setup()
        monitor_thread._ttl = 1
        monitor_thread._ttl_start_time = 1
        # Simulate the model unload raising an error.
        monitor_thread._orig_stop = MagicMock(side_effect=RuntimeError("unload failed"))

        with patch("time.perf_counter", return_value=100):
            # Must not raise despite the unload failure.
            monitor_thread.run_loop()

        monitor_thread._orig_stop.assert_called_once_with()
        # The countdown stays armed (NOT disabled) so the unload is retried later; a transient
        # failure must not leave an idle model loaded indefinitely.
        assert monitor_thread._ttl_start_time > 0
        assert monitor_thread._unload_failures == 1
        # A backoff is scheduled so the failing unload is not retried on every single tick.
        assert monitor_thread._next_unload_attempt > 100

    def test_run_loop_retries_unload_after_backoff_until_success(self) -> None:
        """After a transient unload failure, a later attempt (past the backoff) retries and succeeds."""
        mock_server = MagicMock()
        monitor_thread = InferenceServerMonitorThread(server=mock_server, stop_event=MagicMock())
        monitor_thread.setup()
        monitor_thread._ttl = 1
        monitor_thread._ttl_start_time = 1
        # Fail on the first unload attempt, then succeed on the next actual attempt.
        monitor_thread._orig_stop = MagicMock(side_effect=[RuntimeError("transient"), None])

        # First attempt: TTL expired, unload fails, backoff scheduled (2s -> next attempt at 102).
        with patch("time.perf_counter", return_value=100):
            monitor_thread._try_unload_expired_model()
        assert monitor_thread._orig_stop.call_count == 1
        assert monitor_thread._ttl_start_time > 0  # countdown stays armed
        assert monitor_thread._unload_failures == 1
        assert monitor_thread._next_unload_attempt == 102

        # Still within the backoff window: no new unload attempt is made.
        with patch("time.perf_counter", return_value=101):
            monitor_thread._try_unload_expired_model()
        assert monitor_thread._orig_stop.call_count == 1

        # Past the backoff: the retry succeeds, disarming the countdown and clearing retry state.
        with patch("time.perf_counter", return_value=200):
            monitor_thread._try_unload_expired_model()
        assert monitor_thread._orig_stop.call_count == 2
        assert monitor_thread._ttl_start_time < 0
        assert monitor_thread._unload_failures == 0
        assert monitor_thread._next_unload_attempt == 0.0

    def test_reset_unload_retry_state_on_model_load(self) -> None:
        """Loading a new model clears any pending failed-unload retry bookkeeping."""
        mock_server = MagicMock()
        mock_server.set_inference_model.return_value = True
        monitor_thread = InferenceServerMonitorThread(server=mock_server, stop_event=MagicMock())
        monitor_thread.setup()
        # Simulate leftover failure state from a previous model.
        monitor_thread._unload_failures = 3
        monitor_thread._next_unload_attempt = 999.0

        mock_server.set_inference_model(project_id=uuid4(), model_id=uuid4(), device="AUTO", ttl=60)

        assert monitor_thread._unload_failures == 0
        assert monitor_thread._next_unload_attempt == 0.0
