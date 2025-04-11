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

import logging

import testfixtures
from opentelemetry.sdk.trace import trace_api  # type: ignore[attr-defined]
from opentelemetry.trace import get_tracer  # type: ignore[attr-defined]

from geti_logger_tools.logger_config import initialize_logger
from geti_telemetry_tools import LoggerTelemetry


class TestIntegrationOtelLogging:
    def test_logger_no_tracing_span(self) -> None:
        """
        <b>Description:</b>
        Check that if tracing context is not present, then trace ID and span ID
        will be 0's in logs

        <b>Given:</b>
        No tracing context created

        <b>When:</b>
        A message is logged

        <b>Then:</b>
        Trace ID and span ID will be 0's in logs
        """
        initialize_logger(__name__)
        LoggerTelemetry.instrument()
        _logger = logging.getLogger(__name__)

        with testfixtures.LogCapture(attributes=("getMessage", "otelTraceID", "otelSpanID")) as lcap:
            _logger.info("Test log output")
            # Tracing context is absent, both traceID and spanID should be set to 0
            lcap.check_present(("Test log output", "0", "0"))

    def test_logger_tracing_span(self) -> None:
        """
        <b>Description:</b>
        Check that if tracing context is present, then trace ID and span ID
        will be correctly logged

        <b>Given:</b>
        Tracing context is created and active

        <b>When:</b>
        A message is logged

        <b>Then:</b>
        Logged Trace ID and span ID values match with context values
        """
        initialize_logger(__name__)
        LoggerTelemetry.instrument()
        _logger = logging.getLogger(__name__)

        with get_tracer("test").start_as_current_span("test-span") as span:
            context = span.get_span_context()
            with testfixtures.LogCapture(attributes=("getMessage", "otelTraceID", "otelSpanID")) as lcap:
                _logger.info("Traced test log output")
                # Tracing context is initialized
                # logger should have traceID and spanID propagated from tracing context
                lcap.check_present(
                    (
                        "Traced test log output",
                        trace_api.format_trace_id(context.trace_id),
                        trace_api.format_span_id(context.span_id),
                    )
                )
