#
# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
#

"""This module contains the MongoDB mapper for media related entities"""

import logging
from os import path as osp

from iai_core_py.entities.image import Image
from iai_core_py.entities.media import ImageExtensions, MediaPreprocessing, MediaPreprocessingStatus, VideoExtensions
from iai_core_py.entities.video import Video
from iai_core_py.repos.mappers.mongodb_mapper_interface import (
    IMapperBackward,
    IMapperForward,
    IMapperSimple,
    MappingError,
)

from .id_mapper import IDToMongo
from .primitive_mapper import DatetimeToMongo
from geti_types import ImageIdentifier, MediaIdentifierEntity, MediaType, VideoFrameIdentifier, VideoIdentifier

logger = logging.getLogger(__name__)


class ImageIdentifierToMongo(IMapperSimple[ImageIdentifier, dict]):
    """MongoDB mapper for `ImageIdentifier` entities"""

    @staticmethod
    def forward(instance: ImageIdentifier) -> dict:
        return {
            "media_id": IDToMongo.forward(instance.media_id),
            "type": instance.media_type.value,
        }

    @staticmethod
    def backward(instance: dict) -> ImageIdentifier:
        media_id = instance.get("media_id", "")
        return ImageIdentifier(image_id=IDToMongo.backward(media_id))


class MediaPreprocessingToMongo(IMapperSimple[MediaPreprocessing, dict]):
    """MongoDB mapper for `MediaPreprocessing` entities"""

    @staticmethod
    def forward(instance: MediaPreprocessing) -> dict:
        return {
            "status": instance.status.value,
            "message": instance.message,
            "start_timestamp": DatetimeToMongo.forward(instance.start_timestamp)
            if instance.start_timestamp is not None
            else None,
            "end_timestamp": DatetimeToMongo.forward(instance.end_timestamp)
            if instance.end_timestamp is not None
            else None,
        }

    @staticmethod
    def backward(instance: dict) -> MediaPreprocessing:
        return MediaPreprocessing(
            status=MediaPreprocessingStatus[instance["status"]],
            message=instance.get("message"),
            start_timestamp=DatetimeToMongo.backward(instance.get("start_timestamp"))
            if instance.get("start_timestamp") is not None
            else None,
            end_timestamp=DatetimeToMongo.backward(instance.get("end_timestamp"))
            if instance.get("end_timestamp") is not None
            else None,
        )


class VideoIdentifierToMongo(IMapperSimple[VideoIdentifier, dict]):
    """MongoDB mapper for `VideoIdentifier` entities"""

    @staticmethod
    def forward(instance: VideoIdentifier) -> dict:
        return {
            "media_id": IDToMongo.forward(instance.media_id),
            "type": instance.media_type.value,
        }

    @staticmethod
    def backward(instance: dict) -> VideoIdentifier:
        media_id = instance.get("media_id")
        # Compatibility to allow passing docs from video repo to video identifier mapper
        if media_id is None:
            media_id = instance["_id"]
        return VideoIdentifier(video_id=IDToMongo.backward(media_id))


class VideoFrameIdentifierToMongo(IMapperSimple[VideoFrameIdentifier, dict]):
    """MongoDB mapper for `VideoFrameIdentifier` entities"""

    @staticmethod
    def forward(instance: VideoFrameIdentifier) -> dict:
        return {
            "media_id": IDToMongo.forward(instance.media_id),
            "type": instance.media_type.value,
            "frame_index": instance.frame_index,
        }

    @staticmethod
    def backward(instance: dict) -> VideoFrameIdentifier:
        # TODO: deprecate backward compatibility frame_number/frame_index
        return VideoFrameIdentifier(
            video_id=IDToMongo.backward(instance["media_id"]),
            frame_index=instance.get("frame_index", instance.get("frame_number")),
        )


