# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import datetime

import pytest

from iai_core_py.entities.annotation_scene_state import AnnotationState
from iai_core_py.entities.dataset_storage_filter_data import (
    AnnotationSceneFilterData,
    DatasetStorageFilterData,
    MediaFilterData,
)
from iai_core_py.entities.image import Image
from iai_core_py.entities.media import ImageExtensions, MediaPreprocessing, MediaPreprocessingStatus

from .values import DummyValues


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
def fxt_dataset_storage_filter_data(fxt_annotation_scene, fxt_image) -> DatasetStorageFilterData:
    media_filter_data = MediaFilterData.from_media(media=fxt_image)
    annotation_scene_filter_data = AnnotationSceneFilterData.from_annotation_scene(
        annotation_scene=fxt_annotation_scene,
    )
    return DatasetStorageFilterData(
        media_identifier=fxt_image.media_identifier,
        media_filter_data=media_filter_data,
        annotation_scene_filter_data=annotation_scene_filter_data,
        media_annotation_state=AnnotationState.ANNOTATED,
        ephemeral=True,
        preprocessing=MediaPreprocessingStatus.FINISHED,
    )


@pytest.fixture
def fxt_dataset_storage_filter_data_video(fxt_annotation_scene, fxt_video_entity) -> DatasetStorageFilterData:
    media_filter_data = MediaFilterData.from_media(media=fxt_video_entity)
    annotation_scene_filter_data = AnnotationSceneFilterData.from_annotation_scene(
        annotation_scene=fxt_annotation_scene,
    )
    return DatasetStorageFilterData(
        media_identifier=fxt_video_entity.media_identifier,
        media_filter_data=media_filter_data,
        annotation_scene_filter_data=annotation_scene_filter_data,
        media_annotation_state=AnnotationState.ANNOTATED,
        ephemeral=True,
        preprocessing=MediaPreprocessingStatus.FINISHED,
    )
