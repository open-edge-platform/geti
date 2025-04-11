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
import atexit
import logging
import os
import time
from collections.abc import Callable
from concurrent.futures.thread import ThreadPoolExecutor
from multiprocessing import Process

from opentelemetry import trace

from scheduler.grpc_api.job_update_service import JobUpdateService
from scheduler.kafka_handler import ProgressHandler
from scheduler.loops.cancellation import run_cancellation_loop
from scheduler.loops.deletion import run_deletion_loop
from scheduler.loops.recovery import run_recovery_loop
from scheduler.loops.resetting import run_resetting_loop
from scheduler.loops.revert_scheduling import run_revert_scheduling_loop
from scheduler.loops.scheduling import run_scheduling_loop

from geti_telemetry_tools import ENABLE_TRACING, KafkaTelemetry

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)  # type: ignore[attr-defined]

SCHEDULER_SCHEDULING_LOOP_INTERVAL = int(os.environ.get("SCHEDULER_SCHEDULING_LOOP_INTERVAL", 1))
logger.info(f"Running scheduling loop every {SCHEDULER_SCHEDULING_LOOP_INTERVAL} second(s)")

SCHEDULER_SCHEDULING_LOOP_WORKERS = int(os.environ.get("SCHEDULER_SCHEDULING_LOOP_WORKERS", 1))
logger.info(f"Running scheduling loop with {SCHEDULER_SCHEDULING_LOOP_WORKERS} worker(s)")

SCHEDULER_REVERT_SCHEDULING_LOOP_INTERVAL = int(os.environ.get("SCHEDULER_REVERT_SCHEDULING_LOOP_INTERVAL", 1))
logger.info(f"Running revert scheduling loop every {SCHEDULER_REVERT_SCHEDULING_LOOP_INTERVAL} second(s)")

SCHEDULER_REVERT_SCHEDULING_LOOP_WORKERS = int(os.environ.get("SCHEDULER_REVERT_SCHEDULING_LOOP_WORKERS", 1))
logger.info(f"Running revert scheduling loop with {SCHEDULER_REVERT_SCHEDULING_LOOP_WORKERS} worker(s)")

SCHEDULER_CANCELLATION_LOOP_INTERVAL = int(os.environ.get("SCHEDULER_CANCELLATION_LOOP_INTERVAL", 1))
logger.info(f"Running cancellation loop every {SCHEDULER_CANCELLATION_LOOP_INTERVAL} second(s)")

SCHEDULER_CANCELLATION_LOOP_WORKERS = int(os.environ.get("SCHEDULER_CANCELLATION_LOOP_WORKERS", 1))
logger.info(f"Running cancellation loop with {SCHEDULER_CANCELLATION_LOOP_WORKERS} worker(s)")

SCHEDULER_RESETTING_LOOP_INTERVAL = int(os.environ.get("SCHEDULER_RESETTING_LOOP_INTERVAL", 10))
logger.info(f"Running resetting loop every {SCHEDULER_RESETTING_LOOP_INTERVAL} second(s)")

SCHEDULER_RESETTING_LOOP_WORKERS = int(os.environ.get("SCHEDULER_RESETTING_LOOP_WORKERS", 1))
logger.info(f"Running resetting loop with {SCHEDULER_RESETTING_LOOP_WORKERS} worker(s)")

SCHEDULER_DELETION_LOOP_INTERVAL = int(os.environ.get("SCHEDULER_DELETION_LOOP_INTERVAL", 1))
logger.info(f"Running deletion loop every {SCHEDULER_DELETION_LOOP_INTERVAL} second(s)")

SCHEDULER_DELETION_LOOP_WORKERS = int(os.environ.get("SCHEDULER_DELETION_LOOP_WORKERS", 1))
logger.info(f"Running deletion loop with {SCHEDULER_DELETION_LOOP_WORKERS} worker(s)")

SCHEDULER_RECOVERY_LOOP_INTERVAL = int(os.environ.get("SCHEDULER_RECOVERY_LOOP_INTERVAL", 60))
logger.info(f"Running recovery loop every {SCHEDULER_RECOVERY_LOOP_INTERVAL} second(s)")

SCHEDULER_RECOVERY_LOOP_WORKERS = int(os.environ.get("SCHEDULER_RECOVERY_LOOP_WORKERS", 1))
logger.info(f"Running recovery loop with {SCHEDULER_RECOVERY_LOOP_WORKERS} worker(s)")

