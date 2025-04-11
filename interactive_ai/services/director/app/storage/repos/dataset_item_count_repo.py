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
This module implements the repository for the DatasetItemCount
"""

from collections.abc import Callable
from typing import Any

from pymongo.command_cursor import CommandCursor
from pymongo.cursor import Cursor

from entities.dataset_item_count import (
    DatasetItemCount,
    DeletedDatasetItemCountData,
    NewDatasetItemCountData,
    NullDatasetItemCount,
)
from storage.mappers import DatasetItemCountToMongo

from geti_types import ID, DatasetStorageIdentifier, Session
from sc_sdk.repos.base.dataset_storage_based_repo import DatasetStorageBasedSessionRepo
from sc_sdk.repos.base.session_repo import QueryAccessMode
from sc_sdk.repos.mappers import IDToMongo
from sc_sdk.repos.mappers.cursor_iterator import CursorIterator


class DatasetItemCountRepo(DatasetStorageBasedSessionRepo[DatasetItemCount]):
    """
    This repository is responsible for making
    :class:`DatasetItemCount` entities persistent in a database.

    :param dataset_storage_identifier: Identifier of the dataset storage
    :param session: Session object; if not provided, it is loaded through the context variable CTX_SESSION_VAR
    """

    def __init__(
        self,
        dataset_storage_identifier: DatasetStorageIdentifier,
        session: Session | None = None,
    ) -> None:
        super().__init__(
            collection_name="dataset_item_count",
            dataset_storage_identifier=dataset_storage_identifier,
            session=session,
        )

    @property
    def null_object(self) -> NullDatasetItemCount:
        return NullDatasetItemCount()

    @property
    def forward_map(self) -> Callable[[DatasetItemCount], dict]:
        return DatasetItemCountToMongo.forward

    @property
    def backward_map(self) -> Callable[[dict], DatasetItemCount]:
        return DatasetItemCountToMongo.backward

    @property
    def cursor_wrapper(self) -> Callable[[Cursor | CommandCursor], CursorIterator]:
        return lambda mongo_cursor: CursorIterator(cursor=mongo_cursor, mapper=DatasetItemCountToMongo, parameter=None)

    def update_count_data(
        self,
        id_: ID,
        new_dataset_item_count_data: NewDatasetItemCountData,
        deleted_dataset_item_count_data: DeletedDatasetItemCountData,
        assigned_dataset_items: list[ID],
    ) -> None:
        """
        Updates the count data for a DatasetItemCount entity without serialization.
        The following fields are updated:
            - "unassigned_dataset_items": new items are appended, deleted items are removed
            - "n_dataset_items": increased or decreased by a delta
            - "n_items_per_label": updated entirely

        This method is useful when the unassigned dataset items list is very large.
        It helps to minimize read/write operations caused by entity serialization.

        :param id_: ID of the dataset item count
        :param new_dataset_item_count_data: new dataset item count data
        :param deleted_dataset_item_count_data: deleted dataset item count data
        :param assigned_dataset_items: List of all dataset items in the training dataset that were assigned a subset
        """
        update_query: dict[str, Any] = {}
        if added_unassigned_ids := new_dataset_item_count_data.dataset_item_ids:
            update_query["$push"] = {
                "unassigned_dataset_items": {
                    "$each": [IDToMongo.forward(dataset_item_id) for dataset_item_id in added_unassigned_ids]
                }
            }

        item_count_change = new_dataset_item_count_data.count - deleted_dataset_item_count_data.count
        if item_count_change != 0:
            update_query["$inc"] = {"n_dataset_items": item_count_change}

        # Due to the structure of the n_items_per_label,
        # we need to collect the existing content to get the aggregate number
        query_filter = self.preliminary_query_match_filter(access_mode=QueryAccessMode.READ)
        query_filter["_id"] = IDToMongo.forward(id_)
        doc = self._collection.find_one(filter=query_filter, projection={"n_items_per_label": True})

        item_per_label_update_query = []
        new_per_label_count = new_dataset_item_count_data.per_label_count
        deleted_per_label_count = deleted_dataset_item_count_data.per_label_count
        aggregated_count_per_label: dict[ID, int] = {
            label_id: new_per_label_count.get(label_id, 0) - deleted_per_label_count.get(label_id, 0)
            for label_id in set(new_per_label_count) | set(deleted_per_label_count)
        }
        if any(diff != 0 for diff in aggregated_count_per_label.values()):
            for n_items_dict in doc.get("n_items_per_label", []):  # type: ignore
                label_id = IDToMongo.backward(n_items_dict["label_id"])
                n_items = n_items_dict["n_items"] + aggregated_count_per_label.get(label_id, 0)
                item_per_label_update_query.append({"label_id": IDToMongo.forward(label_id), "n_items": n_items})
            update_query["$set"] = {"n_items_per_label": item_per_label_update_query}

        if update_query:
            self._collection.update_one(filter=query_filter, update=update_query)

        delete_query: dict[str, Any] = {}
        if deleted_unassigned_ids := deleted_dataset_item_count_data.dataset_item_ids + assigned_dataset_items:
            delete_query["$pullAll"] = {
                "unassigned_dataset_items": [
                    IDToMongo.forward(dataset_item_id) for dataset_item_id in deleted_unassigned_ids
                ]
            }
            self._collection.update_one(filter=query_filter, update=delete_query)
