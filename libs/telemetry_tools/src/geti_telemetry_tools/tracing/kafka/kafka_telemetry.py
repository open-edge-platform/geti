# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""Helpers for the integration of OpenTelemetry with Kafka"""

import logging

from geti_telemetry_tools.tracing.common import tracer_provider

logger = logging.getLogger(__name__)


class KafkaTelemetry:
    """OpenTelemetry instrumentation for Kafka"""

    @staticmethod
    def instrument() -> None:
        """
        Instruments Kafka producer and consumer

        Instrumentor wraps KafkaProducer.send() and KafkaConsumer.__next__ methods.
        If incoming Kafka event has a 'traceparent' header in metadata, then parent trace ID & span ID are reused.
        Kafka Producer adds this header in case of event publishing if tracing context exists.
        Adds a hook on a consumer side to put tracing context as 'opentelemetry_context' event header
        to make it possible to restore it in multi-threaded event handlers
        """
        try:
            from opentelemetry.instrumentation.confluent_kafka import (
                ConfluentKafkaInstrumentor,  # type: ignore[attr-defined]
            )
        except ImportError:
            logger.exception(
                "Cannot instrument Kafka because opentelemetry-instrumentation-kafka "
                "is not installed. Add 'telemetry[kafka]' to the required packages."
            )
            raise

        logger.debug("Instrumenting Kafka")
        ConfluentKafkaInstrumentor().instrument(tracer_provider=tracer_provider)

    @staticmethod
    def uninstrument() -> None:
        """
        Removes Kafka instrumentation
        """
        try:
            from opentelemetry.instrumentation.confluent_kafka import (
                ConfluentKafkaInstrumentor,  # type: ignore[attr-defined]
            )
        except ImportError:
            logger.exception(
                "Cannot instrument Kafka because opentelemetry-instrumentation-kafka "
                "is not installed. Add 'telemetry[kafka]' to the required packages."
            )
            raise

        logger.debug("Uninstrumenting Kafka")
        ConfluentKafkaInstrumentor().uninstrument()
