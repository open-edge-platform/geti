"""This module implements the DatasetAdapterInterface"""

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import abc

from sc_sdk.entities.dataset_item import DatasetItem


class DatasetAdapterInterface(metaclass=abc.ABCMeta):
    """
    This interface describes how the Adapter looks like that allows an entity,
    such as the Dataset to fetch its DatasetItems lazily.
    """

    @abc.abstractmethod
    def fetch(self, key: int | slice | list) -> DatasetItem | list[DatasetItem]:
        """
        Fetch one or more DatasetItems given a list operation.

        :param key: Key to specify which element(s) to read, that is the key used
            by the __getitem__ method. The value can be an integer, a list or a slice.
        :return: Depending on the key, one or multiple deserialized DatasetItems
        """

    @abc.abstractmethod
    def get_length(self) -> int:
        """
        Returns the length of the full-dataset.

        :return: Length (int)
        """

    @abc.abstractmethod
    def get_items(self) -> list[DatasetItem]:
        """
        Get all the items in the dataset

        :return: List of DatasetItems
        """

    @abc.abstractmethod
    def delete_at_index(self, index: int) -> None:
        """
        Delete the item at the given index.

        :param index: the index of the item which will be deleted.
        """
