# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
This module implements the repository for project task node entities
"""

from collections.abc import Callable, Generator
from typing import Any

import pymongo
from pymongo import IndexModel
from pymongo.command_cursor import CommandCursor
from pymongo.cursor import Cursor

from iai_core_py.entities.task_node import NullTaskNode, TaskNode
from iai_core_py.repos.base import ProjectBasedSessionRepo
from iai_core_py.repos.mappers.cursor_iterator import CursorIterator
from iai_core_py.repos.mappers.mongodb_mappers.task_node_mapper import TaskNodeToMongo

from geti_types import ID, ProjectIdentifier, Session


class TaskNodeRepo(ProjectBasedSessionRepo[TaskNode]):
    """
    Repository to persist TaskNode entities in the database.

    :param project_identifier: Identifier of the project
    :param session: Session object; if not provided, it is loaded through the context variable CTX_SESSION_VAR
    """

    def __init__(
        self,
        project_identifier: ProjectIdentifier,
        session: Session | None = None,
    ) -> None:
        super().__init__(
            collection_name="task_node",
            session=session,
            project_identifier=project_identifier,
        )

    @property
    def indexes(self) -> list[IndexModel]:
        super_indexes = super().indexes
        new_indexes = [
            IndexModel(
                [
                    ("project_id", pymongo.ASCENDING),
                    ("is_trainable", pymongo.ASCENDING),
                ]
            ),
        ]
        return super_indexes + new_indexes

    @property
    def forward_map(self) -> Callable[[TaskNode], dict]:
        return TaskNodeToMongo.forward

    @property
    def backward_map(self) -> Callable[[dict], TaskNode]:
        return TaskNodeToMongo.backward

    @property
    def null_object(self) -> NullTaskNode:
        return NullTaskNode()

    @property
    def cursor_wrapper(self) -> Callable[[Cursor | CommandCursor], CursorIterator]:
        return lambda mongo_cursor: CursorIterator(cursor=mongo_cursor, mapper=TaskNodeToMongo, parameter=None)

    def get_trainable_task_ids(self) -> Generator[ID, None, None]:
        """
        Get all trainable task IDs.

        :return: Generator over the found IDs
        """
        result_task_filter: dict[str, Any] = {
            "is_trainable": True,
        }
        return self.get_all_ids(extra_filter=result_task_filter)

    def get_trainable_task_nodes(self) -> CursorIterator[TaskNode]:
        """
        Get all trainable tasks.

        :return: Iterator over the found tasks
        """
        result_task_filter: dict[str, Any] = {
            "is_trainable": True,
        }
        return self.get_all(extra_filter=result_task_filter)
