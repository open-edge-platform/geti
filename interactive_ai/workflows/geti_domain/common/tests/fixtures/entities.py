# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import numpy as np
import pytest
from geti_types import ID
from iai_core.entities.annotation import AnnotationScene, AnnotationSceneKind
from iai_core.entities.image import Image
from iai_core.entities.media import MediaPreprocessing, MediaPreprocessingStatus
from iai_core.entities.video import Video, VideoFrame

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
