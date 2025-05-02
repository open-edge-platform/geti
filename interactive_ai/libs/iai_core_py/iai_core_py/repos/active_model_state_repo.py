# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
This module implements the repository for active model states
"""

from collections.abc import Callable
from functools import partial

from pymongo.command_cursor import CommandCursor
from pymongo.cursor import Cursor

from iai_core_py.entities.active_model_state import ActiveModelState, NullActiveModelState
from iai_core_py.repos.base import ProjectBasedSessionRepo
from iai_core_py.repos.mappers.cursor_iterator import CursorIterator
from iai_core_py.repos.mappers.mongodb_mappers.active_model_state_mapper import ActiveModelStateToMongo

from geti_types import ID, ProjectIdentifier, Session


class ActiveModelStateRepo(ProjectBasedSessionRepo[ActiveModelState]):
    """Repository to persist ActiveModelState entities in the database.

    :param project_identifier: Identifier of the project
    :param session: Session object; if not provided, it is loaded through the context variable CTX_SESSION_VAR
    """

    def __init__(self, project_identifier: ProjectIdentifier, session: Session | None = None) -> None:
        super().__init__(
            collection_name="active_model_state",
            session=session,
            project_identifier=project_identifier,
        )

    @property
    def forward_map(self) -> Callable[[ActiveModelState], dict]:
        return ActiveModelStateToMongo.forward

    @property
    def backward_map(self) -> Callable[[dict], ActiveModelState]:
        return partial(
            ActiveModelStateToMongo.backward,
            project_identifier=self.identifier,
        )

    @property
    def null_object(self) -> NullActiveModelState:
        return NullActiveModelState()

    @property
    def cursor_wrapper(self) -> Callable[[Cursor | CommandCursor], CursorIterator]:
        return lambda mongo_cursor: CursorIterator(
            cursor=mongo_cursor,
            mapper=ActiveModelStateToMongo,
            parameter=self.identifier,
        )

    def get_by_task_node_id(self, task_node_id: ID) -> ActiveModelState:
        """
        Fetch the active model state relative to the given task node.

        :param task_node_id: ID of the task node of the active model state
        :return: ActiveModelState, or NullActiveModelState if not found
        """
        return self.get_by_id(task_node_id)

    def delete_by_task_node_id(self, task_node_id: ID) -> None:
        """
        Delete the active model state relative to the given task node

        :param task_node_id: ID of the task node of the active model state
        """
        self.delete_by_id(task_node_id)
