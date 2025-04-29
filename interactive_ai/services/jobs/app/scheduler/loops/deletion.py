# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging

from scheduler.state_machine import StateMachine

from geti_types import session_context

logger = logging.getLogger(__name__)


def run_deletion_loop() -> None:
    """
    Runs the deletion loop iteration for the job scheduler

    Delete jobs in following cases:
        1. Job is finished and marked for deleting afterwards
        2. Job is failed and marked for deleting afterwards
        3. Job is cancelled, put in CANCELLED state and marked for deleting
    """

    try:
        logger.debug("Running job scheduler deletion loop iteration...")
        while True:
            job = StateMachine().get_job_to_delete()
            if job is None:
                break

            with session_context(session=job.session):
                StateMachine().delete_job(job_id=job.id)

    except Exception:
        logger.exception("Error occurred in a job scheduler deletion loop")
