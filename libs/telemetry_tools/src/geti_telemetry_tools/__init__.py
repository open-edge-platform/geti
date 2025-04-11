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
