# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""This module contains mock functions useful for testing"""

from geti_types import ID
from iai_core.entities.image import Image
from iai_core.entities.media import MediaPreprocessing, MediaPreprocessingStatus
from iai_core.entities.video import Video


def mock_get_image_by_id(image_id: ID) -> Image:
    """
    returns an image with the given id and mock data

    :param image_id: id of the image to get
    :return: a mocked image with the given id
    """
    return Image(
        id=image_id,
        name="",
        uploader_id="",
        width=10,
        height=10,
        size=0,
        preprocessing=MediaPreprocessing(status=MediaPreprocessingStatus.FINISHED),
    )


def mock_get_video_by_id(video_id: ID) -> Video:
    """
    returns a video with the given id and mock data

    :param video_id: id of the video to get
    :return: a mocked video with the given id
    """
    return Video(
        id=video_id,
        name="",
        uploader_id="",
        fps=0,
        width=0,
        height=0,
        total_frames=0,
        size=0,
        preprocessing=MediaPreprocessing(status=MediaPreprocessingStatus.FINISHED),
    )


def return_none(self, *args, **kwargs) -> None:
    """
    Do nothing method
    """
    return
