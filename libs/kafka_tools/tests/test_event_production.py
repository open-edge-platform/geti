import os
from unittest.mock import ANY, MagicMock, patch

import confluent_kafka
import pytest

from geti_kafka_tools.event_production import EventProducer, _body_for_logger, json_string_serializer, publish_event


def reset_singleton():
    EventProducer._instance = None


class TestJsonStringSerializer:
    def test_json_string_serializer(self) -> None:
        # Arrange
        body = {"foo": "bar"}

        # Act
        serialized_body = json_string_serializer(body)

        # Assert
        assert serialized_body == b'{"foo": "bar"}'


class TestEventProducer:
    @pytest.fixture
    def fxt_producer(self):
        orig_producer = confluent_kafka.Producer
        fxt_producer = MagicMock(spec=confluent_kafka.Producer)
        confluent_kafka.Producer = fxt_producer
        yield fxt_producer
        confluent_kafka.Producer = orig_producer

    def test_event_producer_initialize(self, fxt_producer) -> None:
        # Arrange

        # Act
        EventProducer._create_producer()

        # Assert
        fxt_producer.assert_called_once_with(
            {
                "bootstrap.servers": "localhost:9092",
                "batch.size": 100000,
                "linger.ms": 10,
                "compression.type": "snappy",
                "acks": 1,
            }
        )

    @patch.dict(os.environ, {"KAFKA_ADDRESS": "non_default_kafka_address"})
    def test_event_producer_initialize_address(self, fxt_producer) -> None:
        # Arrange

        # Act
        EventProducer._create_producer()

        # Assert
        fxt_producer.assert_called_once_with(
            {
                "bootstrap.servers": "non_default_kafka_address",
                "batch.size": 100000,
                "linger.ms": 10,
                "compression.type": "snappy",
                "acks": 1,
            }
        )

    @patch.dict(os.environ, {"KAFKA_USERNAME": "username"})
    @patch.dict(os.environ, {"KAFKA_PASSWORD": "password"})
    @patch.dict(os.environ, {"KAFKA_SECURITY_PROTOCOL": "SASL_PLAINTEXT"})
    @patch.dict(os.environ, {"KAFKA_SASL_MECHANISM": "sasl_mechanism"})
    def test_event_producer_initialize_security_enabled(self, fxt_producer) -> None:
        # Arrange

        # Act
        EventProducer._create_producer()

        # Assert
        fxt_producer.assert_called_once_with(
            {
                "bootstrap.servers": "localhost:9092",
                "batch.size": 100000,
                "linger.ms": 10,
                "compression.type": "snappy",
                "acks": 1,
                "security.protocol": "SASL_PLAINTEXT",
                "sasl.mechanism": "sasl_mechanism",
                "sasl.username": "username",
                "sasl.password": "password",
            }
        )

    def test_event_producer_publish(self, fxt_producer, request) -> None:
        request.addfinalizer(lambda: reset_singleton())
        # Arrange
        event_producer = EventProducer()

        # Act
        event_producer.publish(
            topic="topic", body={"foo": "bar"}, key=b"event_key", headers=[("foo_header", b"bar_header")]
        )

        # Assert
        fxt_producer.assert_called_once()
        event_producer._producer.produce.assert_called_once_with(
            topic="topic",
            value=b'{"foo": "bar"}',
            key=b"event_key",
            headers=[("foo_header", b"bar_header")],
            on_delivery=ANY,
        )
        event_producer._producer.poll.assert_called_once_with(0)

    @patch.dict(os.environ, {"KAFKA_TOPIC_PREFIX": "test_prefix_"})
    def test_event_producer_publish_prefix(self, fxt_producer, request) -> None:
        request.addfinalizer(lambda: reset_singleton())
        # Arrange
        event_producer = EventProducer()

        # Act
        event_producer.publish(
            topic="topic", body={"foo": "bar"}, key=b"event_key", headers=[("foo_header", b"bar_header")]
        )

        # Assert
        fxt_producer.assert_called_once()
        event_producer._producer.produce.assert_called_once_with(
            topic="test_prefix_topic",
            value=b'{"foo": "bar"}',
            key=b"event_key",
            headers=[("foo_header", b"bar_header")],
            on_delivery=ANY,
        )
        event_producer._producer.poll.assert_called_once_with(0)


class TestEventProduction:
    def test_body_for_logger(
        self,
    ) -> None:
        # Arrange
        body = {"key": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]}

        # Act
        body_for_logger = _body_for_logger(body)

        # Assert
        assert body_for_logger["key"] == [
            0,
            1,
            2,
            3,
            4,
            5,
            6,
            7,
            8,
            9,
            "... 11 items in total.",
        ]
        assert body == {"key": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]}

    @patch("geti_kafka_tools.event_production.EventProducer", autospec=True)
    def test_publish_event_no_headers(self, mock_event_producer) -> None:
        # Arrange
        producer = MagicMock()
        mock_event_producer.return_value = producer

        # Act
        publish_event(topic="topic", body={"foo": "bar"}, key=b"event_key")

        # Assert
        mock_event_producer.assert_called_once_with()
        producer.publish.assert_called_once_with(topic="topic", body={"foo": "bar"}, key=b"event_key", headers=None)

    @patch("geti_kafka_tools.event_production.EventProducer", autospec=True)
    def test_publish_event(self, mock_event_producer) -> None:
        # Arrange
        producer = MagicMock()
        mock_event_producer.return_value = producer

        # Act
        headers_getter = MagicMock()
        headers_getter.return_value = [("foo_header", b"bar_header")]
        publish_event(topic="topic", body={"foo": "bar"}, key=b"event_key", headers_getter=headers_getter)

        # Assert
        mock_event_producer.assert_called_once_with()
        headers_getter.assert_called_once_with()
        producer.publish.assert_called_once_with(
            topic="topic", body={"foo": "bar"}, key=b"event_key", headers=[("foo_header", b"bar_header")]
        )
