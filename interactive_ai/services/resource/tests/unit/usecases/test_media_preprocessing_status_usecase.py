# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from unittest.mock import MagicMock, patch

import pytest

from communication.kafka_handlers.preprocessing_kafka_handler import PreprocessingKafkaHandler
from usecases.media_preprocessing_status_usecase import MediaPreprocessingStatusUseCase

from geti_types import ID
from iai_core.entities.dataset_storage import DatasetStorageIdentifier
from iai_core.entities.image import Image
from iai_core.entities.media import MediaPreprocessing, MediaPreprocessingStatus
from iai_core.entities.video import Video
from iai_core.repos import ImageRepo, VideoRepo
from iai_core.repos.dataset_storage_filter_repo import DatasetStorageFilterRepo

DATASET_STORAGE_ID: DatasetStorageIdentifier = DatasetStorageIdentifier(
    workspace_id=ID("63b183d00000000000000001"),
    project_id=ID("project_id"),
    dataset_storage_id=ID("dataset_storage_id"),
)


def mock_init(self, *args, **kwargs) -> None:
    return None


class TestMediaPreprocessingStatusUseCase:
    @pytest.mark.parametrize(
        "event, status, preprocessing",
        [
            ("MEDIA_PREPROCESSING_STARTED", MediaPreprocessingStatus.IN_PROGRESS, None),
            ("MEDIA_PREPROCESSING_FINISHED", MediaPreprocessingStatus.FINISHED, {"success": True}),
            (
                "MEDIA_PREPROCESSING_FINISHED",
                MediaPreprocessingStatus.FAILED,
                {"success": False, "message": "Failure message"},
            ),
        ],
    )
    @patch.object(DatasetStorageFilterRepo, "__init__", new=mock_init)
    @patch.object(ImageRepo, "__init__", new=mock_init)
    @patch.object(PreprocessingKafkaHandler, "__init__", new=mock_init)
    def test_update_image_preprocessing_status(self, event, status, preprocessing) -> None:
        # Arrange
        image_id = ID("image_id")
        image = MagicMock(spec=Image)
        image.preprocessing = MediaPreprocessing(status=MediaPreprocessingStatus.SCHEDULED)

        # Act
        with (
            patch.object(ImageRepo, "get_by_id", return_value=image) as mock_get_by_id,
            patch.object(ImageRepo, "save") as mock_save,
            patch.object(DatasetStorageFilterRepo, "update_preprocessing_status") as mock_update_preprocessing_status,
        ):
            MediaPreprocessingStatusUseCase.update_image_preprocessing_status(
                dataset_storage_identifier=DATASET_STORAGE_ID,
                image_id=image_id,
                event=event,
                preprocessing=preprocessing,
            )

        # Assert
        mock_get_by_id.assert_called_once_with(image_id)
        mock_save.assert_called_once_with(image)
        assert image.preprocessing.status == status
        if preprocessing and "message" in preprocessing:
            assert image.preprocessing.message == preprocessing["message"]
        mock_update_preprocessing_status.assert_called_once_with(media_id=image.id_, status=status)

    @pytest.mark.parametrize(
        "event, status, preprocessing",
        [
            ("MEDIA_PREPROCESSING_STARTED", MediaPreprocessingStatus.IN_PROGRESS, None),
            ("MEDIA_PREPROCESSING_FINISHED", MediaPreprocessingStatus.FINISHED, {"success": True}),
            (
                "MEDIA_PREPROCESSING_FINISHED",
                MediaPreprocessingStatus.FAILED,
                {"success": False, "message": "Failure message"},
            ),
        ],
    )
    @patch.object(DatasetStorageFilterRepo, "__init__", new=mock_init)
    @patch.object(VideoRepo, "__init__", new=mock_init)
    @patch.object(PreprocessingKafkaHandler, "__init__", new=mock_init)
    def test_update_video(self, event, status, preprocessing) -> None:
        # Arrange
        video_id = ID("video_id")
        video = MagicMock(spec=Video)
        video.preprocessing = MediaPreprocessing(status=MediaPreprocessingStatus.SCHEDULED)

        # Act
        with (
            patch.object(VideoRepo, "get_by_id", return_value=video) as mock_get_by_id,
            patch.object(VideoRepo, "save") as mock_save,
            patch.object(DatasetStorageFilterRepo, "update_preprocessing_status") as mock_update_preprocessing_status,
        ):
            MediaPreprocessingStatusUseCase.update_video_preprocessing_status(
                dataset_storage_identifier=DATASET_STORAGE_ID,
                video_id=video_id,
                event=event,
                preprocessing=preprocessing,
            )

        # Assert
        mock_get_by_id.assert_called_once_with(video_id)
        mock_save.assert_called_once_with(video)
        assert video.preprocessing.status == status
        if preprocessing and "message" in preprocessing:
            assert video.preprocessing.message == preprocessing["message"]
        mock_update_preprocessing_status.assert_called_once_with(media_id=video.id_, status=status)
