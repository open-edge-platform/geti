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

from flytekit.remote import FlyteWorkflow, FlyteWorkflowExecution

from model.job import Job
from scheduler.flyte import ExecutionType, Flyte
from scheduler.state_machine import StateMachine
from scheduler.utils import get_revert_execution_name, resolve_revert_job

from geti_telemetry_tools import unified_tracing
from geti_types import ID, session_context

logger = logging.getLogger(__name__)

MAX_START_RETRY_COUNT = int(os.environ.get("MAX_START_RETRY_COUNT", 5))
logger.info(f"Max start retries number is {MAX_START_RETRY_COUNT}")


def run_revert_scheduling_loop() -> None:
    """
    Runs the revert scheduling loop iteration for the job scheduler
    """

    try:
        while True:
            logger.debug("Running job scheduler revert scheduling loop iteration...")
            job = StateMachine().find_and_lock_job_for_reverting()
            if job is None:
                break

            with session_context(session=job.session):
                schedule_revert_job(job_id=job.id)
    except Exception:
        logger.exception("Error occurred in a job scheduler revert scheduling loop")


def schedule_revert_job(job_id: ID) -> None:
    """
    Schedules a revert job execution.

    If this is not the first attempt to schedule this job and number of retries exceeded allowed maximum, transfers
    the job either to FAILED state or to CANCELLED state depending ob cancelled flag.
    If this is not the first attempt to schedule this job and the maximum number of retries has not been reached,
    attempt to obtain Flyte execution.
    If execution is found, uses it. Otherwise starts execution in Flyte.
    Updates the job and sets SCHEDULED state.
    If Flyte execution start fails, sets READY_FOR_REVERT state.
    :param job_id: Job ID
    """
    logger.info(f"Job a revert execution to be scheduled for: {job_id}")
    job = StateMachine().get_by_id(job_id=job_id)

    if job is None:
        logger.error(f"Unable to find job {job_id}")
        return

    start_retry_counter = job.executions.revert.start_retry_counter if job.executions.revert is not None else None

    def set_final_state():
        if job.cancellation_info.is_cancelled:
            StateMachine().set_and_publish_cancelled_state(job_id=job_id)
        else:
            StateMachine().set_and_publish_failed_state(job_id=job_id)

    # If the number of retries exceeded maximum, set FAILED state
    if start_retry_counter is not None and start_retry_counter > MAX_START_RETRY_COUNT:
        logger.critical(f"Job {job_id} revert execution failed to start {start_retry_counter} time(s)")
        set_final_state()
        return

    try:
        execution = start_revert_execution(job=job)
        if execution is None:
            set_final_state()
            return

        # Update job in database
        StateMachine().set_revert_scheduled_state(
            job_id=job_id,
            flyte_execution_id=execution.id.name,
        )
    except Exception:
        logger.exception(f"Failed to schedule Flyte revert execution for job {job_id}")
        StateMachine().reset_revert_scheduling_job(job_id=job_id)


@unified_tracing
def start_revert_execution(job: Job) -> FlyteWorkflowExecution | None:
    """
    Starts jobs revert execution

    :param job: Job to start revert execution for
    :return: FlyteWorkflowExecution Flyte workflow execution object
    """
    execution_name = get_revert_execution_name(job_id=job.id)

    # Resolving Flyte workflow name and version
    resolved_revert_job = resolve_revert_job(job_type=job.type)
    if resolved_revert_job is None:
        return None

    workflow_name, workflow_version = resolved_revert_job
    logger.debug(f"Trying to lookup for {workflow_name}:{workflow_version} revert workflow")
    workflow = Flyte().fetch_workflow(workflow_name=workflow_name, workflow_version=workflow_version)
    if workflow is None:
        logger.debug(f"Workflow {workflow_name}:{workflow_version} is not found")
        return None

    logger.debug(
        f"Workflow {workflow_name}:{workflow_version} is found, launching it with execution name {execution_name}"
    )
    return start_execution(
        job=job,
        workflow=workflow,
        execution_type=ExecutionType.REVERT,
        execution_name=execution_name,
        payload={},
    )


@unified_tracing
def start_execution(
    job: Job,
    workflow: FlyteWorkflow,
    execution_type: ExecutionType,
    execution_name: str,
    payload: dict,
) -> FlyteWorkflowExecution:
    """
    Starts job related execution

    :param job: Job to start execution for
    :param workflow: Job workflow
    :param execution_type: Execution type: MAIN or REVERT
    :param execution_name: Execution name
    :return: FlyteWorkflowExecution Flyte workflow execution object
    """
    # Let's check maybe it's already running
    execution = Flyte().fetch_workflow_execution(execution_name=execution_name)

    if execution is not None:
        logger.info(f"Reusing already running job execution in Flyte: {execution.id.name}")
        return execution

    # If no running execution exists, need to launch it
    project_id = str(job.project_id) if job.project_id is not None else None
    logger.info(
        f"Scheduling a job execution with name {execution_name} in Flyte: "
        f"workspace_id={job.workspace_id}, project_id={project_id}, "
        f"workflow={workflow.id}, payload={job.payload}"
    )

    execution = Flyte().start_workflow_execution(
        workspace_id=job.workspace_id,
        job=job,
        project_id=project_id,
        execution_type=execution_type,
        execution_name=execution_name,
        workflow=workflow,
        payload=payload,
        telemetry=job.telemetry,
        session=job.session,
    )
    logger.info(f"Job execution scheduled in Flyte: {execution.id.name}")
    return execution
