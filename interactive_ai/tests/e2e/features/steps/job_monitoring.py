# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging
import time
from typing import TYPE_CHECKING

from behave import step
from behave.runner import Context
from static_definitions import JobState, JobType

if TYPE_CHECKING:
    from geti_client import JobsApi


JOB_POLLING_PERIOD = 3  # seconds

logger = logging.getLogger(__name__)


@step("the user waits for {seconds:d} seconds")
def step_wait_seconds(context: Context, seconds: int) -> None:  # noqa: ARG001
    time.sleep(seconds)


@step("a job of type '{job_type:w}' is scheduled")
def step_then_job_scheduled(context: Context, job_type: str) -> None:
    """Asserts that the "job_type" is scheduled"""
    jobs_api: JobsApi = context.jobs_api
    expected_job_type = JobType(job_type)

    context.job_info = jobs_api.get_job(
        organization_id=context.organization_id,
        workspace_id=context.workspace_id,
        job_id=context.job_id,
    )

    found_job_type = JobType(context.job_info.actual_instance.type)
    assert found_job_type == expected_job_type, f"Expected job type {expected_job_type}, but found {found_job_type}"


@step("a job of type '{job_type:w}' is running")
def step_then_job_running(context: Context, job_type: str) -> None:
    """Asserts that the "job_type" is running"""
    jobs_api: JobsApi = context.jobs_api
    expected_job_type = JobType(job_type)

    for _ in range(20):
        context.job_info = jobs_api.get_job(
            organization_id=context.organization_id,
            workspace_id=context.workspace_id,
            job_id=context.job_id,
        )
        if context.job_info.actual_instance.state == JobState.RUNNING:
            break
        time.sleep(1)
    else:
        raise RuntimeError(f"A job of type '{job_type}' is not running within 20 seconds")

    found_job_type = JobType(context.job_info.actual_instance.type)
    assert found_job_type == expected_job_type, f"Expected job type {expected_job_type}, but found {found_job_type}"


@step("the user cancels the job")
def step_when_user_cancels_job(context: Context) -> None:
    """Cancels the job"""
    jobs_api: JobsApi = context.jobs_api
    jobs_api.cancel_job(
        organization_id=context.organization_id,
        workspace_id=context.workspace_id,
        job_id=context.job_id,
    )


@step("the job completes successfully within {job_timeout:d} minutes")
def step_then_job_finishes_before_timeout(context: Context, job_timeout: int) -> None:
    """
    Asserts that the jobs finishes within the passed "job_timeout". If not, raises a TimeoutError.
    """
    jobs_api: JobsApi = context.jobs_api
    max_polling_attempts = job_timeout * 60 // JOB_POLLING_PERIOD

    # Poll the job status until it is finished, or the timeout is reached
    for attempt in range(max_polling_attempts):
        logger.debug(
            f"Waiting for job `{context.job_id}` to finish... "
            f"(attempt {attempt + 1}/{max_polling_attempts}, {attempt * JOB_POLLING_PERIOD}s elapsed)"
        )
        context.job_info = jobs_api.get_job(
            organization_id=context.organization_id,
            workspace_id=context.workspace_id,
            job_id=context.job_id,
        )

        if context.job_info.actual_instance.state == JobState.FINISHED:
            logger.debug(f"Job `{context.job_id}` finished successfully")
            break
        if context.job_info.actual_instance.state == JobState.FAILED:
            raise AssertionError(f"Job `{context.job_id}` failed: {context.job_info.actual_instance.steps[-1].message}")
        if context.job_info.actual_instance.state == JobState.CANCELLED:
            raise AssertionError(f"Job `{context.job_id}` was unexpectedly cancelled")

        time.sleep(JOB_POLLING_PERIOD)
    else:
        logger.warning(
            f"Job `{context.job_id}` is still '{context.job_info.actual_instance.state}' "
            f"after {job_timeout} minutes; trying to cancel it"
        )
        try:
            jobs_api.cancel_job(
                organization_id=context.organization_id,
                workspace_id=context.workspace_id,
                job_id=context.job_id,
            )
        except Exception as e:
            logger.warning(f"Failed to cancel job `{context.job_id}`: {e}")
        raise TimeoutError(f"Job `{context.job_id}` did not finish within {job_timeout} minutes")
