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
This module implements the repository for the list of suspended annotation scenes
"""

from collections.abc import Callable

from pymongo.command_cursor import CommandCursor
from pymongo.cursor import Cursor

from sc_sdk.entities.suspended_scenes import (
    NullSuspendedAnnotationScenesDescriptor,
    SuspendedAnnotationScenesDescriptor,
)
from sc_sdk.repos.base import DatasetStorageBasedSessionRepo
from sc_sdk.repos.mappers.cursor_iterator import CursorIterator
from sc_sdk.repos.mappers.mongodb_mappers.suspended_scenes_mapper import SuspendedAnnotationScenesDescriptorToMongo

from geti_types import DatasetStorageIdentifier, Session


class SuspendedAnnotationScenesRepo(DatasetStorageBasedSessionRepo[SuspendedAnnotationScenesDescriptor]):
    """
    Repository to persist ActiveScore entities in the database.

    :param dataset_storage_identifier: Identifier of the dataset_storage
    :param session: Session object; if not provided, it is loaded through the context variable CTX_SESSION_VAR
    """

    def __init__(
        self,
        dataset_storage_identifier: DatasetStorageIdentifier,
        session: Session | None = None,
    ) -> None:
        super().__init__(
            collection_name="suspended_annotation_scenes",
            session=session,
            dataset_storage_identifier=dataset_storage_identifier,
        )

    @property
    def forward_map(self) -> Callable[[SuspendedAnnotationScenesDescriptor], dict]:
        return SuspendedAnnotationScenesDescriptorToMongo.forward

    @property
    def backward_map(self) -> Callable[[dict], SuspendedAnnotationScenesDescriptor]:
        return SuspendedAnnotationScenesDescriptorToMongo.backward

    @property
    def null_object(self) -> NullSuspendedAnnotationScenesDescriptor:
        return NullSuspendedAnnotationScenesDescriptor()

    @property
    def cursor_wrapper(self) -> Callable[[Cursor | CommandCursor], CursorIterator]:
        return lambda mongo_cursor: CursorIterator(
            cursor=mongo_cursor,
            mapper=SuspendedAnnotationScenesDescriptorToMongo,
            parameter=None,
        )
