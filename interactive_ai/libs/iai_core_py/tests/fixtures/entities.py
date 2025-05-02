# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import pytest

from iai_core.entities.annotation import AnnotationScene, AnnotationSceneKind
from iai_core.entities.image import Image
from iai_core.entities.media import MediaPreprocessing, MediaPreprocessingStatus

from .values import DummyValues
from geti_types import ID


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
        width=5,
        height=5,
        size=100,
        preprocessing=MediaPreprocessing(status=MediaPreprocessingStatus.FINISHED),
    )


@pytest.fixture
def fxt_annotation_scene_empty(fxt_image_entity, fxt_ote_id):
    yield AnnotationScene(
        kind=AnnotationSceneKind.ANNOTATION,
        media_identifier=fxt_image_entity.media_identifier,
        media_height=DummyValues.MEDIA_HEIGHT,
        media_width=DummyValues.MEDIA_WIDTH,
        id_=fxt_ote_id(1),
    )
