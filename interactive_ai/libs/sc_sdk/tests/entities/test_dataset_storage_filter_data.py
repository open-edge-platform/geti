# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import datetime

import pytest

from sc_sdk.entities.annotation_scene_state import AnnotationState
from sc_sdk.entities.dataset_storage_filter_data import (
    AnnotationSceneFilterData,
    DatasetStorageFilterData,
    MediaFilterData,
    ShapeFilterData,
    VideoFilterData,
)
from sc_sdk.entities.media import ImageExtensions, MediaPreprocessingStatus
from sc_sdk.entities.shapes import ShapeType


@pytest.mark.ScSdkComponent
class TestDatasetStorageFilterData:
    def test_media_filter_data_from_image(
        self,
        fxt_image,
    ) -> None:
        # Act
        result = MediaFilterData.from_media(media=fxt_image)

        # Assert
        assert result == MediaFilterData(
            media_name="dummy_image.jpg",
            media_extension=ImageExtensions.JPG,
            media_height=100,
            media_width=100,
            upload_date=datetime.datetime(
                year=2023,
                month=9,
                day=8,
                hour=1,
                minute=5,
                second=12,
                tzinfo=datetime.timezone.utc,
            ),
            uploader_id=fxt_image.uploader_id,
            size=100,
        )

    def test_media_filter_data_from_video(
        self,
        fxt_video_entity,
    ) -> None:
        # Act
        result = MediaFilterData.from_media(media=fxt_video_entity)

        # Assert
        assert result == MediaFilterData(
            media_name=fxt_video_entity.name,
            media_extension=fxt_video_entity.extension,
            media_height=fxt_video_entity.height,
            media_width=fxt_video_entity.width,
            upload_date=fxt_video_entity.creation_date,
            uploader_id=fxt_video_entity.uploader_id,
            size=fxt_video_entity.size,
            video_filter_data=VideoFilterData(
                frame_rate=fxt_video_entity.fps,
                frame_count=fxt_video_entity.total_frames,
                frame_stride=fxt_video_entity.fps,
                duration=fxt_video_entity.duration,
                unannotated_frames=fxt_video_entity.total_frames,
            ),
        )

    def test_annotation_scene_filter_data_from_annotation_scene(
        self,
        fxt_annotation_scene,
    ) -> None:
        # Act
        result = AnnotationSceneFilterData.from_annotation_scene(annotation_scene=fxt_annotation_scene)

        # Assert
        assert result == AnnotationSceneFilterData(
            annotation_scene_id=fxt_annotation_scene.id_,
            user_name="editor",
            shapes=[
                ShapeFilterData(
                    shape_type=ShapeType.RECTANGLE,
                    area_percentage=0.03125,
                    area_pixel=9600.0,
                )
            ],
            label_ids=sorted(fxt_annotation_scene.get_label_ids(include_empty=True)),
            creation_date=datetime.datetime(2021, 7, 15, 0, 0, tzinfo=datetime.timezone.utc),
        )

    def test_dataset_storage_filter_data_creation(self, fxt_annotation_scene, fxt_image) -> None:
        # Act
        result = DatasetStorageFilterData.create_dataset_storage_filter_data(
            media_identifier=fxt_image.media_identifier,
            media=fxt_image,
            annotation_scene=fxt_annotation_scene,
            media_annotation_state=AnnotationState.ANNOTATED,
            preprocessing=MediaPreprocessingStatus.FINISHED,
        )

        # Assert
        assert result == DatasetStorageFilterData(
            media_identifier=fxt_image.media_identifier,
            media_filter_data=MediaFilterData(
                media_name="dummy_image.jpg",
                media_extension=ImageExtensions.JPG,
                media_height=32,
                media_width=32,
                upload_date=datetime.datetime(
                    year=2023,
                    month=9,
                    day=8,
                    hour=1,
                    minute=5,
                    second=12,
                    tzinfo=datetime.timezone.utc,
                ),
                uploader_id=fxt_image.uploader_id,
                size=0,
            ),
            annotation_scene_filter_data=AnnotationSceneFilterData(
                annotation_scene_id=fxt_annotation_scene.id_,
                user_name="editor",
                shapes=[
                    ShapeFilterData(
                        shape_type=ShapeType.RECTANGLE,
                        area_percentage=0.03125,
                        area_pixel=9600.0,
                    )
                ],
                label_ids=sorted(fxt_annotation_scene.get_label_ids(include_empty=True)),
                creation_date=datetime.datetime(2021, 7, 15, 0, 0, tzinfo=datetime.timezone.utc),
            ),
            media_annotation_state=AnnotationState.ANNOTATED,
            preprocessing=MediaPreprocessingStatus.FINISHED,
        )
