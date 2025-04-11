# INTEL CONFIDENTIAL
#
# Copyright (C) 2022 Intel Corporation
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
This module implements the repository for CodeDeployment
"""

from collections.abc import Callable

from pymongo.command_cursor import CommandCursor
from pymongo.cursor import Cursor

from entities.deployment import CodeDeployment, NullCodeDeployment
from repos.code_deployment_mapper import CodeDeploymentToMongo

from geti_types import ProjectIdentifier, Session
from sc_sdk.repos.base.project_based_repo import ProjectBasedSessionRepo
from sc_sdk.repos.mappers.cursor_iterator import CursorIterator


class CodeDeploymentRepo(ProjectBasedSessionRepo[CodeDeployment]):
    """
    Repository to persist CodeDeployment entities in the database.

    :param project_identifier: Identifier of the project
    :param session: Session object; if not provided, it is loaded through the context variable CTX_SESSION_VAR
    """

    def __init__(self, project_identifier: ProjectIdentifier, session: Session | None = None) -> None:
        super().__init__(
            collection_name="code_deployment",
            session=session,
            project_identifier=project_identifier,
        )

    @property
    def forward_map(self) -> Callable[[CodeDeployment], dict]:
        return CodeDeploymentToMongo.forward

    @property
    def backward_map(self) -> Callable[[dict], CodeDeployment]:
        return CodeDeploymentToMongo.backward

    @property
    def null_object(self) -> NullCodeDeployment:
        return NullCodeDeployment()

    @property
    def cursor_wrapper(self) -> Callable[[Cursor | CommandCursor], CursorIterator]:
        return lambda mongo_cursor: CursorIterator(cursor=mongo_cursor, mapper=CodeDeploymentToMongo, parameter=None)
