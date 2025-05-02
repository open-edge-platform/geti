# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""Interfaces for per-project repos"""

import logging
from abc import ABCMeta
from uuid import UUID

from bson import ObjectId
from pymongo import ASCENDING, DESCENDING, IndexModel

from iai_core_py.repos.mappers.mongodb_mappers.id_mapper import IDToMongo

from .constants import ID_FIELD_NAME, ORGANIZATION_ID_FIELD_NAME, PROJECT_ID_FIELD_NAME, WORKSPACE_ID_FIELD_NAME
from .session_repo import PersistedEntityT, QueryAccessMode, SessionBasedRepo
from geti_types import ProjectIdentifier, Session

logger = logging.getLogger(__name__)


class ProjectBasedSessionRepo(SessionBasedRepo[PersistedEntityT], metaclass=ABCMeta):
    """
    Interface for project-based session-based repos.

    Project-based means that all the stored objects belong to a project
    (not necessarily the same); all queries must filter by project before applying
    any other filter or transformation, to avoid mixing data of different projects.

    :param collection_name: Name of the database collection
    :param project_identifier: Identifier of the project
    :param session: Session object; if not provided, it is loaded through the context variable CTX_SESSION_VAR
    """

    def __init__(
        self,
        collection_name: str,
        project_identifier: ProjectIdentifier,
        session: Session | None = None,
    ) -> None:
        super().__init__(session=session, collection_name=collection_name)
        self.identifier = project_identifier
        if self.identifier.workspace_id != self._session.workspace_id:
            logger.error(
                f"During initialization of {self.__class__.__name__}, the 'workspace_id' in the identifier "
                f"({self.identifier.workspace_id}) does not match the 'workspace_id' in the Session "
                f"({self._session.workspace_id}); this could indicate a bug in the session initialization/propagation. "
                f"Session: {self._session}."
            )

    def preliminary_query_match_filter(self, access_mode: QueryAccessMode) -> dict[str, str | ObjectId | UUID | dict]:
        """
        Filter that must be applied at the beginning of every MongoDB query based on
        find(), update(), insert(), delete(), count() or similar methods.

        The filter ensures that:
          - only data of a specific organization is selected and processed
          - the query runs with the right scope in the sharded cluster

        The filter matches:
          - organization_id
          - location (optional, depends on access mode and session info)
          - workspace_id
          - project_id

        Derived classes may extend this filter provided that super() is called.
        """
        match_filter = super().preliminary_query_match_filter(access_mode=access_mode)
        match_filter[WORKSPACE_ID_FIELD_NAME] = IDToMongo.forward(self._session.workspace_id)
        match_filter[PROJECT_ID_FIELD_NAME] = IDToMongo.forward(self.identifier.project_id)
        return match_filter

    @property
    def indexes(self) -> list[IndexModel]:
        return [
            IndexModel(
                [
                    (ORGANIZATION_ID_FIELD_NAME, DESCENDING),
                    (WORKSPACE_ID_FIELD_NAME, DESCENDING),
                    (PROJECT_ID_FIELD_NAME, DESCENDING),
                    (ID_FIELD_NAME, ASCENDING),
                ]
            )
        ]
