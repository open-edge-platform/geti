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

from model.job import Job
from scheduler.flyte import Flyte
from scheduler.state_machine import StateMachine

from geti_types import ID, RequestSource, make_session, session_context

logger = logging.getLogger(__name__)

BATCH_SIZE = int(os.environ.get("SCHEDULER_RECOVERY_BATCH_SIZE", 50))
logger.info(f"Recovery batch size is {BATCH_SIZE}")


def run_recovery_loop() -> None:
    """
    Runs the recovery loop iteration for the job scheduler
    """

    try:
        logger.debug("Running job scheduler recovery loop...")
        ids = StateMachine().get_session_ids_with_jobs_not_in_final_state()
        for organization_id, workspace_id in ids.items():
            check_and_recover_organization_if_needed(organization_id=organization_id, workspace_id=workspace_id)
    except Exception:
        logger.exception("Error occurred in a job scheduler recovery loop")


def check_and_recover_organization_if_needed(organization_id: ID, workspace_id: ID) -> None:
    """
    Checks all organization jobs and resets all the jobs missing in Flyte.
    :param organization_id: ID of organization to check
    :param workspace_id: ID of the workspace to check
    """
    logger.debug(f"Checking {organization_id} organization")
    with session_context(
        session=make_session(organization_id=organization_id, workspace_id=workspace_id, source=RequestSource.INTERNAL)
    ):
        active_jobs = list(StateMachine().get_scheduled_jobs_not_in_final_state())
        logger.debug(f"Found {len(active_jobs)} scheduled jobs not in final state")

        for i in range(0, len(active_jobs), BATCH_SIZE):
            batch = active_jobs[i : i + BATCH_SIZE]
            check_and_recover_organization_jobs_if_needed(jobs=batch)


def check_and_recover_organization_jobs_if_needed(jobs: list[Job]) -> None:
    """
    Checks workspace jobs and resets the jobs missing in Flyte.
    :param jobs: list of jobs to check
    """
    logger.debug(f"Processing jobs {[job.id for job in jobs]}")

    executions_ids = [job.executions.main.execution_id for job in jobs if job.executions.main.execution_id is not None]
    executions = Flyte().list_workflow_executions(execution_names=executions_ids)
    logger.debug(f"Found {len(executions)} workflow executions in Flyte")

    for job in jobs:
        execution_id = job.executions.main.execution_id
        execution = next(
            (ex for ex in executions if ex.id.name == execution_id),
            None,
        )
        if execution is not None:
            continue

        logger.warning(f"Found active job {job.id} with missing Flyte execution {execution_id}")
        StateMachine().reset_job_to_submitted_state(job_id=job.id)
