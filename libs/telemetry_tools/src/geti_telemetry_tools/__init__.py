# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""Geti telemetry (tracing, metrics) with OpenTelemetry"""

from .config import (
    DEBUG_METRICS,
    DEBUG_TRACING,
    ENABLE_METRICS,
    ENABLE_TRACING,
    OTLP_METRICS_RECEIVER,
    OTLP_PROCESSOR_DO_NOT_SEND_SPANS,
    OTLP_TRACES_PROTOCOL,
    OTLP_TRACES_RECEIVER,
    TEST_METRICS,
)
from .tracing.common import get_context_string, unified_tracing
from .tracing.fastapi.fastapi_telemetry import FastAPITelemetry
from .tracing.grpc.grpc_telemetry import GrpcClientTelemetry, GrpcServerTelemetry
from .tracing.kafka.kafka_telemetry import KafkaTelemetry
from .tracing.logging.logging_telemetry import LoggerTelemetry

__all__ = [
    "DEBUG_METRICS",
    "DEBUG_TRACING",
    "ENABLE_METRICS",
    "ENABLE_TRACING",
    "OTLP_METRICS_RECEIVER",
    "OTLP_PROCESSOR_DO_NOT_SEND_SPANS",
    "OTLP_TRACES_PROTOCOL",
    "OTLP_TRACES_RECEIVER",
    "TEST_METRICS",
    "FastAPITelemetry",
    "GrpcClientTelemetry",
    "GrpcServerTelemetry",
    "KafkaTelemetry",
    "LoggerTelemetry",
    "get_context_string",
    "unified_tracing",
]
