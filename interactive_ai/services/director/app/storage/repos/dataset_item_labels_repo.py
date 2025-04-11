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
This module implements the repository for the DatasetItemLabels
"""

from collections.abc import Callable

from pymongo.command_cursor import CommandCursor
from pymongo.cursor import Cursor

from entities.dataset_item_labels import DatasetItemLabels, NullDatasetItemLabels
from storage.mappers import DatasetItemLabelsToMongo

from geti_types import DatasetStorageIdentifier, Session
from sc_sdk.repos.base.dataset_storage_based_repo import DatasetStorageBasedSessionRepo
from sc_sdk.repos.mappers import CursorIterator


class DatasetItemLabelsRepo(DatasetStorageBasedSessionRepo[DatasetItemLabels]):
    """
    This repository is responsible for making
    :class:`DatasetItemLabels` entities persistent in a database.

    ID of DatasetItemLabels entities must be the same ID of the dataset item they refer to.
    This ensures that two documents with different dataset item ID can never exist together
    the collection, since the second insertion would raise an exception.

    :param dataset_storage_identifier: Identifier of the dataset storage
    :param session: Session object; if not provided, it is loaded through the context variable CTX_SESSION_VAR
    """

    collection_name = "dataset_item_labels"

    def __init__(
        self,
        dataset_storage_identifier: DatasetStorageIdentifier,
        session: Session | None = None,
    ) -> None:
        super().__init__(
            collection_name=DatasetItemLabelsRepo.collection_name,
            dataset_storage_identifier=dataset_storage_identifier,
            session=session,
        )

    @property
    def null_object(self) -> NullDatasetItemLabels:
        return NullDatasetItemLabels()

    @property
    def forward_map(self) -> Callable[[DatasetItemLabels], dict]:
        return DatasetItemLabelsToMongo.forward

    @property
    def backward_map(self) -> Callable[[dict], DatasetItemLabels]:
        return DatasetItemLabelsToMongo.backward

    @property
    def cursor_wrapper(self) -> Callable[[Cursor | CommandCursor], CursorIterator]:
        return lambda mongo_cursor: CursorIterator(cursor=mongo_cursor, mapper=DatasetItemLabelsToMongo, parameter=None)
