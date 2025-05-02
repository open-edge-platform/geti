# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
This module implements the repository for video entities
"""

import logging
from collections.abc import Callable, Iterable, Iterator, MutableMapping
from threading import Lock
from typing import Any
from weakref import WeakValueDictionary

from pymongo.command_cursor import CommandCursor
from pymongo.cursor import Cursor

from iai_core_py.entities.video import NullVideo, Video
from iai_core_py.repos.base.dataset_storage_based_repo import DatasetStorageBasedSessionRepo
from iai_core_py.repos.base.session_repo import QueryAccessMode
from iai_core_py.repos.mappers.cursor_iterator import CursorIterator
from iai_core_py.repos.mappers.mongodb_mappers.id_mapper import IDToMongo
from iai_core_py.repos.mappers.mongodb_mappers.media_mapper import VideoToMongo
from iai_core_py.repos.storage.binary_repos import ThumbnailBinaryRepo, VideoBinaryRepo

from geti_types import ID, DatasetStorageIdentifier, Session, Singleton, VideoFrameIdentifier, VideoIdentifier

logger = logging.getLogger(__name__)


class VideoCache(metaclass=Singleton):
    """
    Cache of Video objects. Frequently requested videos can be served by this cache
    instead of being repeatedly fetched from the repository. The cache is a singleton,
    so it is shared across VideoRepo objects.
    """

    def __init__(self) -> None:
        self._cache_lock = Lock()
        # The cache is implemented as a weak-ref value dictionary, which means the video
        # entries are automatically removed when the Python object is no longer referenced.
        self._cache: MutableMapping[tuple[DatasetStorageIdentifier, ID], Video] = WeakValueDictionary()

    def get_or_load(
        self,
        dataset_storage_identifier: DatasetStorageIdentifier,
        video_id: ID,
        load_fn: Callable[[ID], Video],
    ) -> Video:
        """
        Get a video from the cache, if present, or load it through the provided function.

        :param dataset_storage_identifier: Identifier of the dataset storage containing the video
        :param video_id: ID of the video
        :param load_fn: Function to load the video, in case of cache miss
        :return: Video object
        """
        with self._cache_lock:
            video = self._cache.get((dataset_storage_identifier, video_id), None)
            if video is None:  # cache miss
                video = load_fn(video_id)
                self._cache[(dataset_storage_identifier, video_id)] = video
        return video

    def remove(self, dataset_storage_identifier: DatasetStorageIdentifier, video_id: ID) -> None:
        """
        Remove a video from the cache, if present.

        :param dataset_storage_identifier: Identifier of the dataset storage containing the video
        :param video_id: ID of the video
        """
        with self._cache_lock:
            self._cache.pop((dataset_storage_identifier, video_id), None)

    def remove_all_by_dataset_storage(self, dataset_storage_identifier: DatasetStorageIdentifier) -> None:
        """
        Remove all videos relative to the given dataset storage from the cache.

        :param dataset_storage_identifier: Identifier of the dataset storage containing the video
        """
        with self._cache_lock:
            keys_to_remove = tuple(k for k in self._cache if k[0] == dataset_storage_identifier)
            for key in keys_to_remove:
                self._cache.pop(key, None)


class VideoRepo(DatasetStorageBasedSessionRepo[Video]):
    """
    Repository to persist Video entities in the database.

    :param dataset_storage_identifier: Identifier of the dataset_storage
    :param session: Session object; if not provided, it is loaded through the context variable CTX_SESSION_VAR
    """

    collection_name = "video"

    def __init__(
        self,
        dataset_storage_identifier: DatasetStorageIdentifier,
        session: Session | None = None,
    ) -> None:
        super().__init__(
            collection_name=VideoRepo.collection_name,
            session=session,
            dataset_storage_identifier=dataset_storage_identifier,
        )
        # binary repos are initialized lazily when needed
        self.__binary_repo: VideoBinaryRepo | None = None
        self.__thumbnail_binary_repo: ThumbnailBinaryRepo | None = None

    @property
    def forward_map(self) -> Callable[[Video], dict]:
        return VideoToMongo.forward

    @property
    def backward_map(self) -> Callable[[dict], Video]:
        return VideoToMongo.backward

    @property
    def null_object(self) -> NullVideo:
        return NullVideo()

    @property
    def cursor_wrapper(self) -> Callable[[Cursor | CommandCursor], CursorIterator]:
        return lambda mongo_cursor: CursorIterator(cursor=mongo_cursor, mapper=VideoToMongo, parameter=None)

    @property
    def binary_repo(self) -> VideoBinaryRepo:
        """Binary repo relative to the video repo"""
        if self.__binary_repo is None:
            self.__binary_repo = VideoBinaryRepo(self.identifier)
        return self.__binary_repo

    @property
    def thumbnail_binary_repo(self) -> ThumbnailBinaryRepo:
        """Thumbnail binary repo relative to the video repo"""
        if self.__thumbnail_binary_repo is None:
            self.__thumbnail_binary_repo = ThumbnailBinaryRepo(self.identifier)
        return self.__thumbnail_binary_repo

    def delete_by_id(self, id_: ID) -> bool:
        """
        Deletes a video and its thumbnail video from the database and filesystem

        :param id_: ID of the video to delete
        :return: True if any DB document was matched and deleted, False otherwise
        """
        # Get the document (which contains the binary data filename). If not found, it means
        # the ID is invalid, the video was already removed, or the user can't access it
        query = self.preliminary_query_match_filter(access_mode=QueryAccessMode.READ)
        query["_id"] = IDToMongo.forward(id_)
        # Find the video document, retrieve only the extension field
        video_doc = self._collection.find_one(query, {"extension": 1})
        if not video_doc:
            logger.warning(
                "Video document with id '%s' not found, possibly it is already deleted",
                id_,
            )
            return False

        # Invalidate the cache entry
        VideoCache().remove(dataset_storage_identifier=self.identifier, video_id=id_)
        # Delete the video document first, to prevent data corruption in case of error
        # during the binary deletion stage
        video_deleted: bool = super().delete_by_id(id_)
        if video_deleted:
            # Delete the thumbnails (both image- and video-like)
            frame_thumbnail_binary_filename = Video.thumbnail_filename_by_video_id(str(id_))
            video_thumbnail_binary_filename = Video.thumbnail_video_filename_by_video_id(str(id_))
            self.thumbnail_binary_repo.delete_by_filename(filename=frame_thumbnail_binary_filename)
            self.thumbnail_binary_repo.delete_by_filename(filename=video_thumbnail_binary_filename)

            # Delete binary
            video_binary_filename = f"{str(id_)}.{video_doc['extension'].lower()}"
            self.binary_repo.delete_by_filename(filename=video_binary_filename)

        return video_deleted

    def delete_all(self, extra_filter: dict | None = None) -> bool:
        """
        Delete all the videos, their binary data and thumbnails.

        :param extra_filter: Optional filter to apply in addition to the default one,
            which depends on the repo type.
        :return: True if any DB document was matched and deleted, False otherwise
        """
        if extra_filter is not None:
            # Since it's not possible to apply the filter to binary repos,
            # we would need a fallback implementation that deletes matched items
            # one by one, which is much slower of course.
            raise NotImplementedError

        # Invalidate cache entries
        VideoCache().remove_all_by_dataset_storage(dataset_storage_identifier=self.identifier)

        # Delete the videos documents first, to prevent data corruption in case of error
        # during the binaries deletion stage
        any_item_deleted = super().delete_all()

        if any_item_deleted:
            # Delete video binary data
            self.binary_repo.delete_all()

            # Delete thumbnails
            self.thumbnail_binary_repo.delete_all()

        return any_item_deleted

    def get_by_id(self, id_: ID) -> Video:
        """
        Fetch a video by ID.

        The method has an internal cache to improve quick subsequent calls, for example
        when reconstructing a dataset with multiple items for the same video.

        :param id_: ID of the video
        :return: Found Video, or NullVideo in case of no match
        """
        return VideoCache().get_or_load(
            dataset_storage_identifier=self.identifier, video_id=id_, load_fn=super().get_by_id
        )

    def get_frame_identifiers(self, *, stride: int | None = None) -> Iterator[VideoFrameIdentifier]:
        """
        Get frame identifiers for all videos in video_repo.
        If stride is not specified, the stride parameter of each video will be used for that video's frames.
        By default, videos have their stride set to 1 frame per second.

        :param stride: Stride with which to step through range of video frames
        :return: An iterator of frame identifiers representing each frame
        """

        if stride is not None and stride < 1:
            raise ValueError("Stride provided should be an integer with the value of 1 or more")

        all_videos = self.get_all()

        for video in all_videos:
            final_stride = stride if stride is not None else video.stride
            for i in range(0, video.total_frames, final_stride):
                yield VideoFrameIdentifier(video.id_, i)

    def get_all_identifiers(self) -> Iterator[VideoIdentifier]:
        """
        Get all media identifiers of videos contained in the dataset storage.

        :return: iterator over the video identifiers
        """
        for video_id in super().get_all_ids():
            yield VideoIdentifier(video_id=video_id)

    def get_video_by_ids(self, ids: Iterable[ID]) -> dict[ID, Video]:
        """
        Get video by video ids

        :param ids: List of IDs to obtain the video info for
        :return: Dict mapping each ID to the corresponding Video
        """
        query: dict[str, Any] = self.preliminary_query_match_filter(QueryAccessMode.READ)
        query["_id"] = {"$in": [IDToMongo.forward(id_) for id_ in ids]}
        docs = self._collection.find(query)
        return {IDToMongo.backward(doc["_id"]): VideoToMongo.backward(doc) for doc in docs}
