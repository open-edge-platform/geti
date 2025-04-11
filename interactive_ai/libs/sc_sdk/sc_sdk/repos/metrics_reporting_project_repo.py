# INTEL CONFIDENTIAL
#
# Copyright (C) 2024 Intel Corporation
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

"""
This module implements the repository for project based metrics
"""

import logging
from collections.abc import Callable
from typing import Any

from pymongo.command_cursor import CommandCursor
from pymongo.cursor import Cursor

from sc_sdk.entities.project import NullProject, Project
from sc_sdk.repos import ProjectRepo
from sc_sdk.repos.base.read_only_repo import ReadOnlyRepo
from sc_sdk.repos.mappers.cursor_iterator import CursorIterator

logger = logging.getLogger(__name__)


class MetricsReportingProjectRepo(ReadOnlyRepo[Project]):
    """
    Repository to report metrics based on the project repo.
    """

    collection_name = ProjectRepo.collection_name

    def __init__(self) -> None:
        super().__init__(collection_name=MetricsReportingProjectRepo.collection_name)

    @property
    def backward_map(self) -> Callable[[dict], Project]:
        raise NotImplementedError

    @property
    def null_object(self) -> Project:
        return NullProject()

    @property
    def cursor_wrapper(self) -> Callable[[Cursor | CommandCursor], CursorIterator]:
        raise NotImplementedError

    def get_total_number_of_projects_per_project_type(self) -> dict[str, int]:
        pipeline: list[dict[str, Any]] = [
            {
                "$match": {
                    "hidden": False,
                },
            },
            {
                "$group": {
                    "_id": "$project_type",
                    "total_number_of_projects": {
                        "$count": {},
                    },
                },
            },
        ]
        docs = self.aggregate_read(pipeline=pipeline)
        return {doc["_id"]: doc["total_number_of_projects"] for doc in docs}
