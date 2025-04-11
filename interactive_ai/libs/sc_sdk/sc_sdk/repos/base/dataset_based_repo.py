# INTEL CONFIDENTIAL
#
# Copyright (C) 2023 Intel Corporation
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

"""Interface for per-dataset repos"""

import logging
from abc import ABCMeta
from uuid import UUID

from bson import ObjectId
from pymongo import ASCENDING, DESCENDING, IndexModel

from sc_sdk.entities.datasets import DatasetIdentifier
from sc_sdk.repos.base import PersistedEntityT, SessionBasedRepo
from sc_sdk.repos.base.constants import (
    DATASET_ID_FIELD_NAME,
    DATASET_STORAGE_ID_FIELD_NAME,
    ID_FIELD_NAME,
    ORGANIZATION_ID_FIELD_NAME,
    PROJECT_ID_FIELD_NAME,
    WORKSPACE_ID_FIELD_NAME,
)
from sc_sdk.repos.base.session_repo import QueryAccessMode
from sc_sdk.repos.mappers import IDToMongo

from geti_types import Session

logger = logging.getLogger(__name__)


class DatasetBasedSessionRepo(SessionBasedRepo[PersistedEntityT], metaclass=ABCMeta):
    """
    Interface for dataset-based session-based repos

    :param collection_name: Name of the database collection
    :param dataset_identifier: Identifier of the dataset
    :param session: Session object; if not provided, it is loaded through the context variable CTX_SESSION_VAR
    """

    def __init__(
        self,
        collection_name: str,
        dataset_identifier: DatasetIdentifier,
        session: Session | None = None,
    ) -> None:
        super().__init__(session=session, collection_name=collection_name)
        self.identifier = dataset_identifier
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
          - dataset_storage_id
          - dataset_id

        Derived classes may extend this filter provided that super() is called.
        """
        match_filter = super().preliminary_query_match_filter(access_mode=access_mode)
        match_filter[WORKSPACE_ID_FIELD_NAME] = IDToMongo.forward(self._session.workspace_id)
        match_filter[PROJECT_ID_FIELD_NAME] = IDToMongo.forward(self.identifier.project_id)
        match_filter[DATASET_STORAGE_ID_FIELD_NAME] = IDToMongo.forward(self.identifier.dataset_storage_id)
        match_filter[DATASET_ID_FIELD_NAME] = IDToMongo.forward(self.identifier.dataset_id)
        return match_filter

    @property
    def indexes(self) -> list[IndexModel]:
        return [
            IndexModel(
                [
                    (ORGANIZATION_ID_FIELD_NAME, DESCENDING),
                    (WORKSPACE_ID_FIELD_NAME, DESCENDING),
                    (PROJECT_ID_FIELD_NAME, DESCENDING),
                    (DATASET_STORAGE_ID_FIELD_NAME, DESCENDING),
                    (DATASET_ID_FIELD_NAME, DESCENDING),
                    (ID_FIELD_NAME, ASCENDING),
                ]
            )
        ]
