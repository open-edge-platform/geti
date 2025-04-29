# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import atexit
import logging
import os
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor

from opentelemetry import trace

from policies import Prioritizer, ResourceManager

from geti_telemetry_tools import ENABLE_TRACING
from geti_types import RequestSource, make_session, session_context

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)  # type: ignore[attr-defined]

POLICY_LOOP_INTERVAL = int(os.environ.get("SCHEDULING_POLICY_SERVICE_LOOP_INTERVAL", 1))
logger.info(f"Running scheduling policy checks every {POLICY_LOOP_INTERVAL} second(s)")

RESOURCE_MANAGER_LOOP_INTERVAL = int(os.environ.get("RESOURCE_MANAGER_LOOP_INTERVAL", 60))
logger.info(f"Running resource manager every {RESOURCE_MANAGER_LOOP_INTERVAL} second(s)")

policy_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="scheduling_policy_service")
resource_manager_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="resource_manager")


def stop() -> None:
    """
    Stops the job scheduling policy service
    """
    logger.info("Shutting down")

    policy_executor.shutdown(wait=False)
    resource_manager_executor.shutdown(wait=False)


def start() -> None:
    """
    Control loop implementation
    """
    atexit.register(stop)

    policy_executor.submit(start_policy_loop)
    resource_manager_executor.submit(start_resource_manager_loop)


def start_loop(loop_id: str, loop: Callable, loop_interval: int) -> None:
    """
    Starts a loop
    :param loop_id: loop identifier
    :param loop: loop implementation
    :param loop_interval: loop interval
    """
    while True:
        try:
            if ENABLE_TRACING:
                with tracer.start_as_current_span(loop_id):
                    loop()
            else:
                loop()
        finally:
            time.sleep(loop_interval)


def start_policy_loop() -> None:
    """
    Job scheduling policy loop implementation
    """
    start_loop("job-scheduling-policy-loop", run_policy_loop, POLICY_LOOP_INTERVAL)


def start_resource_manager_loop() -> None:
    """
    Resource manager loop implementation
    """
    start_loop("resource-manager-loop", run_resource_manager_loop, RESOURCE_MANAGER_LOOP_INTERVAL)


def run_policy_loop() -> None:
    """
    Starts the control loop for the job scheduler
    """
    prioritizer = Prioritizer()
    try:
        logger.debug("Running job scheduling policy loop...")
        ids = prioritizer.get_session_ids_with_submitted_jobs()
        for organization_id, workspace_id in ids.items():
            with session_context(
                session=make_session(
                    organization_id=organization_id, workspace_id=workspace_id, source=RequestSource.INTERNAL
                )
            ):
                prioritizer.mark_next_jobs_as_ready_for_scheduling_from_submitted_queue()
    except Exception:
        logger.exception("Error occurred in job scheduling policy loop")
    finally:
        time.sleep(POLICY_LOOP_INTERVAL)


def run_resource_manager_loop() -> None:
    """
    Starts the resource manager loop
    """
    try:
        logger.debug("Running resource manager loop...")
        ResourceManager().refresh_available_resources()
    except Exception:
        logger.exception("Error occurred in resource manager loop")
    finally:
        time.sleep(RESOURCE_MANAGER_LOOP_INTERVAL)


if __name__ == "__main__":
    start()
