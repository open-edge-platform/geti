# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging
import os

from flytekit.remote import FlyteWorkflow, FlyteWorkflowExecution

from model.job import Job, JobStepDetails, JobTaskExecutionBranch
from model.job_state import JobTaskState
from scheduler.flyte import ExecutionType, Flyte
from scheduler.jobs_templates import JobsTemplates
from scheduler.state_machine import StateMachine
from scheduler.utils import get_main_execution_name, resolve_main_job

from geti_telemetry_tools import unified_tracing
from geti_types import ID, session_context

logger = logging.getLogger(__name__)

MAX_START_RETRY_COUNT = int(os.environ.get("MAX_START_RETRY_COUNT", 5))
logger.info(f"Max start retries number is {MAX_START_RETRY_COUNT}")


class FlyteWorkflowNotFound(Exception):
    """
    Exception to indicate that a Flyte workflow is not found and therefore cannot be started
    """


def run_scheduling_loop() -> None:
    """
    Runs the scheduling loop iteration for the job scheduler
    """

    try:
        logger.debug("Running job scheduler scheduling loop iteration...")
        while True:
            job = StateMachine().find_and_lock_job_for_scheduling()
            if job is None:
                break

            with session_context(session=job.session):
                schedule_main_job(job_id=job.id)
    except Exception:
        logger.exception("Error occurred in a job scheduler scheduling loop")


def schedule_main_job(job_id: ID) -> None:
    """
    Schedules a main job execution.

    If this is not the first attempt to schedule this job and number of retries exceeded allowed maximum, transfers
    the job to FAILED state.
    If this is not the first attempt to schedule this job and the maximum number of retries has not been reached,
    attempt to obtain Flyte execution.
    If execution is found, uses it. Otherwise starts execution in Flyte.
    Updates the job and sets SCHEDULED state.
    If Flyte execution start fails, sets READY_FOR_SCHEDULING state.
    :param job_id: Job ID
    """
    logger.info(f"Job to be scheduled: {job_id}")
    job = StateMachine().get_by_id(job_id=job_id)
    if job is None:
        logger.error(f"Unable to find job {job_id}")
        return

    start_retry_counter = job.executions.main.start_retry_counter

    # If the number of retries exceeded maximum, set FAILED state
    if start_retry_counter is not None and start_retry_counter > MAX_START_RETRY_COUNT:
        logger.warning(f"Job {job_id} main execution failed to start {start_retry_counter} time(s)")
        StateMachine().set_and_publish_failed_state(job_id=job_id)
        return

    try:
        workflow, execution = start_main_execution(job=job)
        job_steps = JobsTemplates().get_job_steps(job_type=job.type)

        step_details = [
            JobStepDetails(
                index=index + 1,
                task_id=job_step.task_id,
                step_name=job_step.name,
                state=JobTaskState.WAITING,
                branches=(
                    tuple(
                        JobTaskExecutionBranch(
                            condition=branch.condition,
                            branch=branch.branch,
                        )
                        for branch in job_step.branches
                    )
                    if job_step.branches is not None and len(job_step.branches) > 0
                    else None
                ),
                progress=-1,
            )
            for index, job_step in enumerate(job_steps)
        ]

        # Update job in database
        StateMachine().set_scheduled_state(
            job_id=job_id,
            flyte_launch_plan_id=execution.spec.launch_plan.name,
            flyte_execution_id=execution.id.name,
            step_details=step_details,
        )
    except Exception:
        logger.exception(f"Failed to schedule Flyte execution for job {job_id}")
        StateMachine().reset_scheduling_job(job_id=job_id)


@unified_tracing
def start_main_execution(job: Job) -> tuple[FlyteWorkflow, FlyteWorkflowExecution]:
    """
    Starts jobs main execution

    :param job: Job to start main execution for
    :return: FlyteWorkflow, FlyteWorkflowExecution Tuple of Flyte workflow and  Flyte workflow execution object
    """
    execution_name = get_main_execution_name(job_id=job.id)

    # Resolving Flyte workflow name and version
    workflow_name, workflow_version = resolve_main_job(job_type=job.type)

    logger.debug(f"Trying to lookup for {workflow_name}:{workflow_version} workflow")
    workflow = Flyte().fetch_workflow(workflow_name=workflow_name, workflow_version=workflow_version)
    if workflow is None:
        logger.debug(f"Workflow {workflow_name}:{workflow_version} is not found")
        raise FlyteWorkflowNotFound(f"Workflow {workflow_name}:{workflow_version} is not found")

    logger.debug(
        f"Workflow {workflow_name}:{workflow_version} is found, launching it with execution name {execution_name}"
    )
    return (
        workflow,
        start_execution(
            job=job,
            workflow=workflow,
            execution_type=ExecutionType.MAIN,
            execution_name=execution_name,
            payload=job.payload,
        ),
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
