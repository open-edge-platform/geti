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
"""Module for a cursor iterator"""

import logging
from typing import Any, Generic, TypeVar

import pymongo.cursor

from sc_sdk.repos.mappers.mongodb_mapper_interface import (
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
