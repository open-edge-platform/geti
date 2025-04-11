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

import numpy as np
import pytest
from geti_types import ID
from sc_sdk.entities.annotation import AnnotationScene, AnnotationSceneKind
from sc_sdk.entities.image import Image
from sc_sdk.entities.media import MediaPreprocessing, MediaPreprocessingStatus
from sc_sdk.entities.video import Video, VideoFrame

from tests.fixtures.values import DummyValues


@pytest.fixture
def fxt_mongo_id():
    """
    Create a realistic MongoDB ID string for testing purposes.

    If you need multiple ones, call this fixture repeatedly with different arguments.
    """
    base_id: int = 0x60D31793D5F1FB7E6E3C1A4F

    def _build_id(offset: int = 0) -> str:
        return str(hex(base_id + offset))[2:]

    yield _build_id


@pytest.fixture
def fxt_image_entity(fxt_mongo_id):
    yield Image(
        name="dummy_image",
        uploader_id="",
        id=ID(fxt_mongo_id(1)),
        numpy=np.ones([5, 5, 3]),
        preprocessing=MediaPreprocessing(status=MediaPreprocessingStatus.FINISHED),
    )


@pytest.fixture
def fxt_video_entity(fxt_mongo_id, fxt_dataset_storage):
    yield Video(
        name="dummy_video",
        id=ID(fxt_mongo_id(2)),
        uploader_id="",
        fps=5.0,
        width=100,
        height=50,
        total_frames=10,
        size=1000,
        preprocessing=MediaPreprocessing(status=MediaPreprocessingStatus.FINISHED),
    )


@pytest.fixture
def fxt_video_frame(fxt_video_entity):
    yield VideoFrame(video=fxt_video_entity, frame_index=0)


@pytest.fixture
def fxt_annotation_scene_empty(fxt_image_entity, fxt_ote_id):
    yield AnnotationScene(
        kind=AnnotationSceneKind.ANNOTATION,
        media_identifier=fxt_image_entity.media_identifier,
        media_height=DummyValues.MEDIA_HEIGHT,
        media_width=DummyValues.MEDIA_WIDTH,
        id_=fxt_ote_id(1),
    )
