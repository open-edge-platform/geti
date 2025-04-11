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
from unittest.mock import MagicMock, patch

from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

from model.job import Job
from scheduler.context import job_context


@patch("scheduler.context.nullcontext")
def test_job_context_no_telemetry(mock_nullcontext) -> None:
    # Arrange
    job = MagicMock(spec=Job)
    job.telemetry = None

    nullcontext = MagicMock()
    mock_nullcontext.return_value = nullcontext

    # Act
    result = job_context(job=job, span_name="test")

    # Assert
    assert result == nullcontext
    mock_nullcontext.assert_called_once_with()


@patch("scheduler.context.nullcontext")
def test_job_context_no_tracing(mock_nullcontext) -> None:
    # Arrange
    job = MagicMock(spec=Job)
    telemetry = MagicMock()
    job.telemetry = telemetry

    nullcontext = MagicMock()
    mock_nullcontext.return_value = nullcontext

    # Act
    result = job_context(job=job, span_name="test")

    # Assert
    assert result == nullcontext
    mock_nullcontext.assert_called_once_with()


@patch.object(TraceContextTextMapPropagator, "extract")
@patch("scheduler.context.tracer", return_value=True)
@patch("scheduler.context.ENABLE_TRACING", return_value=True)
def test_job_context(mock_enable_tracing, mock_tracer, mock_extract) -> None:
    # Arrange
    job = MagicMock(spec=Job)
    telemetry = MagicMock()
    telemetry.context = "traceparent"
    job.telemetry = telemetry

    context = MagicMock()
    mock_extract.return_value = context

    span = MagicMock()
    mock_tracer.start_as_current_span.return_value = span

    # Act
    result = job_context(job=job, span_name="test")

    # Assert
    assert result == span
    mock_extract.assert_called_once_with(carrier={"traceparent": "traceparent"})
    mock_tracer.start_as_current_span.assert_called_once_with(name="test", context=context)
