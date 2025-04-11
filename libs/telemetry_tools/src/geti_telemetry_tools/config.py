# INTEL CONFIDENTIAL
#
# Copyright (C) 2023 Intel Corporation
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

"""Environment variables and telemetry configuration"""

import os


def str2bool(text: str) -> bool:
    """
    Helper function to convert a string to a boolean based on common true/false representations.
    :param text: string to convert to boolean
    :return: boolean of the input string
    """
    return text.lower() in {"y", "yes", "t", "true", "on", "1"}


ENV_ENABLE_TRACING = "ENABLE_TRACING"
ENV_ENABLE_METRICS = "ENABLE_METRICS"
ENV_DEBUG_TRACING = "DEBUG_TRACING"
ENV_DEBUG_METRICS = "DEBUG_METRICS"
ENV_TEST_METRICS = "TEST_METRICS"
ENV_OTLP_TRACES_RECEIVER = "OTLP_TRACES_RECEIVER"
ENV_OTLP_METRICS_RECEIVER = "OTLP_METRICS_RECEIVER"
ENV_OTLP_TRACES_PROTOCOL = "OTLP_TRACES_PROTOCOL"
ENV_OTLP_PROCESSOR_DO_NOT_SEND_SPANS = "OTLP_PROCESSOR_DO_NOT_SEND_SPANS"

# Enable tracing (note: this switch must be used by consumers of the telemetry module)
ENABLE_TRACING: bool = str2bool(os.environ.get(ENV_ENABLE_TRACING, "false"))
# Enable metrics (note: this switch must be used by consumers of the telemetry module)
ENABLE_METRICS: bool = str2bool(os.environ.get(ENV_ENABLE_METRICS, "false"))
# Debug mode for tracing (output to console)
DEBUG_TRACING: bool = str2bool(os.environ.get(ENV_DEBUG_TRACING, "false"))
# Debug mode for metrics (output to console)
DEBUG_METRICS: bool = str2bool(os.environ.get(ENV_DEBUG_METRICS, "false"))
# Test mode for metrics (output to in-memory reader for unit tests)
TEST_METRICS: bool = str2bool(os.environ.get(ENV_TEST_METRICS, "false"))
# Endpoint of the OTLP receiver for traces
OTLP_TRACES_RECEIVER: str = str(os.getenv(ENV_OTLP_TRACES_RECEIVER, ""))
# Endpoint of the OTLP receiver for metrics
OTLP_METRICS_RECEIVER: str = str(os.getenv(ENV_OTLP_METRICS_RECEIVER, ""))
# OTLP transport protocol between trace exporter and collector. Accepted values: [http, grpc]
OTLP_TRACES_PROTOCOL: str = str(os.getenv(ENV_OTLP_TRACES_PROTOCOL, "grpc")).strip().lower()
# Blacklisted spans which shouldn't be sent to receiver
do_not_send_spans_raw = str(os.getenv(ENV_OTLP_PROCESSOR_DO_NOT_SEND_SPANS, ""))
OTLP_PROCESSOR_DO_NOT_SEND_SPANS: list[str] = do_not_send_spans_raw.split(",") if do_not_send_spans_raw else []
