"""This module implements the Repository interface"""

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import abc
from typing import Generic, TypeVar

from geti_types import ID

AnyType = TypeVar("AnyType")


class IRepo(Generic[AnyType]):
    """
    This interface describes how a Repository looks like.
    """

    @abc.abstractmethod
    def save(self, instance: AnyType) -> None:
        """
        Saves an instance and updates the instantiated entity (instance) with a (non-empty ID) object if applicable.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def get_by_id(self, _id: ID) -> AnyType:
        """
        Returns a single instance given its ID. Returns a Null instance if it can not be found
        """
        raise NotImplementedError

    @abc.abstractmethod
    def delete_by_id(self, _id: ID) -> None:
        """
        Deletes a single entity in a repository by it's ID.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def delete_all(self) -> None:
        """
        Deletes all entities of a repository.
        """
        raise NotImplementedError

    @staticmethod
    @abc.abstractmethod
    def generate_id() -> ID:
        """
        Generates a unique ID that can be assigned to an entity
        """
        raise NotImplementedError
