# INTEL CONFIDENTIAL
#
# Copyright (C) 2022 Intel Corporation
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
import threading
import time
import uuid
from collections.abc import Sequence
from importlib import reload
from queue import Queue
from random import randint
from typing import Any, NamedTuple
from unittest.mock import MagicMock

import confluent_kafka
import opentelemetry.instrumentation.confluent_kafka
import pytest
from confluent_kafka import Consumer, KafkaError, Message, Producer
from opentelemetry import trace
from opentelemetry.instrumentation.confluent_kafka import ConfluentKafkaInstrumentor
from opentelemetry.instrumentation.confluent_kafka.utils import _end_current_consume_span
from opentelemetry.propagate import set_global_textmap
from opentelemetry.sdk.trace import (
    TracerProvider,
    trace_api,  # type: ignore[attr-defined]
)
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor
from opentelemetry.trace import INVALID_SPAN, get_current_span  # type: ignore[attr-defined]
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

from geti_telemetry_tools import KafkaTelemetry


class DummyProducer(Producer):
    pass


class DummyConsumer(Consumer):
    pass


@pytest.fixture
def kafka_config():
    return {
        "bootstrap.servers": "localhost:9092",
        "group.id": "integration-test",
        "auto.offset.reset": "smallest",
        "enable.auto.commit": True,
    }


@pytest.fixture
def topic():
    return f"test-topic-{uuid.uuid4()}"


@pytest.fixture
def tracer_provider():
    provider = TracerProvider()
    processor = SimpleSpanProcessor(ConsoleSpanExporter())
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)
    set_global_textmap(TraceContextTextMapPropagator())
    return provider


@pytest.fixture
def instrumented_kafka(tracer_provider):
    ConfluentKafkaInstrumentor().instrument(tracer_provider=tracer_provider)


@pytest.fixture
def producer(kafka_config):
    producer = Producer(
        {
            "bootstrap.servers": kafka_config["bootstrap.servers"],
        }
    )
    yield producer
    producer.flush()


@pytest.fixture
def consumer(kafka_config, topic):
    consumer = Consumer(kafka_config)
    consumer.subscribe([topic])
    yield consumer
    consumer.close()


class KafkaRawMessage(NamedTuple):
    topic: str
    value: Any | None
    headers: Sequence[tuple[str, bytes]]


class MessageCollector:
    def __init__(self):
        self.messages = Queue()
        self.running = True
        self.trace_ids = []
        self.span_ids = []

    def on_message(self, msg: KafkaRawMessage) -> None:
        with trace.get_tracer(__name__).start_as_current_span("on_message") as span:
            span_context = span.get_span_context()
            self.trace_ids.append(span_context.trace_id)
            self.span_ids.append(span_context.span_id)
            self.messages.put(msg)

    def collect(self, consumer) -> None:
        while self.running:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() != KafkaError._PARTITION_EOF:
                    print(f"Consumer error: {msg.error()}")
                continue

            self.on_message(KafkaRawMessage(topic=msg.topic(), headers=msg.headers(), value=msg.value()))


@pytest.fixture
def fxt_mocked_producer_type() -> confluent_kafka.Producer:
    orig_producer_type = confluent_kafka.Producer
    # Mocking doesn't work because Producer is final, that's why we replace it with subclass
    # Also patching confluent_kafka.Producer breaks wrapt integration
    confluent_kafka.Producer = DummyProducer
    # Need to reload opentelemetry.instrumentation.confluent_kafka to trigger AutoInstrumentedProducer definition
    reload(opentelemetry.instrumentation.confluent_kafka)
    confluent_kafka.Producer.produce = MagicMock()
    yield confluent_kafka.Producer
    confluent_kafka.Producer = orig_producer_type


@pytest.fixture
def fxt_mocked_consumer_type() -> confluent_kafka.Consumer:
    orig_consumer_type = confluent_kafka.Consumer
    # Mocking doesn't work because Consumer is final, that's why we replace it with subclass
    # Also patching confluent_kafka.Consumer breaks wrapt integration
    confluent_kafka.Consumer = DummyConsumer
    # Need to reload opentelemetry.instrumentation.confluent_kafka to trigger AutoInstrumentedConsumer definition
    reload(opentelemetry.instrumentation.confluent_kafka)
    confluent_kafka.Consumer.poll = MagicMock()
    yield confluent_kafka.Consumer
    confluent_kafka.Consumer = orig_consumer_type


@pytest.fixture
def fxt_message():
    def _build_message(headers=None) -> Message:
        message = MagicMock(spec=Message)
        message.headers.return_value = [] if headers is None else headers
        message.topic.return_value = "test_topic"
        message.partition.return_value = 0
        message.offset.return_value = 0
        message.__len__.return_value = 1
        return message

    return _build_message


