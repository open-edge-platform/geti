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
"""This module contains mock functions useful for testing"""

from geti_types import ID
from sc_sdk.entities.image import Image
from sc_sdk.entities.media import MediaPreprocessing, MediaPreprocessingStatus
from sc_sdk.entities.video import Video


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
