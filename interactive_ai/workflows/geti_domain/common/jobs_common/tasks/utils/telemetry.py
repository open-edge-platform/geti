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

"""This module defines methods and wrappers to initialize logger for tasks"""

import logging
import os
from collections.abc import Callable
from functools import wraps
from typing import Any

from geti_telemetry_tools import ENABLE_TRACING, KafkaTelemetry, LoggerTelemetry
from opentelemetry import trace
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

ENV_OPENTELEMETRY_CONTEXT = "OPENTELEMETRY_CONTEXT"
OPENTELEMETRY_CONTEXT = os.environ.get(ENV_OPENTELEMETRY_CONTEXT, "")


def task_telemetry(_function: Callable) -> Any:
    """Decorator to add telemetry to task"""

    if not ENABLE_TRACING:
        return _function

    @wraps(_function)
    def wrapper(*args, **kwargs):
        if not OPENTELEMETRY_CONTEXT:
            logger.error("Could not retrieve the opentelemetry context.")
            return _function(*args, **kwargs)

        LoggerTelemetry.instrument()
        KafkaTelemetry.instrument()

        carrier = {"traceparent": OPENTELEMETRY_CONTEXT}
        logger.debug(f"Using opentelemetry context {OPENTELEMETRY_CONTEXT}")
        ctx = TraceContextTextMapPropagator().extract(carrier=carrier)
        with tracer.start_as_current_span(_function.__qualname__, context=ctx):
            return _function(*args, **kwargs)

    return wrapper
