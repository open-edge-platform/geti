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

"""This module contains the implementation of the DatasetAdapter"""

from collections.abc import Callable
from typing import cast

import numpy as np

from sc_sdk.entities.dataset_item import DatasetItem
from sc_sdk.entities.interfaces.dataset_adapter_interface import DatasetAdapterInterface


class DatasetAdapter(DatasetAdapterInterface):
    """
    The DatasetAdapter class provides an adapter to lazy load the dataset items.

    Deserialization can take quite a bit of time for huge Dataset entities,
    especially for annotation with many shapes, while not all data in the Dataset
    might be accessed necessarily. For instance, a model might hold a reference to a
    dataset entity, while this dataset entity is not necessarily used in a next phase.
    """

    def __init__(
        self,
        dataset_item_backward_mapper: Callable[[dict], DatasetItem],
        dataset_items_docs: list[dict],
    ) -> None:
        self.dataset_item_backward_mapper = dataset_item_backward_mapper
        self.dataset_items_docs = dataset_items_docs
        # cache for already deserialized items
        self.__items: list[DatasetItem | None] = [None] * len(dataset_items_docs)

    def __deserialize(self):
        for i, dataset_item_doc in enumerate(self.dataset_items_docs):
            self.__items[i] = self.dataset_item_backward_mapper(dataset_item_doc)

        return self.__items

    def _fetch_at_index(self, index: int) -> DatasetItem:
        cached_item = self.__items[index]
        if cached_item is None:
            dataset_item_doc = self.dataset_items_docs[index]
            result = self.dataset_item_backward_mapper(dataset_item_doc)
            self.__items[index] = result
        else:
            result = cached_item
        return result

    def fetch(self, key: int | slice | list) -> DatasetItem | list[DatasetItem]:
        if isinstance(key, list):
            return [cast("DatasetItem", self.fetch(ii)) for ii in key]
        if isinstance(key, slice):
            # Get the start, stop, and step from the slice
            return [cast("DatasetItem", self.fetch(ii)) for ii in range(*key.indices(len(self.dataset_items_docs)))]
        if isinstance(key, int | np.int32 | np.int64):
            if key < 0:  # Handle negative indices
                key += len(self.dataset_items_docs)
            if key < 0 or key >= len(self.dataset_items_docs):
                raise IndexError(f"Index ({key}) is out of range for dataset")
            return self._fetch_at_index(key)
        raise TypeError(
            f"Instance of type `{type(key).__name__}` cannot be used to deserialize Dataset Item docs. "
            f"Only slice and int are supported"
        )

    def get_length(self) -> int:
        return len(self.dataset_items_docs)

    def get_items(self) -> list[DatasetItem]:
        if any(item is None for item in self.__items):
            return self.__deserialize()
        return cast("list[DatasetItem]", self.__items)

    def delete_at_index(self, index: int) -> None:
        del self.dataset_items_docs[index]
        del self.__items[index]
