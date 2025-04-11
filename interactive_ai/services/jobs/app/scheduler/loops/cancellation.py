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

import logging
import os

from flyteidl.core.execution_pb2 import WorkflowExecution

from model.job_state import JobState
from scheduler.flyte import Flyte
from scheduler.state_machine import StateMachine

from geti_telemetry_tools import unified_tracing
from geti_types import ID, session_context

logger = logging.getLogger(__name__)

MAX_CANCEL_RETRY_COUNT = int(os.environ.get("MAX_CANCEL_RETRY_COUNT", 5))
logger.info(f"Max canceling retries number is {MAX_CANCEL_RETRY_COUNT}")


def run_cancellation_loop() -> None:
    """
    Runs the cancellation loop iteration for the job scheduler

    Performs required canceling.

    Following steps are performed:
    1. Pick one by one all cancelled SCHEDULED or RUNNING job for canceling, move it to CANCELING state.
    Perform canceling in Flyte if such job was found

    2. Pick one by one all jobs in SUBMITTED state which has been marked as cancelled are move directly to CANCELLED
    state. SUBMITTED state means that no scheduling logic has been applied so no Flyte interaction is needed.
    """

    try:
        while True:
            job = StateMachine().find_and_lock_job_for_canceling()
            if job is None:
                break

            with session_context(session=job.session):
                cancel_main_job(job_id=job.id)

        while True:
            job = StateMachine().get_cancelled_job(job_states=(JobState.SUBMITTED, JobState.READY_FOR_SCHEDULING))
            if job is None:
                break

            with session_context(session=job.session):
                StateMachine().set_and_publish_cancelled_state(job_id=job.id)

    except Exception:
        logger.exception("Error occurred in a job scheduler cancellation loop")


def cancel_main_job(job_id: ID) -> None:
    """
    Cancels a job execution.

    If this is not the first attempt to cancel this job and number of retries exceeded allowed maximum, drops cancelled
    flag and transfers the job back to RUNNING state.
    If this is not the first attempt to cancel this job and the maximum number of retries has not been reached,
    attempt to obtain Flyte execution.
    If execution is found, checks its state. If it's not ABORTED, cancels execution in Flyte.
    Updates the job and sets CANCELLED state.
    If Flyte execution stop fails, sets either RUNNING or CANCELLED state.
    :param job_id: Job ID
    """
    logger.info(f"Job to be cancelled: {job_id}")
    job = StateMachine().get_by_id(job_id=job_id)

    if job is None:
        logger.error(f"Unable to find job {job_id}")
        return

    cancel_retry_counter = job.executions.main.cancel_retry_counter

    # If the number of retries exceeded maximum, set either RUNNING or SCHEDULED state back
    if cancel_retry_counter is not None and cancel_retry_counter > MAX_CANCEL_RETRY_COUNT:
        logger.warning(f"Job {job_id} failed to cancel {cancel_retry_counter} time(s), considering it as running")
        StateMachine().drop_cancelled_flag(job_id=job_id)
        return

    try:
        if job.executions.main.execution_id is None:
            raise Exception(f"Main execution ID is not persisted for job {job_id}")

        cancel_execution(execution_name=job.executions.main.execution_id)

        # Update job in database
        StateMachine().set_ready_for_revert_state(job_id=job_id)
    except Exception:
        logger.exception(f"Failed to cancel Flyte execution for job {job_id}")
        StateMachine().reset_canceling_job(job_id=job_id)


@unified_tracing
def cancel_execution(execution_name: str) -> None:
    """
    Cancels job execution

    :param execution_name: Execution name
    """
    execution = Flyte().fetch_workflow_execution(execution_name=execution_name)
    if execution is None:
        logger.warning(f"Execution {execution_name} cannot be found in Flyte, marking job as cancelled")
        return

    if execution.closure.phase in (WorkflowExecution.ABORTED, WorkflowExecution.ABORTING):
        logger.info(f"Flyte job execution with name {execution_name} is being or already aborted")
        return

    if execution.is_done or execution.closure.phase == WorkflowExecution.FAILING:
        logger.info(f"Flyte job execution with name {execution_name} is being or already terminated.")
        return

    logger.info(f"Canceling a job execution with name {execution_name} in Flyte")
    Flyte().cancel_workflow_execution(execution=execution)
    logger.info(f"Job execution cancelled in Flyte: {execution.id.name}")
