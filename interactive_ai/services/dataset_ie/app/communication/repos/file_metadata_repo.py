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
"""
This module implements the import export metadata repo
"""

import logging
from collections.abc import Callable

from pymongo import DESCENDING, IndexModel
from pymongo.collection import Collection
from pymongo.command_cursor import CommandCursor
from pymongo.cursor import Cursor
from pymongo.errors import OperationFailure

from communication.mappers.file_metadata_mapper import TTL_FIELD_NAME, FileMetadataToMongo
from domain.entities.dataset_ie_file_metadata import FileMetadata, NullFileMetadata

from geti_types import Session
from sc_sdk.repos.base import SessionBasedRepo
from sc_sdk.repos.base.mongo_connector import MongoConnector
from sc_sdk.repos.mappers import CursorIterator

logger = logging.getLogger(__name__)

TTL_TIME_IN_SECONDS = 24 * 60 * 60


class FileMetadataRepo(SessionBasedRepo[FileMetadata]):
    """
    Repository to persist FileMetadata entities in the database.

    :param session: Session object; if not provided, it is loaded through get_session()
    """

    collection_name = "file_metadata"

    def __init__(self, session: Session | None = None) -> None:
        super().__init__(collection_name=self.collection_name, session=session)

    @property
    def _collection(self) -> Collection:
        try:
            return super()._collection
        except OperationFailure as e:
            # 85: IndexOptionsConflict
            if e.code == 85 and e.details is not None and TTL_FIELD_NAME in e.details["errmsg"]:
                collection = MongoConnector.get_collection(collection_name=self._collection_name)
                collection.drop_index([(TTL_FIELD_NAME, DESCENDING)])
                logger.warning(
                    f"The index `{TTL_FIELD_NAME}` is dropped due to `IndexOptionsConflict`"
                    f"(error message: {e.details['errmsg']})"
                )
                return super()._collection
            logger.exception(f"Error: `OperationFailure` occurs while getting a collection. (error: {str(e)})")
            raise e

    @property
    def forward_map(self) -> Callable[[FileMetadata], dict]:
        return FileMetadataToMongo.forward

    @property
    def backward_map(self) -> Callable[[dict], FileMetadata]:
        return FileMetadataToMongo.backward

    @property
    def null_object(self) -> NullFileMetadata:
        return NullFileMetadata()

    @property
    def cursor_wrapper(self) -> Callable[[Cursor | CommandCursor], CursorIterator]:
        return lambda mongo_cursor: CursorIterator(cursor=mongo_cursor, mapper=FileMetadataToMongo, parameter=None)

    @property
    def indexes(self) -> list[IndexModel]:
        indexes = super().indexes
        indexes.append(
            IndexModel([(TTL_FIELD_NAME, DESCENDING)], background=True, expireAfterSeconds=TTL_TIME_IN_SECONDS)
        )
        return indexes