scheduling_executor = ThreadPoolExecutor(
    max_workers=SCHEDULER_SCHEDULING_LOOP_WORKERS, thread_name_prefix="jobs_scheduling"
)
revert_scheduling_executor = ThreadPoolExecutor(
    max_workers=SCHEDULER_REVERT_SCHEDULING_LOOP_WORKERS, thread_name_prefix="jobs_revert_scheduling"
)
cancellation_executor = ThreadPoolExecutor(
    max_workers=SCHEDULER_CANCELLATION_LOOP_WORKERS, thread_name_prefix="jobs_cancellation"
)
resetting_executor = ThreadPoolExecutor(
    max_workers=SCHEDULER_RESETTING_LOOP_WORKERS, thread_name_prefix="jobs_resetting"
)
deletion_executor = ThreadPoolExecutor(max_workers=SCHEDULER_DELETION_LOOP_WORKERS, thread_name_prefix="jobs_deletion")
recovery_executor = ThreadPoolExecutor(max_workers=SCHEDULER_RECOVERY_LOOP_WORKERS, thread_name_prefix="jobs_recovery")

grpc_api_server_process = Process(target=JobUpdateService.serve)


def stop() -> None:
    """
    Stops the job scheduler (including recovery loop)
    """
    logger.info("Shutting down")
    ProgressHandler().stop()
    if ENABLE_TRACING:
        KafkaTelemetry.uninstrument()

    # Shutdown
    grpc_api_server_process.kill()
    grpc_api_server_process.join()
    grpc_api_server_process.close()

    scheduling_executor.shutdown(wait=False)
    revert_scheduling_executor.shutdown(wait=False)
    cancellation_executor.shutdown(wait=False)
    resetting_executor.shutdown(wait=False)
    deletion_executor.shutdown(wait=False)
    recovery_executor.shutdown(wait=False)


def start() -> None:
    """
    Starts the job scheduler (including recovery loop)
    """
    if ENABLE_TRACING:
        KafkaTelemetry.instrument()
    ProgressHandler()
    atexit.register(stop)

    grpc_api_server_process.start()

    for _ in range(SCHEDULER_SCHEDULING_LOOP_WORKERS):
        scheduling_executor.submit(start_scheduling_loop)
    for _ in range(SCHEDULER_REVERT_SCHEDULING_LOOP_WORKERS):
        revert_scheduling_executor.submit(start_revert_scheduling_loop)
    for _ in range(SCHEDULER_CANCELLATION_LOOP_WORKERS):
        cancellation_executor.submit(start_cancellation_loop)
    for _ in range(SCHEDULER_RESETTING_LOOP_WORKERS):
        resetting_executor.submit(start_resetting_loop)
    for _ in range(SCHEDULER_DELETION_LOOP_WORKERS):
        deletion_executor.submit(start_deletion_loop)
    for _ in range(SCHEDULER_RECOVERY_LOOP_WORKERS):
        recovery_executor.submit(start_recovery_loop)


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


def start_scheduling_loop() -> None:
    """
    Scheduling loop implementation
    """
    start_loop("scheduling-control-loop", run_scheduling_loop, SCHEDULER_SCHEDULING_LOOP_INTERVAL)


def start_revert_scheduling_loop() -> None:
    """
    Revert scheduling loop implementation
    """
    start_loop("revert-scheduling-control-loop", run_revert_scheduling_loop, SCHEDULER_REVERT_SCHEDULING_LOOP_INTERVAL)


def start_cancellation_loop() -> None:
    """
    Cancellation loop implementation
    """
    start_loop("cancellation-control-loop", run_cancellation_loop, SCHEDULER_CANCELLATION_LOOP_INTERVAL)


def start_deletion_loop() -> None:
    """
    Deletion loop implementation
    """
    start_loop("deletion-control-loop", run_deletion_loop, SCHEDULER_DELETION_LOOP_INTERVAL)


def start_recovery_loop() -> None:
    """
    Recovery loop implementation
    """
    start_loop("recovery-control-loop", run_recovery_loop, SCHEDULER_RECOVERY_LOOP_INTERVAL)


def start_resetting_loop() -> None:
    """
    Resetting loop implementation
    """
    start_loop("resetting-control-loop", run_resetting_loop, SCHEDULER_RESETTING_LOOP_INTERVAL)


if __name__ == "__main__":
    start()
