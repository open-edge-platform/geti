"""This module defines classes and interfaces to consume Kafka events"""

import logging
import signal
import threading
from abc import ABCMeta, abstractmethod
from collections.abc import Callable, Sequence
from json import loads
from types import FrameType
from typing import Any, NamedTuple

# Consumer shouldn't be imported here, because ConfluentKafkaInstrumentor replaces it with its implementation in runtime
import confluent_kafka
from confluent_kafka import Message

from .exceptions import TopicAlreadySubscribedException, TopicNotSubscribedException
from .utils import (
    kafka_bootstrap_endpoints,
    kafka_password,
    kafka_sasl_mechanism,
    kafka_security_enabled,
    kafka_security_protocol,
    kafka_topic_prefix,
    kafka_username,
)

logger = logging.getLogger(__name__)


class KafkaRawMessage(NamedTuple):
    topic: str
    partition: int
    offset: int
    timestamp: int
    timestamp_type: int
    key: str | bytes | None
    value: Any | None
    headers: Sequence[tuple[str, bytes]]


CallbackT = Callable[[KafkaRawMessage], None]
# same as CallbackT but with self argument
CallbackMethodT = Callable[[Any, KafkaRawMessage], None]

Deserializer = Callable[[str | bytes | None], Any | None]


class TopicSubscription(NamedTuple):
    topic: str
    callback: CallbackT
    deserializer: Deserializer | None = None


def json_deserializer(value: str | bytes | None) -> dict | None:
    """
    Kafka event value JSON deserializer.
    :param value: raw Kafka event value
    :return: deserialized JSON value
    """
    if value is None:
        return None
    value_string = value if isinstance(value, str) else value.decode("utf-8")
    return loads(value_string)


