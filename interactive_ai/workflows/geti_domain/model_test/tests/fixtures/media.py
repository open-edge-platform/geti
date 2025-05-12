# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import pytest
from geti_types import ID, ImageIdentifier, VideoFrameIdentifier
from iai_core.entities.image import Image
from iai_core.entities.media import MediaPreprocessing, MediaPreprocessingStatus

from tests.fixtures.values import DummyValues


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
