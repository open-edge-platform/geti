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
This module implements the repository for VideoAnnotationRange
"""

from collections.abc import Callable

from pymongo import DESCENDING, IndexModel
from pymongo.command_cursor import CommandCursor
from pymongo.cursor import Cursor

from sc_sdk.entities.video_annotation_range import NullVideoAnnotationRange, VideoAnnotationRange
from sc_sdk.repos.base.dataset_storage_based_repo import DatasetStorageBasedSessionRepo
from sc_sdk.repos.mappers import VideoAnnotationRangeToMongo
from sc_sdk.repos.mappers.cursor_iterator import CursorIterator
from sc_sdk.repos.mappers.mongodb_mappers.id_mapper import IDToMongo

from geti_types import ID, DatasetStorageIdentifier, Session


class VideoAnnotationRangeRepo(DatasetStorageBasedSessionRepo[VideoAnnotationRange]):
    """
    Repository to persist VideoAnnotationRange entities in the database.

    :param dataset_storage_identifier: Identifier of the dataset_storage
    :param session: Session object; if not provided, it is loaded through the context variable CTX_SESSION_VAR
    """

    def __init__(
        self,
        dataset_storage_identifier: DatasetStorageIdentifier,
        session: Session | None = None,
    ) -> None:
        super().__init__(
            collection_name="video_annotation_range",
            session=session,
            dataset_storage_identifier=dataset_storage_identifier,
        )

    @property
    def forward_map(self) -> Callable[[VideoAnnotationRange], dict]:
        return VideoAnnotationRangeToMongo.forward

    @property
    def backward_map(self) -> Callable[[dict], VideoAnnotationRange]:
        return VideoAnnotationRangeToMongo.backward

    @property
    def null_object(self) -> NullVideoAnnotationRange:
        return NullVideoAnnotationRange()

    @property
    def cursor_wrapper(self) -> Callable[[Cursor | CommandCursor], CursorIterator]:
        return lambda mongo_cursor: CursorIterator(
            cursor=mongo_cursor,
            mapper=VideoAnnotationRangeToMongo,
            parameter=None,
        )

    @property
    def indexes(self) -> list[IndexModel]:
        super_indexes = super().indexes
        new_indexes = [IndexModel([("video_id", DESCENDING)])]
        return super_indexes + new_indexes

    def delete_all_by_video_id(self, video_id: ID) -> None:
        """
        Delete all VideoAnnotationRange objects from the database that have the passed
        video ID.

        :param video_id: Video ID to delete all VideoAnnotationRange objects for
        """
        video_filter = {"video_id": IDToMongo.forward(video_id)}
        self.delete_all(extra_filter=video_filter)

    def get_latest_by_video_id(self, video_id: ID) -> VideoAnnotationRange:
        """
        Get the latest VideoAnnotationRange by video_id.

        If none is found, a default one with no labels is returned.

        :param video_id: video_id
        :return: VideoAnnotationRange
        """
        video_filter = {"video_id": IDToMongo.forward(video_id)}
        video_ann_range = self.get_one(extra_filter=video_filter, latest=True)
        if isinstance(video_ann_range, NullVideoAnnotationRange):
            video_ann_range = VideoAnnotationRange(video_id=video_id, range_labels=[], id_=self.generate_id())
        return video_ann_range
