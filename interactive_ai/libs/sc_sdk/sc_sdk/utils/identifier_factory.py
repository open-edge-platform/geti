"""
This module is responsible for producing Media Identifier entities for different purposes
"""

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging

from sc_sdk.entities.dataset_storage import DatasetStorage
from sc_sdk.entities.video import Video
from sc_sdk.repos import VideoRepo

from geti_types import ImageIdentifier, MediaIdentifierEntity, MediaType, VideoFrameIdentifier, VideoIdentifier

logger = logging.getLogger(__name__)


class IdentifierFactory:
    """
    The IdentifierFactory is responsible for producing Media Identifier entities for different purposes.
    It provides convenience functions for commonly used tasks within SC,
    such as "expand" a VideoIdentifier into a list of VideoFrameIdentifier,
    or producing a list of MediaIdentifiers which carry no annotations.
    """

    @staticmethod
    def generate_frame_identifiers_for_video(video: Video, stride: int | None = None) -> list[MediaIdentifierEntity]:
        """
        Generates frame identifiers for a given video.
        If stride is not specified, the stride parameter of each video will be used for that video's frames.
        By default, videos have their stride set to 1 frame per second.

        :param video: video entity
        :param stride: Stride with which to step through range of video frames
        :return:
        """
        final_stride = stride if stride is not None else video.stride
        return [
            VideoFrameIdentifier(video_id=video.id_, frame_index=i) for i in range(0, video.total_frames, final_stride)
        ]

    @staticmethod
    def expand_media_identifier(
        media_identifier: MediaIdentifierEntity, dataset_storage: DatasetStorage
    ) -> list[MediaIdentifierEntity]:
        """
        Generates the "children" media identifiers.
        For example, passing a VideoIdentifier will return a list of VideoFrameIdentifiers

        :param media_identifier: the "parent" media identifier
        :param dataset_storage: the DatasetStorage of the media identifier

        :return:
        """
        if isinstance(media_identifier, VideoIdentifier):
            video_repo = VideoRepo(dataset_storage.identifier)
            return IdentifierFactory.generate_frame_identifiers_for_video(
                video_repo.get_by_id(media_identifier.media_id)
            )
        raise NotImplementedError(f"Cannot expand `{media_identifier}`")

    @staticmethod
    def identifier_from_tuple(media_identifier_tuple: tuple) -> MediaIdentifierEntity:
        """
        Create a MediaIdentifierEntity from the tuple representation.

        :param media_identifier_tuple: Tuple containing:
         - The identifier name, which is either 'image', 'video' or 'video_frame'.
         - the media ID.
         - If the media is a video frame, the frame index.
        :return: Image, video or video frame identifier.
        """
        if len(media_identifier_tuple) < 2:
            raise ValueError("Cannot create media identifier from tuple: media_type and media_id must be included")
        media_type = media_identifier_tuple[0]
        media_id = media_identifier_tuple[1]
        if media_type == MediaType.IMAGE:
            return ImageIdentifier(image_id=media_id)
        if media_type == MediaType.VIDEO:
            return VideoIdentifier(video_id=media_id)
        if media_type == MediaType.VIDEO_FRAME:
            if len(media_identifier_tuple) < 3:
                raise ValueError("Cannot create video frame identifier without parameter frame_index")
            return VideoFrameIdentifier(video_id=media_id, frame_index=media_identifier_tuple[2])
        raise ValueError(
            f"Failed to create media identifier from tuple with media_type {media_type.value}: only "
            f"image, video and video_frame are allowed."
        )
