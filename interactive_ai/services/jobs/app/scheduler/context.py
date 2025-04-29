# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from contextlib import nullcontext
from typing import Any

from opentelemetry import trace
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

from model.job import Job

from geti_telemetry_tools import ENABLE_TRACING

tracer = trace.get_tracer(__name__)


def job_context(job: Job, span_name: str) -> Any:
    """
    Creates a context manager which allows to execute code in context of job's telemetry
    :param job: job to pick telemetry context from
    :param span_name: name of the span where managed code will be executed
    :return any: returns a context manager. If tracing is enabled and job has telemetry context, then it will be used.
    Otherwise nullcontext will be returned.
    """
    if job.telemetry is None or not ENABLE_TRACING:
        return nullcontext()

    carrier = {"traceparent": job.telemetry.context}
    ctx = TraceContextTextMapPropagator().extract(carrier=carrier)
    return tracer.start_as_current_span(name=span_name, context=ctx)
