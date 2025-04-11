# INTEL CONFIDENTIAL
#
# Copyright (C) 2025 Intel Corporation
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
"""This module defines helpers used to check limit constraints"""

import logging

from communication.constants import MAX_NUMBER_OF_PROJECTS_PER_ORGANIZATION
from communication.http_exceptions import MaxProjectsReachedException

from sc_sdk.repos import ProjectRepo

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
