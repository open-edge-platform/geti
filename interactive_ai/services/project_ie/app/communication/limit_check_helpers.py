# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""This module defines helpers used to check limit constraints"""

import logging

from communication.constants import MAX_NUMBER_OF_PROJECTS_PER_ORGANIZATION
from communication.http_exceptions import MaxProjectsReachedException

from iai_core.repos import ProjectRepo

logger = logging.getLogger(__name__)


def check_max_number_of_projects(include_hidden: bool = False) -> None:
    """
    Check if the number of projects in the workspace exceeds the maximum allowed

    TODO CVS-130681 - handle project counting across multiple workspaces
    :param include_hidden: Whether to include hidden (not fully created or deleted) projects
    :raises: MaxProjectsReachedException if the maximum number of projects has been hit
    """
    if (
        MAX_NUMBER_OF_PROJECTS_PER_ORGANIZATION
        and ProjectRepo().count_all(include_hidden=include_hidden) >= MAX_NUMBER_OF_PROJECTS_PER_ORGANIZATION
    ):
        raise MaxProjectsReachedException(maximum=MAX_NUMBER_OF_PROJECTS_PER_ORGANIZATION)
