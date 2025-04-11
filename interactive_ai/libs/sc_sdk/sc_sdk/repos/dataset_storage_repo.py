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

"""Repository for dataset storage entities"""

from collections.abc import Callable

from pymongo.command_cursor import CommandCursor
from pymongo.cursor import Cursor

from sc_sdk.entities.dataset_storage import DatasetStorage, NullDatasetStorage
from sc_sdk.repos.base import ProjectBasedSessionRepo
from sc_sdk.repos.mappers.cursor_iterator import CursorIterator
from sc_sdk.repos.mappers.mongodb_mappers.dataset_storage_mapper import DatasetStorageToMongo

from geti_types import ProjectIdentifier, Session


class DatasetStorageRepo(ProjectBasedSessionRepo[DatasetStorage]):
    """
    Repository to persist DatasetStorage entities in the database.

    :param project_identifier: Identifier of the project
    :param session: Session object; if not provided, it is loaded through the context variable CTX_SESSION_VAR
    """

    def __init__(self, project_identifier: ProjectIdentifier, session: Session | None = None) -> None:
        super().__init__(
            collection_name="dataset_storage",
            session=session,
            project_identifier=project_identifier,
        )

    @property
    def forward_map(self) -> Callable[[DatasetStorage], dict]:
        return DatasetStorageToMongo.forward

    @property
    def backward_map(self) -> Callable[[dict], DatasetStorage]:
        return DatasetStorageToMongo.backward

    @property
    def null_object(self) -> NullDatasetStorage:
        return NullDatasetStorage()

    @property
    def cursor_wrapper(self) -> Callable[[Cursor | CommandCursor], CursorIterator]:
        return lambda mongo_cursor: CursorIterator(
            cursor=mongo_cursor,
            mapper=DatasetStorageToMongo,
            parameter=None,
        )
