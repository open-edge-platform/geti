# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
