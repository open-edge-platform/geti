# INTEL CONFIDENTIAL
#
# Copyright (C) 2021 Intel Corporation
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
This module implements the repository for active model states
"""

from collections.abc import Callable
from functools import partial

from pymongo.command_cursor import CommandCursor
from pymongo.cursor import Cursor

from sc_sdk.entities.active_model_state import ActiveModelState, NullActiveModelState
from sc_sdk.repos.base import ProjectBasedSessionRepo
from sc_sdk.repos.mappers.cursor_iterator import CursorIterator
from sc_sdk.repos.mappers.mongodb_mappers.active_model_state_mapper import ActiveModelStateToMongo

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
