# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import time
from collections.abc import Callable
from functools import wraps
from multiprocessing.synchronize import Event
from uuid import UUID

from loguru import logger

from app.models.system import DeviceInfo
from app.services.inference import InferenceServer
from app.workers.base import BaseThreadWorker

# When unloading an expired model fails, the attempt is retried with an exponential backoff
# (in seconds) capped at this value, instead of giving up. This prevents a single transient
# failure from leaving an idle model loaded indefinitely, while avoiding hammering the server on
# every monitor tick.
MAX_UNLOAD_RETRY_BACKOFF_SECONDS = 30.0


class InferenceServerMonitorThread(BaseThreadWorker):
    """
    Inference Server Monitor Thread manages the lifecycle of the inference model loaded in the Inference Server,
    ensuring that models are unloaded after their TTL expires.
    It monitors the inference server for model loading, inference requests, and model stopping events to track the TTL
    countdown and unload models when necessary.
    The thread runs in the background, periodically checking the status of the loaded model and performing actions
    based on the events it observes.
    This helps to optimize resource usage by ensuring that models are not kept loaded indefinitely when they are not
    being used for inference.
    """

    ROLE = "InferenceServerMonitor"

    def __init__(self, server: InferenceServer, stop_event: Event) -> None:
        super().__init__(stop_event=stop_event)

        self._server = server
        self._ttl = 0
        self._ttl_start_time = -1.0

        # Retry bookkeeping for failed model-unload attempts. While a TTL-expired model fails to
        # unload, the countdown stays armed and the unload is retried after an exponential backoff.
        self._unload_failures = 0
        self._next_unload_attempt = 0.0

        self._orig_stop: Callable[[], None] | None = None

    def setup(self) -> None:
        logger.debug("Setting up inference server")

        orig_set_inference_model = self._server.set_inference_model

        @wraps(orig_set_inference_model)
        def wrapped_set_inference_model(
            project_id: UUID,
            model_id: UUID,
            device: DeviceInfo,
            ttl: int,
            model_variant_id: UUID | None = None,
        ):
            model_loaded = orig_set_inference_model(
                project_id=project_id,
                model_id=model_id,
                device=device,
                ttl=ttl,
                model_variant_id=model_variant_id,
            )
            if model_loaded:
                self._ttl = ttl
                logger.debug("Model loaded with TTL of {} seconds, starting countdown", self._ttl)
                self._ttl_start_time = time.perf_counter()
                self._reset_unload_retry_state()
            return model_loaded

        self._server.set_inference_model = wrapped_set_inference_model

        orig_infer_batch = self._server.infer_batch

        @wraps(orig_infer_batch)
        def wrapped_infer_batch(*args, **kwargs):
            logger.debug("Batch inference requested, resetting TTL countdown")
            self._ttl_start_time = time.perf_counter()
            self._reset_unload_retry_state()
            return orig_infer_batch(*args, **kwargs)

        self._server.infer_batch = wrapped_infer_batch

        orig_stop = self._server.stop
        self._orig_stop = orig_stop

        @wraps(orig_stop)
        def wrapped_stop():
            logger.debug("Model stopped, stopping TTL countdown")
            self._ttl_start_time = -1.0
            self._reset_unload_retry_state()
            orig_stop()

        self._server.stop = wrapped_stop

    def _reset_unload_retry_state(self) -> None:
        """Clear the failed-unload retry bookkeeping (called when the model lifecycle changes)."""
        self._unload_failures = 0
        self._next_unload_attempt = 0.0

    def _try_unload_expired_model(self) -> None:
        """Unload the model if its TTL has expired, retrying failed attempts with backoff.

        Unlike simply disarming the countdown on failure, this keeps the countdown armed so a
        transient stop failure does not leave an idle model loaded indefinitely. Repeated failures
        are retried on later ticks with an exponential backoff to avoid hammering the server.
        """
        if self._ttl_start_time <= 0:
            return
        elapsed = time.perf_counter() - self._ttl_start_time
        if not (0 < self._ttl <= elapsed):
            return

        # TTL expired: attempt to unload, but not more often than the current backoff allows.
        now = time.perf_counter()
        if now < self._next_unload_attempt:
            return

        try:
            logger.debug("TTL of {} seconds expired, unloading model", self._ttl)
            self._orig_stop()  # pyrefly: ignore[not-callable]
        except Exception:
            self._unload_failures += 1
            backoff = min(2.0**self._unload_failures, MAX_UNLOAD_RETRY_BACKOFF_SECONDS)
            self._next_unload_attempt = now + backoff
            # Keep _ttl_start_time armed so the unload is retried after the backoff, rather than
            # disabling further attempts (which would leave an idle model loaded indefinitely).
            logger.exception(
                "Failed to unload model after TTL expiry (attempt {}); retrying in {}s.",
                self._unload_failures,
                backoff,
            )
            return

        # Unload succeeded: disarm the countdown and clear the retry bookkeeping.
        self._ttl_start_time = -1.0
        self._reset_unload_retry_state()

    def run_loop(self) -> None:
        while not self.should_stop():
            try:
                self._try_unload_expired_model()
            except Exception as e:
                # Defensive catch: a failure here must not kill the monitor thread; otherwise
                # models would never be unloaded again for the lifetime of the process. Schedule a
                # backoff so the model is not repeatedly retried every tick, then keep monitoring.
                self._unload_failures += 1
                backoff = min(2.0**self._unload_failures, MAX_UNLOAD_RETRY_BACKOFF_SECONDS)
                self._next_unload_attempt = time.perf_counter() + backoff
                logger.exception("Error while monitoring inference server model TTL; continuing {}", e)

            self.stop_aware_sleep(1)
