# INTEL CONFIDENTIAL
#
# Copyright (C) 2021 Intel Corporation
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

import pytest

from sc_sdk.entities.image import Image
from sc_sdk.entities.media import MediaPreprocessing, MediaPreprocessingStatus

from .values import DummyValues
from geti_types import ID, ImageIdentifier, VideoFrameIdentifier


@pytest.fixture
def fxt_image_identifier(fxt_mongo_id):
    yield ImageIdentifier(image_id=ID(fxt_mongo_id(0)))


@pytest.fixture
def fxt_video_frame_identifier(fxt_mongo_id):
    yield VideoFrameIdentifier(video_id=ID(fxt_mongo_id()), frame_index=DummyValues.FRAME_INDEX)


@pytest.fixture
def fxt_video_frame_identifier_2(fxt_mongo_id):
    yield VideoFrameIdentifier(video_id=ID(fxt_mongo_id()), frame_index=DummyValues.FRAME_INDEX + 1)


@pytest.fixture
def fxt_image_entity_factory(fxt_ote_id):
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
