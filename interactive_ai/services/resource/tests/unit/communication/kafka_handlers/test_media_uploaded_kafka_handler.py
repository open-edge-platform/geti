# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from datetime import datetime
from unittest.mock import patch

import pytest

from communication.kafka_handlers.media_uploaded_kafka_handler import MediaUploadedKafkaHandler
from usecases.media_uploaded_usecase import MediaUploadedUseCase

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


def kafka_message(event: str, media_type: str | None = None) -> KafkaRawMessage:
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
        },
        [
            ("organization_id", b"000000000000000000000001"),
            ("workspace_id", b"63b183d00000000000000001"),
            ("mongodb_sharding_profile", b"NOT_SHARDED"),
            ("organization_location", b"IT-TR"),
            ("connected_instance_location", b"NL-GR"),
        ],
    )


class TestMediaUploadedKafkaHandler:
    @pytest.mark.parametrize("event", ["MEDIA_PREPROCESSING_STARTED", "MEDIA_PREPROCESSING_FINISHED"])
    @patch.object(MediaUploadedKafkaHandler, "__init__", new=mock_init)
    def test_on_media_preprocessing_another_event(self, event) -> None:
        # Arrange
        message: KafkaRawMessage = kafka_message(event=event)

        # Act
        with patch.object(MediaUploadedUseCase, "on_media_uploaded") as mock_on_media_uploaded:
            MediaUploadedKafkaHandler().on_media_preprocessing(message)

        # Assert
        mock_on_media_uploaded.assert_not_called()

    @pytest.mark.parametrize("media_type", ["IMAGE", "VIDEO"])
    @patch.object(MediaUploadedKafkaHandler, "__init__", new=mock_init)
    def test_on_media_preprocessing(self, media_type) -> None:
        # Arrange
        message: KafkaRawMessage = kafka_message(event="MEDIA_UPLOADED", media_type=media_type)

        # Act
        with patch.object(MediaUploadedUseCase, "on_media_uploaded") as mock_on_media_uploaded:
            MediaUploadedKafkaHandler().on_media_preprocessing(message)

        # Assert
        mock_on_media_uploaded.assert_called_once_with(
            dataset_storage_identifier=DATASET_STORAGE_ID,
            media_type=media_type,
            media_id=ID("media_id"),
            data_binary_filename="data_binary_filename",
        )
