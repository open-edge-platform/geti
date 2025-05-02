# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""
This module implements the repository for CodeDeployment
"""

from collections.abc import Callable

from pymongo.command_cursor import CommandCursor
from pymongo.cursor import Cursor

from entities.deployment import CodeDeployment, NullCodeDeployment
from repos.code_deployment_mapper import CodeDeploymentToMongo

from geti_types import ProjectIdentifier, Session
from iai_core_py.repos.base.project_based_repo import ProjectBasedSessionRepo
from iai_core_py.repos.mappers.cursor_iterator import CursorIterator


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
