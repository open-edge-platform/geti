# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module contains Project-related utility functions for job creation"""

import logging
import os

from geti_types import ID
from iai_core.repos import ProjectRepo

PROJECT_LOCK_TIME = int(os.environ.get("PROJECT_LOCK_TIME", 8 * 60 * 60))
logger = logging.getLogger(__name__)


def lock_project(job_type: str, project_id: ID) -> None:
    """
    Locks the project to prevent data modification that could disrupt the job's execution.

    :param job_type: The job type
    :param project_id: ID of the project to lock
    """
    try:
        ProjectRepo().mark_locked(owner=job_type, project_id=project_id, duration_seconds=PROJECT_LOCK_TIME)
    except ValueError:
        logger.debug(
            "Project with ID '%s' is already locked for '%s' job. Cannot decrease the lock time.",
            project_id,
            job_type,
        )
        return
    logger.debug(
        "Project with ID '%s' has been marked as locked for '%s' job for %s seconds.",
        project_id,
        job_type,
        PROJECT_LOCK_TIME,
    )
