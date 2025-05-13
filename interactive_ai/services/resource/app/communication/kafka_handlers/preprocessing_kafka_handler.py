# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import logging
from typing import Any

from geti_kafka_tools import BaseKafkaHandler, KafkaRawMessage, TopicSubscription
from geti_types import ID, Singleton
from iai_core.entities.dataset_storage import DatasetStorageIdentifier
from iai_core.entities.image import Image
from iai_core.entities.video import Video
from iai_core.repos import ImageRepo, VideoRepo
from iai_core.repos.dataset_storage_filter_repo import DatasetStorageFilterRepo
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
            workspace_id=ID(value["workspace_id"]),
            project_id=ID(value["project_id"]),
            dataset_storage_id=ID(value["dataset_storage_id"]),
        )

        if event in ("MEDIA_PREPROCESSING_STARTED", "MEDIA_PREPROCESSING_FINISHED"):
            try:
                media_id = ID(value["media_id"])
                media_type = value["media_type"]

                if media_type == "IMAGE":
                    PreprocessingKafkaHandler.update_image(
                        dataset_storage_identifier=dataset_storage_identifier,
                        image_id=media_id,
                        event=event,
                        preprocessing=value.get("preprocessing"),
                    )
                else:
                    PreprocessingKafkaHandler.update_video(
                        dataset_storage_identifier=dataset_storage_identifier,
                        video_id=media_id,
                        event=event,
                        preprocessing=value.get("preprocessing"),
                    )
            except Exception as ex:
                logger.error(f"Failed to handle {event} preprocessing event, reason = {ex}")

    @staticmethod
    def _update_preprocessing(media: Image | Video, event: str, preprocessing: dict[str, Any] | None) -> None:
        if event == "MEDIA_PREPROCESSING_STARTED":
            media.preprocessing.started()
        elif preprocessing is not None and preprocessing["success"]:
            media.preprocessing.finished()
        elif preprocessing is not None:
            media.preprocessing.failed(preprocessing.get("message", ""))

    @staticmethod
    def update_image(
        dataset_storage_identifier: DatasetStorageIdentifier,
        image_id: ID,
        event: str,
        preprocessing: dict | None,
    ) -> None:
        image_repo = ImageRepo(dataset_storage_identifier=dataset_storage_identifier)
        image = image_repo.get_by_id(image_id)
        PreprocessingKafkaHandler._update_preprocessing(media=image, event=event, preprocessing=preprocessing)
        image_repo.save(image)

        DatasetStorageFilterRepo(dataset_storage_identifier=dataset_storage_identifier).update_preprocessing_status(
            media_identifier=image.media_identifier,
            status=image.preprocessing.status,
        )

    @staticmethod
    def update_video(
        dataset_storage_identifier: DatasetStorageIdentifier,
        video_id: ID,
        event: str,
        preprocessing: dict | None,
    ) -> None:
        video_repo = VideoRepo(dataset_storage_identifier=dataset_storage_identifier)
        video = video_repo.get_by_id(video_id)
        PreprocessingKafkaHandler._update_preprocessing(media=video, event=event, preprocessing=preprocessing)
        video_repo.save(video)

        DatasetStorageFilterRepo(dataset_storage_identifier=dataset_storage_identifier).update_preprocessing_status(
            media_identifier=video.media_identifier,
            status=video.preprocessing.status,
        )