class KafkaEventConsumer:
    def __init__(self, group_id: str, deserializer: Deserializer = json_deserializer) -> None:
        """
        KafkaEventConsumer is responsible to receive Kafka events on the subscribed
        topics and consume them, calling the appropriate callbacks.

        :param group_id: unique id for the Consumer. Recommended to name it along
        the lines of "{microservice_name}_consumer".
        :param deserializer: function to deserialize Kafka event value, applies by default to all
        subscribed topics if no deserializer defined, by default json_string_deserializer
        """
        self.group_id = group_id
        self._deserializer = deserializer

        self._topic_to_callback: dict[str, CallbackT] = {}
        self._topic_to_deserializer: dict[str, Deserializer] = {}
        self._should_stop = False

        logger.info(f"Creating Kafka consumer ({group_id}).")
        self._consumer = self._create_consumer(group_id=group_id)

        self._topic_prefix = kafka_topic_prefix()

        signal.signal(signal.SIGINT, self.__signal)  # type: ignore
        signal.signal(signal.SIGQUIT, self.__signal)  # type: ignore

        self._start_consume_thread()

    @staticmethod
    def _create_consumer(group_id: str) -> confluent_kafka.Consumer:
        """
        Create a kafka consumer.

        :param group_id: Group id for the Consumer
        :return: Consumer if succeeded
        """
        config = {
            "bootstrap.servers": kafka_bootstrap_endpoints(),
            "group.id": group_id,
            "enable.auto.commit": False,
            "max.poll.interval.ms": 900000,
            "connections.max.idle.ms": 910000,
        }
        if kafka_security_enabled():
            config.update(
                {
                    "security.protocol": kafka_security_protocol(),
                    "sasl.mechanism": kafka_sasl_mechanism(),
                    "sasl.username": kafka_username(),
                    "sasl.password": kafka_password(),
                }
            )

        return confluent_kafka.Consumer(config)

    def _start_consume_thread(self) -> None:
        logger.info("Starting Kafka consumer thread")
        self._consumer_thread = threading.Thread(target=self._consume, args=(), name="Kafka consumer thread")
        self._consumer_thread.start()

    @staticmethod
    def is_connected() -> bool:
        """
        Returns connection state of consumer
        """
        # Todo: Check connectivity CVS-81113
        return True

    def subscribe(
        self,
        topics_subscriptions: list[TopicSubscription],
        on_assign: Callable[[], None],
    ) -> None:
        """
        Subscribe to topics and install callbacks that will be executed when
        a message is received on that topics.

        Note: a callback is blocking and prevents other events to be processed.

        :param topics_subscriptions: list of topics to subscribe to with callbacks and custom deserializers
        :param on_assign: a callback function to be invoked when consumer is successfully subscribed to the topics
        :raises: TopicAlreadySubscribedException if the consumer is already
            subscribed to any of the given topics
        """
        _topic_to_callback = {}
        _topic_to_deserializer = {}
        for topics_subscription in topics_subscriptions:
            prefixed_topic = f"{self._topic_prefix}{topics_subscription.topic}"
            if prefixed_topic in self._topic_to_callback:
                raise TopicAlreadySubscribedException(prefixed_topic)

            _topic_to_callback[prefixed_topic] = topics_subscription.callback
            if topics_subscription.deserializer is not None:
                _topic_to_deserializer[prefixed_topic] = topics_subscription.deserializer

        self._topic_to_callback = self._topic_to_callback | _topic_to_callback
        self._topic_to_deserializer = self._topic_to_deserializer | _topic_to_deserializer

        topics_names = list(self._topic_to_callback.keys())
        logger.info(
            "Kafka event consumer with group ID `%s` subscribing to topics `%s`",
            self.group_id,
            topics_names,
        )
        self._consumer.subscribe(topics=topics_names, on_assign=lambda consumer, partitions: on_assign())  # noqa: ARG005

    def unsubscribe(
        self,
        topic: str,
        on_assign: Callable[[], None] | None = None,
    ) -> None:
        """
        Unsubscribe from a topic and remove the associated callback.

        :param topic: Name of the topic
        :param on_assign: a callback function to be invoked when consumer is successfully unsubscribed from the topics
        and subscribed back to remaining ones
        :raises: InvalidTopicUnsubscribeException if the consumer is not already
            subscribed to the given topic
        """
        prefixed_topic = f"{self._topic_prefix}{topic}"
        logger.info(
            "Kafka event consumer with group ID `%s` unsubscribing from topic `%s`",
            self.group_id,
            prefixed_topic,
        )

        if prefixed_topic not in self._topic_to_callback:
            raise TopicNotSubscribedException(prefixed_topic)

        self._topic_to_callback.pop(prefixed_topic, None)
        self._topic_to_deserializer.pop(prefixed_topic, None)

        self._consumer.unsubscribe()
        self._consumer.subscribe(topics=list(self._topic_to_callback.keys()), on_assign=on_assign)

    def _consume(self) -> None:
        """
        Runs a message polling loop. Each iteration of the loop
        :func:`~geti_kafka_tools.event_consuming.KafkaEventConsumer._poll_and_consume_message` is being invoked.
        Loop stops if _should_stop flag is triggered.
        """
        while True:
            if self._should_stop:
                break
            self._poll_and_consume_message()

    def _poll_and_consume_message(self) -> None:
        """
        Polls next message from the consumer. If message is available, then instantiates telemetry context
        and calls :func:`~geti_kafka_tools.event_consuming.KafkaEventConsumer._consume_message`.
        If message has been processed successfully, commits the offset to broker.
        Detaches telemetry context afterwards.
        """
        try:
            message: Message = self._consumer.poll(timeout=1.0)
            if not isinstance(message, Message):
                # Timeout condition
                return

            if message.error():
                logger.warning(f"Error occurred polling for a message {message.error()}")
                return

            self._consume_message(message)
            self._consumer.commit()

        except Exception:
            logger.exception("Failed to consume an event (group_id `%s`)", self.group_id)

    def _deserialize_message_value(self, topic: str, value: str | bytes | None) -> Any | None:
        """
        Deserializes event value.
        Uses either deserializer registered for specific topic, or general consumer deserializer.
        :param topic: Name of the topic
        :param value: event raw value
        :return: deserialized event value
        """
        return self._topic_to_deserializer.get(topic, self._deserializer)(value)

    def _consume_message(self, message: Message) -> None:
        """
        Processes Kafka event. Deserializes event value, builds KafkaRawMessage instance and invokes a callback
        registered for the event topic.
        :param message: Kafka event
        :raises: RuntimeError if the callback cannot be found for the topic
        """
        topic = message.topic()

        deserialized_value = self._deserialize_message_value(topic=topic, value=message.value())
        logger.info(
            "Kafka event received (group_id: `%s`, topic: `%s`, partition: `%s`, offset: `%s`, value `%s`)",
            self.group_id,
            topic,
            message.partition(),
            message.offset(),
            str(deserialized_value)[:1000],
        )

        # Execute the callback
        callback: CallbackT | None = self._topic_to_callback.get(topic)
        if callback is not None:
            raw_message = KafkaRawMessage(
                topic=message.topic(),
                partition=message.partition(),
                offset=message.offset(),
                timestamp_type=message.timestamp()[0],
                timestamp=message.timestamp()[1],
                key=message.key(),
                value=deserialized_value,
                headers=message.headers(),
            )
            callback(raw_message)
        else:
            raise RuntimeError(f"Callback not found for topic {topic}")

        logger.info(
            "Kafka event processed (group_id: `%s`, topic: `%s`, partition: `%s`, offset: `%s`)",
            self.group_id,
            topic,
            message.partition(),
            message.offset(),
        )

    def stop(self) -> None:
        """
        Stop the event consumer.
        """
        logger.info("Stopping Kafka event consumer with group_id `%s`", self.group_id)

        self._should_stop = True
        self._consumer_thread.join()
        self._consumer.close()

    def __signal(self, signum: int, frame: FrameType) -> None:  # noqa: ARG002
        """
        Process signals, in an attempt to close more gracefully.
        """
        self.stop()


class BaseKafkaHandler(metaclass=ABCMeta):
    """
    Base class to handle incoming Kafka events for microservices.

    :param group_id: The group id of the Kafka consumer
    """

    def __init__(self, group_id: str) -> None:
        self.group_id = group_id
        self.event_consumer = KafkaEventConsumer(group_id=group_id)
        self.subscribed = False
        self.__setup_events()

    def stop(self) -> None:
        """Stop the KafkaEventConsumer"""
        self.event_consumer.stop()

    @property
    @abstractmethod
    def topics_subscriptions(self) -> list[TopicSubscription]:
        """
        This property must be implemented in the child class and return a dictionary
        with the topic name as key and the callback function as value.
        """

    def _on_assign(self) -> None:
        logger.info(
            f"Kafka event consumer {self.group_id} successfully subscribed to topics and "
            "has been assigned with partitions"
        )
        self.subscribed = True

    def __setup_events(self) -> None:
        """Configure the topics to listen and the corresponding callback functions"""
        self.event_consumer.subscribe(self.topics_subscriptions, on_assign=self._on_assign)
