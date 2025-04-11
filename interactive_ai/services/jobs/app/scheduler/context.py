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
