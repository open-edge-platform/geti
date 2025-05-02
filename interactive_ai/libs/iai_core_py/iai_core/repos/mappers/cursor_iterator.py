# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""Module for a cursor iterator"""

import logging
from typing import Any, Generic, TypeVar

import pymongo.cursor

from iai_core.repos.mappers.mongodb_mapper_interface import (
    IMapperBackward,
    IMapperDatasetStorageBackward,
    IMapperDatasetStorageIdentifierBackward,
    IMapperModelStorageBackward,
    IMapperModelStorageIdentifierBackward,
    IMapperParametricBackward,
    IMapperProjectBackward,
    IMapperProjectIdentifierBackward,
    IMapperSimple,
)

AnyType = TypeVar("AnyType")

logger = logging.getLogger(__name__)


class CursorIterator(Generic[AnyType]):
    """
    Wrapper for mongo cursor to iterate and map documents to python object.
    """

    def __init__(
        self,
        mapper: (
            IMapperSimple
            | type[IMapperSimple]
            | type[IMapperBackward]
            | type[IMapperDatasetStorageBackward]
            | type[IMapperDatasetStorageIdentifierBackward]
            | type[IMapperModelStorageBackward]
            | type[IMapperModelStorageIdentifierBackward]
            | type[IMapperParametricBackward]
            | type[IMapperProjectBackward]
            | type[IMapperProjectIdentifierBackward]
        ),
        cursor: pymongo.cursor.Cursor | pymongo.command_cursor.CommandCursor,
        parameter: Any = None,
    ) -> None:
        self._cursor = cursor
        self._mapper = mapper
        self._parameter = parameter
        # First time iter is used in cases where the repo does not find any result which
        # gives a cursor that is not alive. In these cases, we want the cursor iterator
        # to return an empty list for the first iteration, instead of throwing an error.
        self._first_time_iter = True

    def __map(self, item: dict) -> AnyType:
        if self._parameter is not None:
            return self._mapper.backward(item, self._parameter)  # type: ignore
        return self._mapper.backward(item)  # type: ignore

    def __next__(self) -> AnyType:
        """Advance and return the next object in the cursor"""
        item = self._cursor.next()
        return self.__map(item)

    def __iter__(self):
        if not self._cursor.alive and not self._first_time_iter:
            raise RuntimeError("Cursor is no longer alive, so it can't be iterated.")
        self._first_time_iter = False
        return self
