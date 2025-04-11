import logging
import threading
from collections.abc import Callable
from json import dumps

# Producer shouldn't be imported here, because ConfluentKafkaInstrumentor replaces it with its implementation in runtime
import confluent_kafka

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


def json_string_serializer(body: dict) -> bytes:
    """
    Kafka event value serializer. Converts dict to JSON and transform to bytes
    :param body: body dict
    :return: serialized JSON value
    """
    return dumps(body).encode("utf-8")


class EventProducer:
    _instance = None
    _lock = threading.Lock()

    def __new__(
        cls, serializer: Callable[[dict], str | bytes] = json_string_serializer
    ):  # singleton with double-checked locking
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    new_instance = super().__new__(cls)
                    new_instance.__initialize(serializer)
                    cls._instance = new_instance
        return cls._instance

    def __initialize(self, serializer: Callable[[dict], str | bytes]) -> None:
        self._serializer = serializer
        self._producer = self._create_producer()
        self._topic_prefix = kafka_topic_prefix()

    @staticmethod
    def _create_producer() -> confluent_kafka.Producer:
        """
        Create a kafka producer.
        :return: Producer if succeeded
        """
        config = {
            "bootstrap.servers": kafka_bootstrap_endpoints(),
            "batch.size": 100000,
            "linger.ms": 10,
            "compression.type": "snappy",
            "acks": 1,
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

        return confluent_kafka.Producer(config)

    @staticmethod
    def delivery_callback(err: str | None, msg: str) -> None:
        """Delivery report callback called by poll() on successful or failed delivery"""
        if err is not None:
            logger.error("Error occurred while delivering Kafka message: %s", err)
        else:
            logger.debug("Kafka message has been delivered: %s", msg)

    def publish(
        self, topic: str, body: dict, key: bytes | None = None, headers: list[tuple[str, bytes]] | None = None
    ) -> None:
        """
        Publishes an event via Kafka.

        :param topic: string used as a key to identify the topic where the event
            will be published in
        :param body: A dictionary with the data that needs to be translated
        :param key: Key to send with the message
        :param headers: Headers to send with the message
        """
        prefixed_topic = f"{self._topic_prefix}{topic}"
        logger.debug("Preparing to submit Kafka message for topic '%s': %s", prefixed_topic, body)
        self._producer.produce(
            topic=prefixed_topic,
            value=self._serializer(body),
            key=key,
            headers=headers,
            on_delivery=EventProducer.delivery_callback,
        )
        self._producer.poll(0)

    def health_check(self) -> bool:
        # Todo: implement CVS-81113
        return True


def publish_event(
    topic: str,
    body: dict,
    key: bytes | None = None,
    headers_getter: Callable[[], list[tuple[str, bytes]]] | None = None,
) -> None:
    """
    Publishes an event via Kafka.

    :param topic: string used as a key to identify the topic where the event
        will be published in
    :param body: A dictionary with the data that needs to be translated
    :param key: Key to send with the message
    :param headers_getter: Callback function to get headers to send with the message
    """
    if not isinstance(body, dict):
        raise ValueError("Expected the body for a Kafka event to be of type dict")

    body_for_logger = _body_for_logger(body)

    headers = headers_getter() if headers_getter is not None else None

    logger.info(f"Publishing Kafka event in topic {topic} : {body_for_logger}")
    EventProducer().publish(topic=topic, body=body, key=key, headers=headers)


def _body_for_logger(body: dict) -> dict:
    """
    Prepares an event body for logging. Strips any list that is longer than 10 items and adds total item length
    """
    body_for_logger = body.copy()
    for key, value in body_for_logger.items():
        if isinstance(value, list) and len(value) > 10:
            body_for_logger[key] = value[:10] + [f"... {len(value)} items in total."]
    return body_for_logger
