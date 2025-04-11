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

from geti_kafka_tools import BaseKafkaHandler, KafkaRawMessage, TopicSubscription
from geti_types import ID, Singleton
from sc_sdk.services.dataset_storage_filter_service import DatasetStorageFilterService
from sc_sdk.session.session_propagation import setup_session_kafka

logger = logging.getLogger(__name__)


class AnnotationKafkaHandler(BaseKafkaHandler, metaclass=Singleton):
    """
    This class handles incoming annotation Kafka events for the resource MS.
    """

    def __init__(self) -> None:
        super().__init__(group_id="annotation_consumer")

    @property
    def topics_subscriptions(self) -> list[TopicSubscription]:
        return [
            TopicSubscription(topic="new_annotation_scene", callback=self.on_new_annotation_scene),
        ]

    @staticmethod
    @setup_session_kafka
    def on_new_annotation_scene(raw_message: KafkaRawMessage) -> None:
        """
        Updates the DatasetStorageFilterDataRepo with new data from the most recent
        annotation scene
        """
        value: dict = raw_message.value
        project_id = ID(value["project_id"])
        dataset_storage_id = ID(value["dataset_storage_id"])
        annotation_scene_id = ID(value["annotation_scene_id"])
        DatasetStorageFilterService.on_new_annotation_scene(
            project_id=project_id,
            dataset_storage_id=dataset_storage_id,
            annotation_scene_id=annotation_scene_id,
        )
