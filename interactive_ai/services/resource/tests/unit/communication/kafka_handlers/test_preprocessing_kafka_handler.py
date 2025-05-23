# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from datetime import datetime
from unittest.mock import patch

import pytest

from communication.kafka_handlers.preprocessing_kafka_handler import PreprocessingKafkaHandler
from usecases.media_preprocessing_status_usecase import MediaPreprocessingStatusUseCase

from geti_kafka_tools import KafkaRawMessage
from geti_types import ID
from iai_core.entities.dataset_storage import DatasetStorageIdentifier

DATASET_STORAGE_ID: DatasetStorageIdentifier = DatasetStorageIdentifier(
    workspace_id=ID("63b183d00000000000000001"),
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
            ("IMAGE", "update_image_preprocessing_status"),
            ("VIDEO", "update_video_preprocessing_status"),
        ],
    )
    @patch.object(PreprocessingKafkaHandler, "__init__", new=mock_init)
    def test_on_media_preprocessing_another_event(self, media_type, update_method_name) -> None:
        # Arrange
        message: KafkaRawMessage = kafka_message(event="MEDIA_UPLOADED", media_type=media_type)

        # Act
        with patch.object(MediaPreprocessingStatusUseCase, update_method_name) as mock_update:
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
        with patch.object(
            MediaPreprocessingStatusUseCase, "update_image_preprocessing_status"
        ) as mock_update_image_preprocessing_status:
            PreprocessingKafkaHandler().on_media_preprocessing(message)

        # Assert
        mock_update_image_preprocessing_status.assert_called_once_with(
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
        with patch.object(
            MediaPreprocessingStatusUseCase, "update_video_preprocessing_status"
        ) as mock_update_video_preprocessing_status:
            PreprocessingKafkaHandler().on_media_preprocessing(message)

        # Assert
        mock_update_video_preprocessing_status.assert_called_once_with(
            dataset_storage_identifier=DATASET_STORAGE_ID,
            video_id=ID("media_id"),
            event=event,
            preprocessing=preprocessing,
        )
