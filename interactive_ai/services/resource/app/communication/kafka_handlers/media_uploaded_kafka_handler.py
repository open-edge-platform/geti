# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import logging

from usecases.media_uploaded_usecase import MediaUploadedUseCase

from geti_kafka_tools import BaseKafkaHandler, KafkaRawMessage, TopicSubscription
from geti_types import CTX_SESSION_VAR, ID, Singleton
from iai_core.entities.dataset_storage import DatasetStorageIdentifier
from iai_core.session.session_propagation import setup_session_kafka

logger = logging.getLogger(__name__)


class MediaUploadedKafkaHandler(BaseKafkaHandler, metaclass=Singleton):
    """
    This class handles MEDIA_UPLOADED preprocessing Kafka events.
    TODO: ITEP-32599 extract to new microservice
    """

    def __init__(self) -> None:
        super().__init__(group_id="media_uploaded_consumer")

    @property
    def topics_subscriptions(self) -> list[TopicSubscription]:
        return [
            TopicSubscription(topic="media_preprocessing", callback=self.on_media_preprocessing),
        ]

    @staticmethod
    @setup_session_kafka
    def on_media_preprocessing(raw_message: KafkaRawMessage) -> None:
        value: dict = raw_message.value
        event = value["event"]
        if event != "MEDIA_UPLOADED":
            return

        dataset_storage_identifier = DatasetStorageIdentifier(
            workspace_id=CTX_SESSION_VAR.get().workspace_id,
            project_id=ID(value["project_id"]),
            dataset_storage_id=ID(value["dataset_storage_id"]),
        )
        MediaUploadedUseCase.on_media_uploaded(
            dataset_storage_identifier=dataset_storage_identifier,
            media_type=value["media_type"],
            media_id=ID(value["media_id"]),
            data_binary_filename=value["data_binary_filename"],
        )
