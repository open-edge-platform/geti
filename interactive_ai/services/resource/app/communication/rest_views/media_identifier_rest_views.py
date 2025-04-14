# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import abc
from collections.abc import Sequence
from typing import Generic, TypeVar

from geti_types import ID, ImageIdentifier, MediaIdentifierEntity, MediaType, VideoFrameIdentifier, VideoIdentifier

T = TypeVar("T")
FRAME_INDEX = "frame_index"
IMAGE_ID = "image_id"
TYPE = "type"
VIDEO_ID = "video_id"


class MediaIdentifierRESTViewBase(Generic[T]):
    supported_types: Sequence[MediaType] = []

    @staticmethod
    @abc.abstractmethod
    def media_identifier_to_rest(media_identifier: T) -> dict:
        raise NotImplementedError

    @staticmethod
    @abc.abstractmethod
    def media_identifier_from_rest(data: dict) -> T:
        raise NotImplementedError

    @staticmethod
    @abc.abstractmethod
    def media_identifier_to_url(media_identifier: T) -> str:
        raise NotImplementedError


class ImageIdentifierRESTViewsBase(MediaIdentifierRESTViewBase[ImageIdentifier]):
    supported_types = [MediaType.IMAGE]

    @staticmethod
    def media_identifier_to_rest(media_identifier: ImageIdentifier) -> dict:
        return {
            TYPE: media_identifier.media_type.value,
            IMAGE_ID: str(media_identifier.media_id),
        }

    @staticmethod
    def media_identifier_from_rest(data: dict) -> ImageIdentifier:
        return ImageIdentifier(ID(data[IMAGE_ID]))

    @staticmethod
    def media_identifier_to_url(media_identifier: ImageIdentifier) -> str:
        return f"media/images/{str(media_identifier.media_id)}"


class VideoFrameIdentifierRESTViewsBase(MediaIdentifierRESTViewBase[VideoFrameIdentifier]):
    supported_types = [MediaType.VIDEO_FRAME]

    @staticmethod
    def media_identifier_to_rest(media_identifier: VideoFrameIdentifier) -> dict:
        return {
            TYPE: media_identifier.media_type.value,
            VIDEO_ID: str(media_identifier.media_id),
            FRAME_INDEX: media_identifier.frame_index,
        }

    @staticmethod
    def media_identifier_from_rest(data: dict) -> VideoFrameIdentifier:
        return VideoFrameIdentifier(video_id=ID(data[VIDEO_ID]), frame_index=int(data[FRAME_INDEX]))

    @staticmethod
    def media_identifier_to_url(media_identifier: VideoFrameIdentifier) -> str:
        return f"media/videos/{str(media_identifier.media_id)}/frames/{str(media_identifier.frame_index)}"


class VideoIdentifierRESTViewsBase(MediaIdentifierRESTViewBase[VideoIdentifier]):
    supported_types = [MediaType.VIDEO]

    @staticmethod
    def media_identifier_to_rest(media_identifier: VideoIdentifier) -> dict:
        return {
            TYPE: media_identifier.media_type.value,
            VIDEO_ID: str(media_identifier.media_id),
        }

    @staticmethod
    def media_identifier_from_rest(data: dict) -> VideoIdentifier:
        return VideoIdentifier(video_id=ID(data[VIDEO_ID]))

    @staticmethod
    def media_identifier_to_url(media_identifier: T):  # noqa: ANN205
        raise NotImplementedError


class MediaIdentifierRESTViews:
    registered_views: list[MediaIdentifierRESTViewBase] = [
        ImageIdentifierRESTViewsBase(),
        VideoFrameIdentifierRESTViewsBase(),
        VideoIdentifierRESTViewsBase(),
    ]

    @staticmethod
    def media_identifier_to_rest(media_identifier: MediaIdentifierEntity) -> dict:
        for view in MediaIdentifierRESTViews.registered_views:
            if media_identifier.media_type in view.supported_types:
                return view.media_identifier_to_rest(media_identifier)
        raise NotImplementedError(
            f"Got unsupported media type `{str(type(media_identifier))}` "
            f"for MediaIdentifierRESTViews.media_identifier_to_rest"
        )

    @staticmethod
    def media_identifier_from_rest(data: dict) -> MediaIdentifierEntity:
        for view in MediaIdentifierRESTViews.registered_views:
            if data[TYPE] in view.supported_types:
                return view.media_identifier_from_rest(data)
        raise NotImplementedError(
            f"Got unsupported media type `{data['type']}` for MediaIdentifierRESTViews.media_identifier_from_rest"
        )

    @staticmethod
    def media_identifier_to_url(media_identifier: MediaIdentifierEntity) -> str:
        for view in MediaIdentifierRESTViews.registered_views:
            if media_identifier.media_type in view.supported_types:
                return view.media_identifier_to_url(media_identifier)
        raise NotImplementedError(
            f"Got unsupported media type `{str(type(media_identifier))}` "
            f"for MediaIdentifierRESTViews.media_identifier_to_url"
        )
