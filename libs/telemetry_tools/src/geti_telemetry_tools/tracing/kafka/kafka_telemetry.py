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
