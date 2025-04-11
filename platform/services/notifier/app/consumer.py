# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
Topic related functions
"""

import asyncio
import logging

from geti_kafka_tools import BaseKafkaHandler, KafkaRawMessage, TopicSubscription
from message import Message
from sender import send_message

from config import GETI_NOTIFICATION_TOPIC

logger = logging.getLogger(__name__)


class NotificationsHandler(BaseKafkaHandler):
    def __init__(self) -> None:
        super().__init__(group_id="notifier-consumer-group")
        self._event_loop = asyncio.new_event_loop()

    @property
    def topics_subscriptions(self) -> list[TopicSubscription]:
        return [
            TopicSubscription(topic=GETI_NOTIFICATION_TOPIC, callback=self.consume_notification),
        ]

    def consume_notification(self, raw_message: KafkaRawMessage) -> None:
        logger.debug("Trying to deserialize a message from Kafka")
        message = Message(raw_message.value)

        logger.debug("Message received from kafka")
        self._event_loop.run_until_complete(send_message(message))
