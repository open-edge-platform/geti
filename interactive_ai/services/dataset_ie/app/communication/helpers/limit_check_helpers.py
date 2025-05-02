# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""This module defines helpers used to check limit constraints"""

from communication.constants import MAX_NUMBER_OF_LABELS, MAX_NUMBER_OF_PROJECTS_PER_ORGANIZATION
from communication.helpers.http_exceptions import MaxLabelsReachedGetiBaseException, MaxProjectsReachedGetiBaseException

from iai_core_py.repos import ProjectRepo


def check_max_number_of_projects(include_hidden: bool = False) -> None:
    """
    Check if the number of projects in the workspace exceeds the maximum allowed

    TODO CVS-130681 - handle project counting across multiple workspaces
    :param include_hidden: Whether to include hidden (not fully created or deleted) projects
    :raises: MaxProjectsReachedGetiBaseException if the maximum number of projects has been hit
    """
    if (
        MAX_NUMBER_OF_PROJECTS_PER_ORGANIZATION
        and ProjectRepo().count_all(include_hidden=include_hidden) >= MAX_NUMBER_OF_PROJECTS_PER_ORGANIZATION
    ):
        raise MaxProjectsReachedGetiBaseException(maximum=MAX_NUMBER_OF_PROJECTS_PER_ORGANIZATION)


def check_max_number_of_labels(labels: list) -> None:
    """
    Check if the number of labels exceeds the maximum allowed

    :param labels: The labels to check
    :raises: MaxLabelsReachedGetiBaseException if the maximum number of projects has been hit
    """
    if len(labels) > MAX_NUMBER_OF_LABELS:
        raise MaxLabelsReachedGetiBaseException(maximum=MAX_NUMBER_OF_LABELS)
