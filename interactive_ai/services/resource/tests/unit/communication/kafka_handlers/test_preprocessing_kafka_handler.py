# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from communication.kafka_handlers.preprocessing_kafka_handler import PreprocessingKafkaHandler

from geti_kafka_tools import KafkaRawMessage
from geti_types import ID
from iai_core.entities.dataset_storage import DatasetStorageIdentifier
from iai_core.entities.image import Image
from iai_core.entities.media import MediaPreprocessing, MediaPreprocessingStatus
from iai_core.entities.video import Video
from iai_core.repos import ImageRepo, VideoRepo
from iai_core.repos.dataset_storage_filter_repo import DatasetStorageFilterRepo

DATASET_STORAGE_ID: DatasetStorageIdentifier = DatasetStorageIdentifier(
    workspace_id=ID("workspace_id"),
    project_id=ID("project_id"),
    dataset_storage_id=ID("dataset_storage_id"),
)


def mock_init(self, *args, **kwargs) -> None:
    return None


def kafka_message(event: str, media_type: str | None = None, preprocessing: dict | None = None) -> KafkaRawMessage:
    return KafkaRawMessage(
        "media_preprocessing",
        0,
        0,
        int(datetime.now().timestamp()),
        0,
        b"media_id",
        {
            "event": event,
            "workspace_id": str(DATASET_STORAGE_ID.workspace_id),
            "project_id": str(DATASET_STORAGE_ID.project_id),
            "dataset_storage_id": str(DATASET_STORAGE_ID.dataset_storage_id),
            "media_type": media_type,
            "media_id": "media_id",
            "data_binary_filename": "data_binary_filename",
            "preprocessing": preprocessing,
        },
        [
            ("organization_id", b"000000000000000000000001"),
            ("workspace_id", b"63b183d00000000000000001"),
            ("mongodb_sharding_profile", b"NOT_SHARDED"),
            ("organization_location", b"IT-TR"),
            ("connected_instance_location", b"NL-GR"),
        ],
    )


class TestPreprocessingKafkaHandler:
    @pytest.mark.parametrize(
        "media_type, update_method_name",
        [
            ("IMAGE", "update_image"),
            ("VIDEO", "update_video"),
        ],
    )
    @patch.object(PreprocessingKafkaHandler, "__init__", new=mock_init)
    def test_on_media_preprocessing_another_event(self, media_type, update_method_name) -> None:
        # Arrange
        message: KafkaRawMessage = kafka_message(event="MEDIA_UPLOADED", media_type=media_type)

        # Act
        with patch.object(PreprocessingKafkaHandler, update_method_name) as mock_update:
            PreprocessingKafkaHandler().on_media_preprocessing(message)

        # Assert
        mock_update.assert_not_called()

    @pytest.mark.parametrize(
        "event, preprocessing",
        [
            ("MEDIA_PREPROCESSING_STARTED", None),
            ("MEDIA_PREPROCESSING_FINISHED", {"success": True}),
        ],
    )
    @patch.object(PreprocessingKafkaHandler, "__init__", new=mock_init)
    def test_on_image_preprocessing(self, event, preprocessing) -> None:
        # Arrange
        message: KafkaRawMessage = kafka_message(event=event, media_type="IMAGE", preprocessing=preprocessing)

        # Act
        with patch.object(PreprocessingKafkaHandler, "update_image") as mock_update_image:
            PreprocessingKafkaHandler().on_media_preprocessing(message)

        # Assert
        mock_update_image.assert_called_once_with(
            dataset_storage_identifier=DATASET_STORAGE_ID,
            image_id=ID("media_id"),
            event=event,
            preprocessing=preprocessing,
        )

    @pytest.mark.parametrize(
        "event, preprocessing",
        [
            ("MEDIA_PREPROCESSING_STARTED", None),
            ("MEDIA_PREPROCESSING_FINISHED", {"success": True}),
        ],
    )
    @patch.object(PreprocessingKafkaHandler, "__init__", new=mock_init)
    def test_on_video_preprocessing(self, event, preprocessing) -> None:
        # Arrange
        message: KafkaRawMessage = kafka_message(event=event, media_type="VIDEO", preprocessing=preprocessing)

        # Act
        with patch.object(PreprocessingKafkaHandler, "update_video") as mock_update_video:
            PreprocessingKafkaHandler().on_media_preprocessing(message)

        # Assert
        mock_update_video.assert_called_once_with(
            dataset_storage_identifier=DATASET_STORAGE_ID,
            video_id=ID("media_id"),
            event=event,
            preprocessing=preprocessing,
        )

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
    def test_update_image(self, event, status, preprocessing) -> None:
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
            PreprocessingKafkaHandler.update_image(
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
            PreprocessingKafkaHandler.update_video(
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
