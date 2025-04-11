# INTEL CONFIDENTIAL
#
# Copyright (C) 2024 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and
# your use of them is governed by the express license under which they were provided to
# you ("License"). Unless the License provides otherwise, you may not use, modify, copy,
# publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is,
# with no express or implied warranties, other than those that are expressly stated
# in the License.
import logging

from resource_management.media_manager import MediaManager

from geti_kafka_tools import BaseKafkaHandler, KafkaRawMessage, TopicSubscription
from geti_types import ID, DatasetStorageIdentifier, Singleton
from sc_sdk.session.session_propagation import setup_session_kafka

logger = logging.getLogger(__name__)


class ThumbVideoKafkaHandler(BaseKafkaHandler, metaclass=Singleton):
    """
    This class handles thumbnail video incoming Kafka events for the resource MS.
    """

    def __init__(self) -> None:
        super().__init__(group_id="thumb_video_consumer")

    @property
    def topics_subscriptions(self) -> list[TopicSubscription]:
        return [
            TopicSubscription(topic="thumbnail_video_missing", callback=self.generate_and_save_thumbnail_video),
        ]

    @staticmethod
    @setup_session_kafka
    def generate_and_save_thumbnail_video(raw_message: KafkaRawMessage) -> None:
        """
        Generates a thumbnail video for a video
        """
        value: dict = raw_message.value
        dataset_storage_identifier = DatasetStorageIdentifier(
            workspace_id=ID(value["workspace_id"]),
            project_id=ID(value["project_id"]),
            dataset_storage_id=ID(value["dataset_storage_id"]),
        )
        video = MediaManager.get_video_by_id(
            dataset_storage_identifier=dataset_storage_identifier,
            video_id=ID(value["video_id"]),
        )
        logger.info(f"Creating thumbnail video for video with ID {video.id_}")
        MediaManager.create_and_save_thumbnail_video(dataset_storage_identifier=dataset_storage_identifier, video=video)