class MediaIdentifierToMongo(IMapperSimple[MediaIdentifierEntity, dict]):
    """MongoDB mapper for `MediaIdentifier` entities"""

    @staticmethod
    def forward(instance: MediaIdentifierEntity) -> dict:
        if isinstance(instance, ImageIdentifier):
            return ImageIdentifierToMongo.forward(instance)
        if isinstance(instance, VideoFrameIdentifier):
            return VideoFrameIdentifierToMongo.forward(instance)
        if isinstance(instance, VideoIdentifier):
            return VideoIdentifierToMongo.forward(instance)
        raise MappingError(
            f"Cannot map MediaIdentifier with type {type(instance)} (media_type: {instance.media_type.value})"
        )

    @staticmethod
    def backward(instance: dict) -> MediaIdentifierEntity:
        media_identifier: MediaIdentifierEntity
        if instance["type"] == MediaType.IMAGE.value:
            media_identifier = ImageIdentifierToMongo.backward(instance)
        elif instance["type"] == MediaType.VIDEO_FRAME.value:
            media_identifier = VideoFrameIdentifierToMongo.backward(instance)
        elif instance["type"] == MediaType.VIDEO.value:
            media_identifier = VideoIdentifierToMongo.backward(instance)
        else:
            raise MappingError(f"Cannot unmap MediaIdentifier with type {instance['type']}")
        return media_identifier


class ImageToMongo(
    IMapperForward[Image, dict],
    IMapperBackward[Image, dict],
):
    """MongoDB mapper for `Image` entities"""

    @staticmethod
    def forward(instance: Image) -> dict:
        return {
            "_id": IDToMongo.forward(instance.id_),
            "name": instance.name,
            "uploader_id": instance.uploader_id,
            "creation_date": DatetimeToMongo.forward(instance.creation_date),
            "width": instance.width,
            "height": instance.height,
            "extension": str(instance.extension.name),
            "size": instance.size,
            "preprocessing": MediaPreprocessingToMongo.forward(instance.preprocessing),
        }

    @staticmethod
    def backward(instance: dict) -> Image:
        # construct the binary filename from the _id and the extension
        image_extension = instance["extension"]

        creation_date = DatetimeToMongo.backward(instance.get("creation_date"))
        return Image(
            id=IDToMongo.backward(instance["_id"]),
            uploader_id=instance.get("uploader_id", "Unknown"),
            name=instance["name"],
            creation_date=creation_date,
            ephemeral=False,
            extension=ImageExtensions[image_extension],
            width=int(instance["width"]),
            height=int(instance["height"]),
            size=int(instance["size"]),
            preprocessing=MediaPreprocessingToMongo.backward(instance["preprocessing"])
            # TODO: remove in scope of CVS-163688
            if "preprocessing" in instance
            else MediaPreprocessing(status=MediaPreprocessingStatus.FINISHED),
        )


class VideoToMongo(IMapperForward[Video, dict], IMapperBackward[Video, dict]):
    """MongoDB mapper for `Video` entities"""

    @staticmethod
    def forward(instance: Video) -> dict:
        # since extension property is added to Video entity in a later version, check to verify that instance.extension
        # matches the extension in instance.data_binary_filename.
        if instance.data_binary_filename is not None:
            filename_extension = osp.splitext(instance.data_binary_filename)[1]
            if filename_extension and instance.extension.name.lower() != filename_extension.lower()[1:]:
                raise ValueError(
                    f"Video extension {instance.extension.name} does not match the extension of the binary filename "
                    f"{filename_extension}."
                )

        return {
            "_id": IDToMongo.forward(instance.id_),
            "uploader_id": instance.uploader_id,
            "name": instance.name,
            "stride": instance.stride,
            "creation_date": DatetimeToMongo.forward(instance.creation_date),
            "width": instance.width,
            "height": instance.height,
            "fps": instance.fps,
            "total_frames": instance.total_frames,
            "size": instance.size,
            "extension": str(instance.extension.name),
            "preprocessing": MediaPreprocessingToMongo.forward(instance.preprocessing),
        }

    @staticmethod
    def backward(instance: dict) -> Video:
        # construct the binary filename from the _id and the extension
        video_extension = instance["extension"]

        creation_date = DatetimeToMongo.backward(instance.get("creation_date"))
        return Video(
            id=IDToMongo.backward(instance["_id"]),
            uploader_id=instance.get("uploader_id", "Unknown"),
            name=instance["name"],
            creation_date=creation_date,
            stride=int(instance["stride"]) if "stride" in instance else None,
            ephemeral=False,
            extension=VideoExtensions[video_extension],
            fps=instance.get("fps"),  # type: ignore
            width=instance.get("width"),  # type: ignore
            height=instance.get("height"),  # type: ignore
            total_frames=instance.get("total_frames"),  # type: ignore
            size=int(instance["size"]),
            preprocessing=MediaPreprocessingToMongo.backward(instance["preprocessing"])
            # TODO: remove in scope of CVS-163688
            if "preprocessing" in instance
            else MediaPreprocessing(status=MediaPreprocessingStatus.FINISHED),
        )
