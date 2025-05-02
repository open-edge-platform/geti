# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
This module implements the repository for project based metrics
"""

import logging
from collections.abc import Callable
from typing import Any

from pymongo.command_cursor import CommandCursor
from pymongo.cursor import Cursor

from iai_core_py.entities.project import NullProject, Project
from iai_core_py.repos import ProjectRepo
from iai_core_py.repos.base.read_only_repo import ReadOnlyRepo
from iai_core_py.repos.mappers.cursor_iterator import CursorIterator

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
