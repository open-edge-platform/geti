# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from unittest.mock import patch

import pytest

from iai_core_py.entities.dataset_storage_filter_data import (
    AnnotationSceneFilterData,
    DatasetStorageFilterData,
    MediaFilterData,
    ShapeFilterData,
    VideoFilterData,
)
from iai_core_py.entities.media import MediaPreprocessingStatus
from iai_core_py.repos import AnnotationSceneRepo, AnnotationSceneStateRepo, ImageRepo, VideoRepo
from iai_core_py.repos.dataset_storage_filter_repo import DatasetStorageFilterRepo
from iai_core_py.services.dataset_storage_filter_service import DatasetStorageFilterService

from geti_types import ImageIdentifier, MediaIdentifierEntity, MediaType, VideoFrameIdentifier


class TestDatasetStorageFilterService:
    def test_on_new_image_upload(
        self,
        fxt_image,
        fxt_ote_id,
    ) -> None:
        # Arrange
        workspace_id = fxt_ote_id(1)
        project_id = fxt_ote_id(2)
        dataset_storage_id = fxt_ote_id(3)
        expected_media_filter_data = DatasetStorageFilterData(
            media_identifier=fxt_image.media_identifier,
            media_filter_data=MediaFilterData(
                media_name=fxt_image.name,
                media_extension=fxt_image.extension,
                media_width=fxt_image.width,
                media_height=fxt_image.height,
                upload_date=fxt_image.creation_date,
                uploader_id=fxt_image.uploader_id,
                size=fxt_image.size,
            ),
            preprocessing=MediaPreprocessingStatus.FINISHED,
        )

        with (
            patch.object(
                ImageRepo,
                "get_by_id",
                return_value=fxt_image,
            ) as mock_get_image,
            patch.object(
                DatasetStorageFilterRepo,
                "upsert_dataset_storage_filter_data",
                return_value=None,
            ) as mock_create_new_media_filter_data_entry,
        ):
            # Act
            DatasetStorageFilterService.on_new_media_upload(
                workspace_id=workspace_id,
                project_id=project_id,
                dataset_storage_id=dataset_storage_id,
                media_id=fxt_image.id_,
                media_type=MediaType.IMAGE,
            )

        # Assert
        mock_get_image.assert_called_once_with(id_=fxt_image.id_)
        mock_create_new_media_filter_data_entry.assert_called_once_with(expected_media_filter_data)

    def test_on_new_video_upload(
        self,
        fxt_video_entity,
        fxt_ote_id,
    ) -> None:
        # Arrange
        workspace_id = fxt_ote_id(1)
        project_id = fxt_ote_id(2)
        dataset_storage_id = fxt_ote_id(3)
        expected_media_filter_data = DatasetStorageFilterData(
            media_identifier=fxt_video_entity.media_identifier,
            media_filter_data=MediaFilterData(
                media_name=fxt_video_entity.name,
                media_extension=fxt_video_entity.extension,
                media_width=fxt_video_entity.width,
                media_height=fxt_video_entity.height,
                upload_date=fxt_video_entity.creation_date,
                uploader_id=fxt_video_entity.uploader_id,
                size=fxt_video_entity.size,
                video_filter_data=VideoFilterData(
                    frame_stride=fxt_video_entity.stride,
                    frame_count=fxt_video_entity.total_frames,
                    frame_rate=fxt_video_entity.fps,
                    duration=fxt_video_entity.duration,
                    unannotated_frames=fxt_video_entity.total_frames,
                ),
            ),
            preprocessing=MediaPreprocessingStatus.FINISHED,
        )

        with (
            patch.object(
                VideoRepo,
                "get_by_id",
                return_value=fxt_video_entity,
            ) as mock_get_video,
            patch.object(
                DatasetStorageFilterRepo,
                "upsert_dataset_storage_filter_data",
                return_value=None,
            ) as mock_create_new_media_filter_data_entry,
        ):
            # Act
            DatasetStorageFilterService.on_new_media_upload(
                workspace_id=workspace_id,
                project_id=project_id,
                dataset_storage_id=dataset_storage_id,
                media_id=fxt_video_entity.id_,
                media_type=MediaType.VIDEO,
            )

        # Assert
        mock_get_video.assert_called_once_with(id_=fxt_video_entity.id_)
        mock_create_new_media_filter_data_entry.assert_called_once_with(expected_media_filter_data)

    @pytest.mark.parametrize(
        "media_type",
        [
            MediaType.IMAGE,
            MediaType.VIDEO_FRAME,
        ],
    )
    def test_on_new_annotation_scene(
        self,
        media_type,
        fxt_annotation_scene,
        fxt_annotation_scene_state,
        fxt_video_entity,
        fxt_ote_id,
    ) -> None:
        # Arrange
        media_id = fxt_annotation_scene.media_identifier.media_id
        media_identifier: MediaIdentifierEntity
        if media_type is MediaType.IMAGE:
            media_identifier = ImageIdentifier(image_id=media_id)
        else:
            media_identifier = VideoFrameIdentifier(video_id=media_id, frame_index=1)
        fxt_annotation_scene.media_identifier = media_identifier
        fxt_video_entity.id_ = media_id

        fxt_ote_id(1)
        project_id = fxt_ote_id(2)
        dataset_storage_id = fxt_ote_id(3)
        expected_shapes = [
            ShapeFilterData(
                shape_type=shape.type,
                area_percentage=shape.get_area(),
                area_pixel=shape.get_area() * fxt_annotation_scene.media_width * fxt_annotation_scene.media_height,
            )
            for shape in fxt_annotation_scene.shapes
        ]
        expected_label_ids = sorted(fxt_annotation_scene.get_label_ids(include_empty=True))
        expected_media_filter_data = MediaFilterData(
            media_name=fxt_video_entity.name,
            media_extension=fxt_video_entity.extension,
            media_height=fxt_video_entity.height,
            media_width=fxt_video_entity.width,
            upload_date=fxt_video_entity.creation_date,
            uploader_id=fxt_video_entity.uploader_id,
            size=fxt_video_entity.size,
        )
        expected_annotation_scene_filter_data = AnnotationSceneFilterData(
            annotation_scene_id=fxt_annotation_scene.id_,
            user_name=fxt_annotation_scene.last_annotator_id,
            shapes=expected_shapes,
            label_ids=expected_label_ids,
            creation_date=fxt_annotation_scene.creation_date,
        )
        expected_dataset_storage_filter_data = DatasetStorageFilterData(
            media_identifier=fxt_annotation_scene.media_identifier,
            media_filter_data=expected_media_filter_data,
            annotation_scene_filter_data=expected_annotation_scene_filter_data,
            media_annotation_state=fxt_annotation_scene_state.get_state_media_level(),
            preprocessing=MediaPreprocessingStatus.FINISHED,
        )

        with (
            patch.object(
                AnnotationSceneRepo,
                "get_by_id",
                return_value=fxt_annotation_scene,
            ) as mock_get_annotation_scene,
            patch.object(
                AnnotationSceneStateRepo,
                "get_latest_for_annotation_scene",
                return_value=fxt_annotation_scene_state,
            ) as mock_get_annotation_scene_state,
            patch.object(
                DatasetStorageFilterRepo,
                "upsert_dataset_storage_filter_data",
                return_value=None,
            ) as mock_save_data,
            patch.object(
                VideoRepo,
                "get_by_id",
                return_value=fxt_video_entity,
            ) as mock_get_video,
        ):
            # Act
            DatasetStorageFilterService.on_new_annotation_scene(
                project_id=project_id,
                dataset_storage_id=dataset_storage_id,
                annotation_scene_id=fxt_annotation_scene.id_,
            )

        # Assert
        mock_get_annotation_scene.assert_called_once_with(id_=fxt_annotation_scene.id_)
        mock_get_annotation_scene_state.assert_called_once_with(annotation_scene_id=fxt_annotation_scene.id_)
        mock_save_data.assert_called_once_with(expected_dataset_storage_filter_data)

        if media_type is MediaType.VIDEO_FRAME:
            mock_get_video.assert_called_once_with(media_id)
        else:
            mock_get_video.assert_not_called()
