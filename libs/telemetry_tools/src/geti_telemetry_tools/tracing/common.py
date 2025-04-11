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

"""Common variables and utils for Geti telemetry tracing"""

import functools
import logging
from collections.abc import Callable
from typing import TypeVar, cast

# isort: off
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (  # type: ignore[attr-defined]
    OTLPSpanExporter as GrpcOTLPSpanExporter,
)
from opentelemetry.exporter.otlp.proto.http.trace_exporter import (  # type: ignore[attr-defined]
    OTLPSpanExporter as HttpOTLPSpanExporter,
)

# isort: on
from opentelemetry import propagate
from opentelemetry.sdk.trace import TracerProvider  # type: ignore[attr-defined]
from opentelemetry.sdk.trace.export import ConsoleSpanExporter  # type: ignore[attr-defined]
from opentelemetry.trace import set_tracer_provider  # type: ignore[attr-defined]
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

from geti_logger_tools.logger_config import get_logging_format
from geti_telemetry_tools import (
    DEBUG_TRACING,
    ENABLE_TRACING,
    OTLP_PROCESSOR_DO_NOT_SEND_SPANS,
    OTLP_TRACES_PROTOCOL,
    OTLP_TRACES_RECEIVER,
)
from geti_telemetry_tools.tracing.export.processor import FilteredBatchSpanProcessor

FuncT = TypeVar("FuncT", bound=Callable[..., object])
logger = logging.getLogger(__name__)
if not logger.hasHandlers() and logger.getEffectiveLevel() == logging.WARNING:
    # setup the logger if telemetry is imported before the common logger initialization code
    logging.basicConfig()
    logger.setLevel(logging.INFO)

tracer_provider = TracerProvider()
set_tracer_provider(tracer_provider)
tracer = tracer_provider.get_tracer(__name__)

# Set up the span processors based on configuration
if DEBUG_TRACING:  # Enable console exporter
    span_processor = FilteredBatchSpanProcessor(
        span_exporter=ConsoleSpanExporter(), do_not_send_spans=OTLP_PROCESSOR_DO_NOT_SEND_SPANS
    )
    tracer_provider.add_span_processor(span_processor)
    logger.info("Telemetry console span exporter enabled")
if OTLP_TRACES_RECEIVER:  # Enable OLTP exporter
    try:
        span_exporter: HttpOTLPSpanExporter | GrpcOTLPSpanExporter
        if OTLP_TRACES_PROTOCOL == "http":
            span_exporter = HttpOTLPSpanExporter(endpoint=OTLP_TRACES_RECEIVER)
        elif OTLP_TRACES_PROTOCOL == "grpc":
            span_exporter = GrpcOTLPSpanExporter(endpoint=OTLP_TRACES_RECEIVER, insecure=True)
        else:
            raise ValueError(f"Invalid protocol for OTLP trace exporting: {OTLP_TRACES_PROTOCOL}")
        span_processor = FilteredBatchSpanProcessor(
            span_exporter=span_exporter, do_not_send_spans=OTLP_PROCESSOR_DO_NOT_SEND_SPANS
        )
        tracer_provider.add_span_processor(span_processor)
        logger.info(
            "Telemetry OTLP span exporter enabled. Endpoint: `%s` Carrier: `%s`",
            OTLP_TRACES_RECEIVER,
            OTLP_TRACES_PROTOCOL,
        )
    except Exception:
        # Log exception and do not initialize any span processor
        logger.exception(
            "Failed to initialize OTLP traces exporter to endpoint `%s`. Traces will not be exported.",
            OTLP_TRACES_RECEIVER,
        )
if not DEBUG_TRACING and not OTLP_TRACES_RECEIVER:
    logger.warning("Missing config for exporting telemetry traces: they will not be exported.")


def unified_tracing(_function: FuncT) -> FuncT:
    """Create a tracing span around the wrapped function"""

    if not ENABLE_TRACING:
        return _function

    @functools.wraps(_function)
    def wrapper_tracing(*args, **kwargs):
        message = next((arg for arg in args if hasattr(arg, "headers") and hasattr(arg, "topic")), None)
        if message:
            headers = message.headers
            if headers:
                carrier = {
                    key: value.decode()
                    for key, value in headers
                    if key in ("traceparent", "tracestate") and isinstance(value, bytes)
                }
                ctx = propagate.extract(carrier)
                with tracer.start_as_current_span(_function.__qualname__, context=ctx):
                    return _function(*args, **kwargs)

        with tracer.start_as_current_span(_function.__qualname__):
            return _function(*args, **kwargs)

    return cast("FuncT", wrapper_tracing)


def get_context_string() -> str:
    """Retrieve the current opentelemetry context as string"""
    carrier: dict = {}
    TraceContextTextMapPropagator().inject(carrier)
    return carrier.get("traceparent", "")


def get_logging_format_with_tracing_context(extra_headers: str = "") -> str:
    """
    Get the logging format as a string, including tracing information if enabled.

    The tracing information embedded in the log records includes:
      - trace ID
      - span ID
      - service name

    :param extra_headers: Optional format string to include additional headers before the message
    :returns: Logging format as string
    """
    if ENABLE_TRACING:
        tracing_header = "[trace_id=%(otelTraceID)s span_id=%(otelSpanID)s resource.service.name=%(otelServiceName)s]"
    else:
        tracing_header = ""

    all_headers = " ".join([tracing_header, extra_headers])

    return get_logging_format(extra_headers=all_headers)
