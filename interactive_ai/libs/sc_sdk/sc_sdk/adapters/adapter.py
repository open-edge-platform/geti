"""
This module implements the ReferenceAdapter and ProxyAdapter
"""

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

import abc
from collections.abc import Callable
from typing import Generic, Protocol, TypeVar

from geti_types import ID


class PersistentEntity(Protocol):
    """
    Protocol representing a persistent entity
    which can be identified by its ID.
    """

    id_: ID


TEntity = TypeVar("TEntity", bound=PersistentEntity)


class IAdapter(Generic[TEntity], metaclass=abc.ABCMeta):
    """
    Generic Adapter that is either used to lazily fetch data from a repo or hold a reference to an entity
    """

    @property
    @abc.abstractmethod
    def id_(self) -> ID:
        """Get the ID of the entity"""
        raise NotImplementedError

    @abc.abstractmethod
    def get(self) -> TEntity:
        """Get the entity"""
        raise NotImplementedError


class ReferenceAdapter(IAdapter[TEntity]):
    """
    Adapter that holds a reference to an entity in memory
    """

    def __init__(self, reference: TEntity) -> None:
        self._reference = reference

    @property
    def id_(self) -> ID:
        """
        Get the ID of the referenced entity.
        """
        return self._reference.id_

    def get(self) -> TEntity:
        """
        Get the referenced entity.
        """
        return self._reference


class ProxyAdapter(IAdapter[TEntity]):
    """
    Adapter that holds an ID and a function to fetch the entity from the database.
    """

    def __init__(self, id: ID, proxy: Callable[[], TEntity]) -> None:
        self._id = id
        self._proxy = proxy

    @property
    def id_(self) -> ID:
        """
        Get the ID of the referenced entity
        """
        return self._id

    def get(self) -> TEntity:
        """
        Call the _proxy() method to fetch the entity from the database
        """
        return self._proxy()


class NoAdapterSetError(ValueError):
    """Error that will be raised when an adapter was not set"""
