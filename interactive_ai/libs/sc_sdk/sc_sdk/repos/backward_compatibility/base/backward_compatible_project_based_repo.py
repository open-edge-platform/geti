# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import abc
import logging
from uuid import UUID

from bson import ObjectId
from pymongo import DESCENDING, IndexModel

from sc_sdk.repos.backward_compatibility.base.backward_compatible_session_repo import BackwardCompatibilitySessionRepo
from sc_sdk.repos.base.constants import PROJECT_ID_FIELD_NAME, WORKSPACE_ID_FIELD_NAME
from sc_sdk.repos.base.session_repo import PersistedEntityT, QueryAccessMode
from sc_sdk.repos.mappers import IDToMongo

from geti_types import ProjectIdentifier, Session

logger = logging.getLogger(__name__)


class BackwardCompatibilityProjectBasedRepo(BackwardCompatibilitySessionRepo[PersistedEntityT], metaclass=abc.ABCMeta):
    """
    Interface for a backward-compatible project-based session-based repo class.
    For more information, see :class:`BackwardCompatibilitySessionRepo` and :class:`ProjectBasedSessionRepo`.

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
        super_indexes = super().indexes
        new_indexes = [IndexModel([(PROJECT_ID_FIELD_NAME, DESCENDING)])]
        return super_indexes + new_indexes