class TestIntegrationOtelKafka:
    def test_kafka_producer_no_instrumentation(self, fxt_mocked_producer_type) -> None:
        """
        <b>Description:</b>
        Check that without instrumentation Kafka producer sends no headers

        <b>Given:</b>
        Kafka producer is not instrumented

        <b>When:</b>
        Kafka producer sends an event

        <b>Then:</b>
        No headers are sent
        """
        # Keep original method, since OpenTelemetry instrumentor replaces it
        orig_produce_method = fxt_mocked_producer_type.produce

        kafka_producer = confluent_kafka.Producer({})
        kafka_producer.produce(topic="test_topic", value="", key=b"key")

        orig_produce_method.assert_called_once()
        assert "headers" not in orig_produce_method.call_args.kwargs, "Expected not to have headers"

    def test_kafka_producer_instrumented(self, fxt_mocked_producer_type, request) -> None:
        """
        <b>Description:</b>
        Check that with instrumentation Kafka producer sends 'traceparent' header

        <b>Given:</b>
        Kafka producer is instrumented

        <b>When:</b>
        Kafka producer sends an event

        <b>Then:</b>
        Event header 'traceparent' is sent
        """
        request.addfinalizer(lambda: KafkaTelemetry.uninstrument())
        # Keep original method, since OpenTelemetry instrumentor replaces it
        orig_produce_method = fxt_mocked_producer_type.produce

        KafkaTelemetry.instrument()

        kafka_producer = confluent_kafka.Producer({})
        kafka_producer.produce(topic="test_topic", value="", key=b"key")

        orig_produce_method.assert_called_once()
        assert "headers" in orig_produce_method.call_args.kwargs, "Expected to have headers"
        headers = orig_produce_method.call_args.kwargs["headers"]

        traceparent = next((header[1] for header in headers if header[0] == "traceparent"), [None])
        assert traceparent is not None, "Expected to have traceparent header"

    def test_kafka_consumer_no_instrumentation(self, fxt_mocked_consumer_type, fxt_message) -> None:
        """
        <b>Description:</b>
        Check that with instrumentation Kafka consumer puts a tracing context as an event header

        <b>Given:</b>
        Kafka consumer is instrumented

        <b>When:</b>
        Kafka consumer returns an event

        <b>Then:</b>
        Event headers contain tracing context, and it's possible to attach it
        """
        # Keep original method, since OpenTelemetry instrumentor replaces it
        orig_poll_method = fxt_mocked_consumer_type.poll
        orig_poll_method.return_value = fxt_message()

        kafka_consumer = confluent_kafka.Consumer({"group.id": "integration-test"})
        message = kafka_consumer.poll()
        assert message is not None, "Expected to have a message"

        with get_current_span() as span:
            assert span == INVALID_SPAN

    def test_kafka_consumer_instrumented(self, fxt_mocked_consumer_type, fxt_message, request) -> None:
        """
        <b>Description:</b>
        Check that with instrumentation Kafka consumer puts a tracing context as an event header

        <b>Given:</b>
        Kafka consumer is instrumented

        <b>When:</b>
        Kafka consumer returns an event

        <b>Then:</b>
        Event headers contain tracing context, and it's possible to attach it
        """
        request.addfinalizer(lambda: KafkaTelemetry.uninstrument())
        # Keep original method, since OpenTelemetry instrumentor replaces it
        orig_poll_method = fxt_mocked_consumer_type.poll
        orig_poll_method.return_value = fxt_message()

        KafkaTelemetry.instrument()

        kafka_consumer = confluent_kafka.Consumer({"group.id": "integration-test"})
        request.addfinalizer(lambda: _end_current_consume_span(kafka_consumer))

        message = kafka_consumer.poll()

        assert message is not None, "Expected to have a message"
        with get_current_span() as span:
            assert span is not None, "Expected to have a span"
            assert span != INVALID_SPAN

    def test_kafka_consumer_instrumented_request_headers(
        self,
        fxt_mocked_consumer_type,
        fxt_message,
        request,
    ) -> None:
        """
        <b>Description:</b>
        Check that with instrumentation Kafka consumer reuses trace ID & span ID from 'traceparent' event header

        <b>Given:</b>
        Kafka consumer is instrumented
        Kafka event contains 'traceparent' header

        <b>When:</b>
        Kafka consumer returns an event

        <b>Then:</b>
        Event headers contain tracing context
        Trace ID matches with one from event header
        New span has a parent span from event header
        """
        request.addfinalizer(lambda: KafkaTelemetry.uninstrument())
        # Keep original method, since OpenTelemetry instrumentor replaces it
        orig_poll_method = fxt_mocked_consumer_type.poll

        span_id = randint(1, 2**64 - 1)
        span_id_s = trace_api.format_span_id(span_id)

        trace_id = randint(1, 2**128 - 1)
        trace_id_s = trace_api.format_trace_id(trace_id)

        orig_poll_method.return_value = fxt_message([("traceparent", f"00-{trace_id_s}-{span_id_s}-01".encode())])

        KafkaTelemetry.instrument()

        kafka_consumer = confluent_kafka.Consumer({"group.id": "integration-test"})
        request.addfinalizer(lambda: _end_current_consume_span(kafka_consumer))

        message = kafka_consumer.poll()

        assert message is not None, "Expected to have a message"
        with get_current_span() as span:
            assert span is not None, "Expected to have a span"
            assert span.links is not None
            assert len(span.links) == 1
            assert span.links[0].context.trace_id == trace_id, "Expected to have a link with valid trace ID"
            assert span.links[0].context.span_id == span_id, "Expected to have a link with valid parent span ID"

    @pytest.mark.skip
    def test_trace_propagation(self, producer, consumer, topic, instrumented_kafka) -> None:
        """
        <b>Description:</b>
        Verify that trace context is properly propagated from Kafka producer to consumer,
        maintaining the same trace_id while generating new span_ids.

        <b>Given:</b>
        - A configured Kafka producer and consumer
        - Initialized OpenTelemetry tracer provider
        - Instrumented Confluent Kafka client
        - A dedicated Kafka topic
        - A message collector running in a separate thread

        <b>When:</b>
        - Producer sends 3 messages with trace context
        - Each message is produced within a new span
        - Consumer processes messages in a separate thread
        - Each message is consumed within a new span

        <b>Then:</b>
        - Number of produced messages equals number of consumed messages
        - Trace IDs in consumer spans match the producer spans
        - Span IDs in consumer are different from producer (new spans created)
        - All messages are successfully processed within timeout period
        - Trace context is properly extracted from message headers
        """
        # Setup message collector
        collector = MessageCollector()
        consumer_thread = threading.Thread(target=collector.collect, args=(consumer,))
        consumer_thread.start()

        producer_trace_ids = []
        producer_span_ids = []

        # Produce messages with tracing
        try:
            for i in range(3):
                with trace.get_tracer(__name__).start_as_current_span(f"produce_message_{i}") as span:
                    trace_id = span.get_span_context().trace_id
                    span_id = span.get_span_context().span_id
                    producer_trace_ids.append(trace_id)
                    producer_span_ids.append(span_id)

                    producer.produce(
                        topic=topic,
                        value=f"test message {i}".encode(),
                        headers=[
                            (
                                "traceparent",
                                f"00-{trace_api.format_trace_id(trace_id)}-{trace_api.format_span_id(span_id)}-01".encode(),
                            )
                        ],
                        callback=lambda err, msg: print(f"Produced message: {msg.value().decode()}"),  # noqa: ARG005
                    )
                    producer.flush()

            # Wait for messages to be consumed
            messages_received = 0
            start_time = time.time()
            while messages_received < 3 and time.time() - start_time < 10:
                if not collector.messages.empty():
                    msg = collector.messages.get()
                    print(f"Received message: {msg.value.decode()}")
                    messages_received += 1

            # Stop collector
            collector.running = False
            consumer_thread.join()

            # Verify trace propagation
            assert len(producer_trace_ids) == len(collector.trace_ids), (
                "Number of produced and consumed messages doesn't match"
            )

            # Print all trace IDs for debugging
            for i in range(len(producer_trace_ids)):
                print(f"\nMessage {i}:")
                print(f"Producer trace_id: {producer_trace_ids[i]:x}")
                print(f"Consumer trace_id: {collector.trace_ids[i]:x}")
                print(f"Producer span_id: {producer_span_ids[i]:x}")
                print(f"Consumer span_id: {collector.span_ids[i]:x}")

            # Verify trace IDs match
            for prod_trace_id, cons_trace_id in zip(producer_trace_ids, collector.trace_ids):
                assert prod_trace_id == cons_trace_id, (
                    f"Trace ID mismatch: producer={prod_trace_id:x}, consumer={cons_trace_id:x}"
                )

            # Verify span IDs are different (as they should be)
            for prod_span_id, cons_span_id in zip(producer_span_ids, collector.span_ids):
                assert prod_span_id != cons_span_id, "Span IDs should be different for producer and consumer"

        finally:
            # Cleanup
            collector.running = False
            consumer_thread.join()
