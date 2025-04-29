import datetime
import os
from json import JSONDecodeError
from unittest.mock import ANY, MagicMock, patch

import confluent_kafka
import pytest
from confluent_kafka import Message

from geti_kafka_tools import (
    KafkaEventConsumer,
    KafkaRawMessage,
    TopicAlreadySubscribedException,
    TopicNotSubscribedException,
    TopicSubscription,
)
from geti_kafka_tools.event_consuming import json_deserializer


class TestJsonStringDeserializer:
    @pytest.mark.parametrize(
        "body, expected_deserialized_body",
        [
            (None, None),
            ('{"foo": "bar"}', {"foo": "bar"}),
            (b'{"foo": "bar"}', {"foo": "bar"}),
        ],
    )
    def test_json_string_deserializer(self, body, expected_deserialized_body) -> None:
        # Arrange

        # Act
        deserialized_body = json_deserializer(body)

        # Assert
        assert deserialized_body == expected_deserialized_body

    @pytest.mark.parametrize("body", ["foobar", b"foobar", "", b""])
    def test_json_string_deserializer_invalid_json(self, body) -> None:
        # Arrange

        # Act
        with pytest.raises(JSONDecodeError):
            json_deserializer(body)

        # Assert


class TestKafkaEventConsumer:
    @pytest.fixture
    def fxt_consumer(self):
        orig_consumer = confluent_kafka.Consumer
        fxt_consumer = MagicMock(spec=confluent_kafka.Consumer)
        confluent_kafka.Consumer = fxt_consumer
        yield fxt_consumer
        confluent_kafka.Consumer = orig_consumer

    def test_kafka_event_consumer_create_consumer(self, fxt_consumer) -> None:
        # Arrange

        # Act
        KafkaEventConsumer._create_consumer("integration-test")

        # Assert
        fxt_consumer.assert_called_once_with(
            {
                "bootstrap.servers": "localhost:9092",
                "group.id": "integration-test",
                "enable.auto.commit": False,
                "max.poll.interval.ms": 900000,
                "connections.max.idle.ms": 910000,
            }
        )

    @patch.dict(os.environ, {"KAFKA_ADDRESS": "non_default_kafka_address"})
    def test_kafka_event_consumer_create_consumer_address(self, fxt_consumer) -> None:
        # Arrange

        # Act
        KafkaEventConsumer._create_consumer("integration-test")

        # Assert
        fxt_consumer.assert_called_once_with(
            {
                "bootstrap.servers": "non_default_kafka_address",
                "group.id": "integration-test",
                "enable.auto.commit": False,
                "max.poll.interval.ms": 900000,
                "connections.max.idle.ms": 910000,
            }
        )

    @patch.dict(os.environ, {"KAFKA_USERNAME": "username"})
    @patch.dict(os.environ, {"KAFKA_PASSWORD": "password"})
    @patch.dict(os.environ, {"KAFKA_SECURITY_PROTOCOL": "SASL_PLAINTEXT"})
    @patch.dict(os.environ, {"KAFKA_SASL_MECHANISM": "SCRAM-SHA-512"})
    def test_kafka_event_consumer_create_consumer_security_enabled(self, fxt_consumer) -> None:
        # Arrange

        # Act
        KafkaEventConsumer._create_consumer("integration-test")

        # Assert
        fxt_consumer.assert_called_once_with(
            {
                "bootstrap.servers": "localhost:9092",
                "group.id": "integration-test",
                "enable.auto.commit": False,
                "max.poll.interval.ms": 900000,
                "connections.max.idle.ms": 910000,
                "security.protocol": "SASL_PLAINTEXT",
                "sasl.mechanism": "SCRAM-SHA-512",
                "sasl.username": "username",
                "sasl.password": "password",
            }
        )

    @patch.object(KafkaEventConsumer, "_start_consume_thread")
    def test_kafka_event_consumer_subscribe(self, mock_start_consume_thread, fxt_consumer) -> None:
        # Arrange
        kafka_event_consumer = KafkaEventConsumer("integration-test")
        callback = MagicMock()
        deserializer = MagicMock()

        # Act
        kafka_event_consumer.subscribe(
            topics_subscriptions=[
                TopicSubscription(topic="topic1", callback=callback, deserializer=deserializer),
                TopicSubscription(topic="topic2", callback=callback, deserializer=deserializer),
            ],
            on_assign=MagicMock(),
        )

        # Assert
        fxt_consumer.assert_called_once()
        mock_start_consume_thread.assert_called_once()
        kafka_event_consumer._consumer.subscribe.assert_called_once_with(topics=["topic1", "topic2"], on_assign=ANY)

        assert kafka_event_consumer._topic_to_callback == {"topic1": callback, "topic2": callback}
        assert kafka_event_consumer._topic_to_deserializer == {"topic1": deserializer, "topic2": deserializer}

    @patch.dict(os.environ, {"KAFKA_TOPIC_PREFIX": "test_prefix_"})
    @patch.object(KafkaEventConsumer, "_start_consume_thread")
    def test_kafka_event_consumer_subscribe_prefix(self, mock_start_consume_thread, fxt_consumer) -> None:
        # Arrange
        kafka_event_consumer = KafkaEventConsumer("integration-test")
        callback = MagicMock()
        deserializer = MagicMock()

        # Act
        kafka_event_consumer.subscribe(
            topics_subscriptions=[
                TopicSubscription(topic="topic1", callback=callback, deserializer=deserializer),
                TopicSubscription(topic="topic2", callback=callback, deserializer=deserializer),
            ],
            on_assign=MagicMock(),
        )

        # Assert
        fxt_consumer.assert_called_once()
        mock_start_consume_thread.assert_called_once()
        kafka_event_consumer._consumer.subscribe.assert_called_once_with(
            topics=["test_prefix_topic1", "test_prefix_topic2"], on_assign=ANY
        )

        assert kafka_event_consumer._topic_to_callback == {
            "test_prefix_topic1": callback,
            "test_prefix_topic2": callback,
        }
        assert kafka_event_consumer._topic_to_deserializer == {
            "test_prefix_topic1": deserializer,
            "test_prefix_topic2": deserializer,
        }

    @patch.object(KafkaEventConsumer, "_start_consume_thread")
    def test_kafka_event_consumer_subscribe_already_subscribed(self, mock_start_consume_thread, fxt_consumer) -> None:
        # Arrange
        kafka_event_consumer = KafkaEventConsumer("integration-test")
        registered_callback = MagicMock()
        callback = MagicMock()
        deserializer = MagicMock()

        kafka_event_consumer._topic_to_callback = {"topic1": registered_callback}

        # Act
        with pytest.raises(TopicAlreadySubscribedException):
            kafka_event_consumer.subscribe(
                topics_subscriptions=[
                    TopicSubscription(topic="topic1", callback=callback, deserializer=deserializer),
                    TopicSubscription(topic="topic2", callback=callback, deserializer=deserializer),
                ],
                on_assign=MagicMock(),
            )

        # Assert
        fxt_consumer.assert_called_once()
        mock_start_consume_thread.assert_called_once()
        kafka_event_consumer._consumer.subscribe.assert_not_called()

        assert kafka_event_consumer._topic_to_callback == {"topic1": registered_callback}
        assert kafka_event_consumer._topic_to_deserializer == {}

    @patch.object(KafkaEventConsumer, "_start_consume_thread")
    def test_kafka_event_consumer_unsubscribe(self, mock_start_consume_thread, fxt_consumer) -> None:
        # Arrange
        kafka_event_consumer = KafkaEventConsumer("integration-test")
        registered_callback = MagicMock()

        kafka_event_consumer._topic_to_callback = {"topic1": registered_callback, "topic2": registered_callback}

        # Act
        kafka_event_consumer.unsubscribe("topic1")

        # Assert
        fxt_consumer.assert_called_once()
        mock_start_consume_thread.assert_called_once()
        kafka_event_consumer._consumer.unsubscribe.assert_called_once_with()
        kafka_event_consumer._consumer.subscribe.assert_called_once_with(topics=["topic2"], on_assign=ANY)

        assert kafka_event_consumer._topic_to_callback == {"topic2": registered_callback}
        assert kafka_event_consumer._topic_to_deserializer == {}

    @patch.object(KafkaEventConsumer, "_start_consume_thread")
    def test_kafka_event_consumer_unsubscribe_not_subscribed(self, mock_start_consume_thread, fxt_consumer) -> None:
        # Arrange
        kafka_event_consumer = KafkaEventConsumer("integration-test")
        registered_callback = MagicMock()

        kafka_event_consumer._topic_to_callback = {"topic2": registered_callback}

        # Act
        with pytest.raises(TopicNotSubscribedException):
            kafka_event_consumer.unsubscribe("topic1")

        # Assert
        fxt_consumer.assert_called_once()
        mock_start_consume_thread.assert_called_once()
        kafka_event_consumer._consumer.unsubscribe.assert_not_called()
        kafka_event_consumer._consumer.subscribe.assert_not_called()

        assert kafka_event_consumer._topic_to_callback == {"topic2": registered_callback}
        assert kafka_event_consumer._topic_to_deserializer == {}

    @patch.object(KafkaEventConsumer, "_start_consume_thread")
    def test_kafka_event_consumer_deserialize_message_value_default_deserializer(
        self, mock_start_consume_thread, fxt_consumer
    ) -> None:
        # Arrange
        kafka_event_consumer = KafkaEventConsumer("integration-test")
        kafka_event_consumer._consumer_thread = MagicMock()
        kafka_event_consumer._deserializer = MagicMock()

        value = b'{"foo": "bar"}'
        deserialized_value = {"foo": "bar"}

        kafka_event_consumer._deserializer.return_value = deserialized_value

        # Act
        result = kafka_event_consumer._deserialize_message_value(topic="test_topic", value=value)

        # Assert
        fxt_consumer.assert_called_once()
        mock_start_consume_thread.assert_called_once()
        kafka_event_consumer._deserializer.assert_called_once_with(value)
        assert result == deserialized_value

    @patch.object(KafkaEventConsumer, "_start_consume_thread")
    def test_kafka_event_consumer_deserialize_message_value_topic_deserializer(
        self, mock_start_consume_thread, fxt_consumer
    ) -> None:
        # Arrange
        kafka_event_consumer = KafkaEventConsumer("integration-test")
        kafka_event_consumer._consumer_thread = MagicMock()
        kafka_event_consumer._deserializer = MagicMock()

        topic_deserializer = MagicMock()
        kafka_event_consumer._topic_to_deserializer = {"test_topic": topic_deserializer}

        value = b'{"foo": "bar"}'
        deserialized_value = {"foo": "bar"}

        topic_deserializer.return_value = deserialized_value

        # Act
        result = kafka_event_consumer._deserialize_message_value(topic="test_topic", value=value)

        # Assert
        fxt_consumer.assert_called_once()
        mock_start_consume_thread.assert_called_once()
        kafka_event_consumer._deserializer.assert_not_called()
        topic_deserializer.assert_called_once_with(value)
        assert result == deserialized_value

    @patch.object(KafkaEventConsumer, "_start_consume_thread")
    def test_kafka_event_consumer_consume_message_no_callback(self, mock_start_consume_thread, fxt_consumer) -> None:
        # Arrange
        kafka_event_consumer = KafkaEventConsumer("integration-test")
        kafka_event_consumer._consumer_thread = MagicMock()

        message = MagicMock(spec=Message)
        message.topic.return_value = "test_topic"

        # Act
        with (
            patch.object(kafka_event_consumer, "_deserialize_message_value", return_value={"foo": "bar"}),
            pytest.raises(RuntimeError),
        ):
            kafka_event_consumer._consume_message(message)

        # Assert
        fxt_consumer.assert_called_once()
        mock_start_consume_thread.assert_called_once()

    @patch.object(KafkaEventConsumer, "_start_consume_thread")
    def test_kafka_event_consumer_consume_message(self, mock_start_consume_thread, fxt_consumer) -> None:
        # Arrange
        kafka_event_consumer = KafkaEventConsumer("integration-test")
        kafka_event_consumer._consumer_thread = MagicMock()

        message = MagicMock(spec=Message)
        message.topic.return_value = "test_topic"
        message.partition.return_value = 0
        message.offset.return_value = 0
        timestamp = int(datetime.datetime.now().timestamp())
        message.timestamp.return_value = (0, timestamp)
        message.key.return_value = b"event_key"
        message.headers.return_value = [("foo_header", b"bar_header")]

        callback = MagicMock()
        kafka_event_consumer._topic_to_callback = {"test_topic": callback}

        # Act
        with patch.object(kafka_event_consumer, "_deserialize_message_value", return_value={"foo": "bar"}):
            kafka_event_consumer._consume_message(message)

        # Assert
        fxt_consumer.assert_called_once()
        mock_start_consume_thread.assert_called_once()
        callback.assert_called_once_with(
            KafkaRawMessage(
                topic="test_topic",
                partition=0,
                offset=0,
                timestamp=timestamp,
                timestamp_type=0,
                key=b"event_key",
                value={"foo": "bar"},
                headers=[("foo_header", b"bar_header")],
            )
        )

    @patch.object(KafkaEventConsumer, "_start_consume_thread")
    def test_kafka_event_consumer_poll_and_consume_message_not_message(
        self, mock_start_consume_thread, fxt_consumer
    ) -> None:
        # Arrange
        kafka_event_consumer = KafkaEventConsumer("integration-test")
        kafka_event_consumer._consumer_thread = MagicMock()

        message = MagicMock()
        kafka_event_consumer._consumer.poll.return_value = message

        # Act
        with patch.object(kafka_event_consumer, "_consume_message", side_effect=RuntimeError) as mock_consume_message:
            kafka_event_consumer._poll_and_consume_message()

        # Assert
        fxt_consumer.assert_called_once()
        mock_start_consume_thread.assert_called_once()
        mock_consume_message.assert_not_called()
        kafka_event_consumer._consumer.commit.assert_not_called()

    @patch.object(KafkaEventConsumer, "_start_consume_thread")
    def test_kafka_event_consumer_poll_and_consume_message_is_error(
        self, mock_start_consume_thread, fxt_consumer
    ) -> None:
        # Arrange
        kafka_event_consumer = KafkaEventConsumer("integration-test")
        kafka_event_consumer._consumer_thread = MagicMock()

        message = MagicMock()
        message.error.return_value = True
        kafka_event_consumer._consumer.poll.return_value = message

        # Act
        with patch.object(kafka_event_consumer, "_consume_message", side_effect=RuntimeError) as mock_consume_message:
            kafka_event_consumer._poll_and_consume_message()

        # Assert
        fxt_consumer.assert_called_once()
        mock_start_consume_thread.assert_called_once()
        mock_consume_message.assert_not_called()
        kafka_event_consumer._consumer.commit.assert_not_called()

    @patch.object(KafkaEventConsumer, "_start_consume_thread")
    def test_kafka_event_consumer_poll_and_consume_message_thrown_error(
        self, mock_start_consume_thread, fxt_consumer
    ) -> None:
        # Arrange
        kafka_event_consumer = KafkaEventConsumer("integration-test")
        kafka_event_consumer._consumer_thread = MagicMock()

        message = MagicMock(spec=Message)
        message.error.return_value = False
        kafka_event_consumer._consumer.poll.return_value = message

        # Act
        with patch.object(kafka_event_consumer, "_consume_message", side_effect=RuntimeError) as mock_consume_message:
            kafka_event_consumer._poll_and_consume_message()

        # Assert
        fxt_consumer.assert_called_once()
        mock_start_consume_thread.assert_called_once()
        mock_consume_message.assert_called_once_with(message)
        kafka_event_consumer._consumer.commit.assert_not_called()

    @patch.object(KafkaEventConsumer, "_start_consume_thread")
    def test_kafka_event_consumer_poll_and_consume_message(self, mock_start_consume_thread, fxt_consumer) -> None:
        # Arrange
        kafka_event_consumer = KafkaEventConsumer("integration-test")
        kafka_event_consumer._consumer_thread = MagicMock()

        message = MagicMock(spec=Message)
        message.error.return_value = False
        kafka_event_consumer._consumer.poll.return_value = message

        # Act
        with patch.object(kafka_event_consumer, "_consume_message") as mock_consume_message:
            kafka_event_consumer._poll_and_consume_message()

        # Assert
        fxt_consumer.assert_called_once()
        mock_start_consume_thread.assert_called_once()
        mock_consume_message.assert_called_once_with(message)
        kafka_event_consumer._consumer.commit.assert_called_once_with()

    @patch.object(KafkaEventConsumer, "_start_consume_thread")
    def test_kafka_event_consumer_stop(self, mock_start_consume_thread, fxt_consumer) -> None:
        # Arrange
        kafka_event_consumer = KafkaEventConsumer("integration-test")
        kafka_event_consumer._consumer_thread = MagicMock()

        # Act
        kafka_event_consumer.stop()

        # Assert
        fxt_consumer.assert_called_once()
        mock_start_consume_thread.assert_called_once()
        assert kafka_event_consumer._should_stop
        kafka_event_consumer._consumer_thread.join.assert_called_once_with()
        kafka_event_consumer._consumer.close.assert_called_once_with()
