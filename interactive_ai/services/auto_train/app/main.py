# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""Entry point and main control loop of the auto-train controller"""

# ruff: noqa: E402
# Note: logging must be initialized before importing other modules
from telemetry_config import setup_telemetry

from grpc_interfaces.job_submission.client import InsufficientBalanceException

setup_telemetry()

import logging
import os
import time
from contextlib import nullcontext

from controller import AutoTrainController
from entities import NullAutoTrainActivationRequest
from exceptions import InvalidAutoTrainRequestError, JobSubmissionError

from geti_telemetry_tools import ENABLE_TRACING
from geti_telemetry_tools.tracing.common import tracer_provider

logger = logging.getLogger(__name__)
tracer = tracer_provider.get_tracer(__name__)

AUTO_TRAIN_CONTROLLER_LOOP_INTERVAL = int(os.environ.get("AUTO_TRAIN_CONTROLLER_LOOP_INTERVAL", 5))  # noqa: PLW1508
logger.info(f"Auto-train controller loop is configured to run every {AUTO_TRAIN_CONTROLLER_LOOP_INTERVAL} second(s)")
AUTO_TRAIN_DEBOUNCING_PERIOD = int(os.environ.get("AUTO_TRAIN_DEBOUNCING_PERIOD", 5))  # noqa: PLW1508
logger.info(f"Auto-train debouncing period is configured as {AUTO_TRAIN_DEBOUNCING_PERIOD} second(s)")
AUTO_TRAIN_JOB_SUBMISSION_COOLDOWN = int(os.environ.get("AUTO_TRAIN_JOB_SUBMISSION_COOLDOWN", 60))  # noqa: PLW1508
logger.info(
    f"Auto-train job submission cooldown period is configured as {AUTO_TRAIN_JOB_SUBMISSION_COOLDOWN} second(s)"
)
JOB_SERVICE_GRPC_ADDRESS = os.environ.get("JOB_SERVICE_ADDRESS", "localhost:50051")


def run_controller_loop() -> None:
    """Runs the auto-train controller loop iteration"""
    controller: AutoTrainController | None = None
    logger.debug("Auto-train control loop: new iteration")
    try:
        controller = AutoTrainController(
            debouncing_period=AUTO_TRAIN_DEBOUNCING_PERIOD,
            jobs_grpc_client_address=JOB_SERVICE_GRPC_ADDRESS,
            job_submission_cooldown=AUTO_TRAIN_JOB_SUBMISSION_COOLDOWN,
        )
        while not isinstance((ready_request := controller.find_ready_request()), NullAutoTrainActivationRequest):
            try:
                controller.submit_train_job(auto_train_request=ready_request)
            except (InvalidAutoTrainRequestError, JobSubmissionError, InsufficientBalanceException) as exc:
                # Log the error, then remove the request to prevent repeated failures (no retry)
                logger.exception(f"Cannot start auto-train for task {ready_request.task_node_id}: {exc}")
            controller.remove_request_by_task(task_node_id=ready_request.task_node_id)
    except Exception as exc:
        logger.exception(f"Internal error in the auto-train controller loop: {exc}")
    finally:
        if controller is not None:
            controller.shutdown()


def start_controller_loop() -> None:
    """Start the auto-train controller loop"""
    logger.info("Starting the auto-train controller loop")
    tracing_context = tracer.start_as_current_span("auto-train-control-loop") if ENABLE_TRACING else nullcontext()
    with tracing_context:
        while True:
            try:
                run_controller_loop()
            finally:
                time.sleep(AUTO_TRAIN_CONTROLLER_LOOP_INTERVAL)


if __name__ == "__main__":
    start_controller_loop()
