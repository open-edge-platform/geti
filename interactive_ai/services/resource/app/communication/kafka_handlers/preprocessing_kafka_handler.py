# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import logging

from usecases.media_preprocessing_status_usecase import MediaPreprocessingStatusUseCase

from geti_kafka_tools import BaseKafkaHandler, KafkaRawMessage, TopicSubscription
from geti_types import CTX_SESSION_VAR, ID, Singleton
from iai_core.entities.dataset_storage import DatasetStorageIdentifier
from iai_core.session.session_propagation import setup_session_kafka

logger = logging.getLogger(__name__)


class PreprocessingKafkaHandler(BaseKafkaHandler, metaclass=Singleton):
    """
    This class handles media preprocessing Kafka events (MEDIA_PREPROCESSING_STARTED and MEDIA_PREPROCESSING_FINISHED)
    for the resource MS.
    """

    def __init__(self) -> None:
        super().__init__(group_id="preprocessing_consumer")

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
        dataset_storage_identifier = DatasetStorageIdentifier(
            workspace_id=CTX_SESSION_VAR.get().workspace_id,
            project_id=ID(value["project_id"]),
            dataset_storage_id=ID(value["dataset_storage_id"]),
        )
        if event not in ("MEDIA_PREPROCESSING_STARTED", "MEDIA_PREPROCESSING_FINISHED"):
            return

        try:
            media_id = ID(value["media_id"])
            media_type = value["media_type"]

            if media_type == "IMAGE":
                MediaPreprocessingStatusUseCase.update_image_preprocessing_status(
                    dataset_storage_identifier=dataset_storage_identifier,
                    image_id=media_id,
                    event=event,
                    preprocessing=value.get("preprocessing"),
                )
            else:
                MediaPreprocessingStatusUseCase.update_video_preprocessing_status(
                    dataset_storage_identifier=dataset_storage_identifier,
                    video_id=media_id,
                    event=event,
                    preprocessing=value.get("preprocessing"),
                )
        except Exception as ex:
            logger.error(f"Failed to handle {event} preprocessing event, reason = {ex}")
