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


import datetime

import pytest
from geti_types import ID, ImageIdentifier, VideoFrameIdentifier
from sc_sdk.entities.image import Image
from sc_sdk.entities.media import ImageExtensions, MediaPreprocessing, MediaPreprocessingStatus
from sc_sdk.entities.video import Video, VideoFrame

from tests.fixtures.values import DummyValues


@pytest.fixture
def fxt_image(fxt_ote_id) -> Image:
    return Image(
        name="dummy_image.jpg",
        uploader_id=DummyValues.CREATOR_NAME,
        id=fxt_ote_id(1),
        creation_date=datetime.datetime(
            year=2023,
            month=9,
            day=8,
            hour=1,
            minute=5,
            second=12,
            tzinfo=datetime.timezone.utc,
        ),
        width=100,
        height=100,
        size=100,
        extension=ImageExtensions.JPG,
        preprocessing=MediaPreprocessing(status=MediaPreprocessingStatus.FINISHED),
    )


@pytest.fixture
def fxt_image_entity_factory(fxt_ote_id, fxt_dataset_storage):
    def _build_image(index: int = 1, name: str = "dummy image"):
        return Image(
            name=name,
            uploader_id="",
            id=fxt_ote_id(index),
            height=32,
            width=32,
            size=100,
            preprocessing=MediaPreprocessing(status=MediaPreprocessingStatus.FINISHED),
        )

    yield _build_image


@pytest.fixture
def fxt_video_factory(fxt_ote_id):
    def _build_video(index: int = 1, name: str = "dummy video"):
        return Video(
            name=name,
            id=fxt_ote_id(index),
            uploader_id="",
            fps=30,
            height=32,
            width=32,
            total_frames=100,
            size=1000,
            preprocessing=MediaPreprocessing(status=MediaPreprocessingStatus.FINISHED),
        )

    yield _build_video


@pytest.fixture
def fxt_video_frame_entity_factory(fxt_video_factory):
    def _build_video_frame(video: Video | None = None, index: int = 1):
        return VideoFrame(
            video=video if video else fxt_video_factory(),
            frame_index=index,
        )

    yield _build_video_frame


@pytest.fixture
def fxt_image_identifier(fxt_mongo_id):
    yield ImageIdentifier(image_id=ID(fxt_mongo_id(0)))


@pytest.fixture
def fxt_video_frame_identifier(fxt_mongo_id):
    yield VideoFrameIdentifier(video_id=ID(fxt_mongo_id()), frame_index=DummyValues.FRAME_INDEX)


@pytest.fixture
def fxt_video_frame_identifier_2(fxt_mongo_id):
    yield VideoFrameIdentifier(video_id=ID(fxt_mongo_id()), frame_index=DummyValues.FRAME_INDEX + 1)
