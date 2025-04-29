# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from random import randint
from unittest.mock import patch

import fastapi
import pytest
from fastapi import Request
from opentelemetry import propagate  # type: ignore[attr-defined]
from opentelemetry.baggage.propagation import W3CBaggagePropagator  # type: ignore[attr-defined]
from opentelemetry.propagators.b3 import B3Format  # type: ignore[attr-defined]
from opentelemetry.propagators.composite import CompositePropagator  # type: ignore[attr-defined]
from opentelemetry.propagators.jaeger import JaegerPropagator  # type: ignore[attr-defined]
from opentelemetry.sdk.trace import trace_api  # type: ignore[attr-defined]
from opentelemetry.trace import INVALID_SPAN, get_current_span  # type: ignore[attr-defined]
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator  # type: ignore[attr-defined]
from starlette.testclient import TestClient

from geti_telemetry_tools import FastAPITelemetry

from .tracing_header_utils import (
    traceparent_regex,
    uber_traceid_regex,
    x_b3_sampled_regex,
    x_b3_spanid_regex,
    x_b3_traceid_regex,
)


@pytest.fixture
def fastapi_app():
    app = fastapi.FastAPI()

    @app.middleware("http")
    async def save_request_span(request: Request, call_next):
        span = get_current_span()
        app.request_span = span
        return await call_next(request)

    @app.get("/ping")
    async def ping(name: str):
        return "pong"

    yield app


@pytest.fixture
def fastapi_client(fastapi_app):
    return TestClient(fastapi_app)


class TestIntegrationOtelFastapi:
    def test_fastapi_no_instrumentation(self, fastapi_app, fastapi_client) -> None:
        """
        <b>Description:</b>
        Check that, without instrumentation, a FastAPI app has no tracing context
        upon request, and it returns no 'traceparent' header.

        <b>Given:</b>
        FastAPI app is not instrumented

        <b>When:</b>
        Application handles a request

        <b>Then:</b>
        No tracing context presents and response contains no 'traceparent' header
        """
        response = fastapi_client.get("/ping")

        assert fastapi_app.request_span == INVALID_SPAN, "Expected to have an invalid span"
        assert response.headers.get("traceparent") is None, "Expected to not have a traceparent response header"

    def test_fastapi_instrumented(self, fastapi_app, fastapi_client) -> None:
        """
        <b>Description:</b>
        Check that, with instrumentation, FastAPI app has tracing context
        upon request it and returns 'traceparent' header

        <b>Given:</b>
        FastAPI app is instrumented

        <b>When:</b>
        Application handles a request

        <b>Then:</b>
        The request contains tracing context
        The response contains a valid traceparent header
        The response trace-id matches the one in the request span context
        """
        FastAPITelemetry.instrument(fastapi_app)

        try:
            response = fastapi_client.get("/ping")

            request_span = fastapi_app.request_span
            assert request_span != INVALID_SPAN, "Expected to have a valid span"
            span_context = request_span.get_span_context()
            request_trace_id = trace_api.format_trace_id(span_context.trace_id)
            response_traceparent = response.headers.get("traceparent")
            assert response_traceparent is not None, "Missing traceparent response header"
            assert traceparent_regex.match(response_traceparent), "Invalid traceparent header format"
            assert request_trace_id in response_traceparent, "Incorrect trace-id in traceparent header"
        finally:
            FastAPITelemetry.uninstrument(fastapi_app)

    def test_fastapi_instrumented_request_headers(self, fastapi_app, fastapi_client) -> None:
        """
        <b>Description:</b>
        Check that, with instrumentation, FastAPI app reuses trace ID & span ID
        from 'traceparent' request header.

        <b>Given:</b>
        FastAPI app is instrumented, incoming request contains 'traceparent' request header

        <b>When:</b>
        Application handles a request

        <b>Then:</b>
        The request contains tracing context
        The request context has the same trace-id and span-id as set in the header
        The response contains a valid traceparent header
        The response trace-id matches the one in the request header
        """
        FastAPITelemetry.instrument(fastapi_app)

        span_id = randint(1, 2**64 - 1)
        span_id_s = trace_api.format_span_id(span_id)

        trace_id = randint(1, 2**128 - 1)
        trace_id_s = trace_api.format_trace_id(trace_id)

        try:
            response = fastapi_client.get("/ping", headers={"traceparent": f"00-{trace_id_s}-{span_id_s}-01"})

            # Check request
            request_span = fastapi_app.request_span
            assert request_span != INVALID_SPAN, "Expected to have a valid span"
            span_context = request_span.get_span_context()
            request_trace_id = span_context.trace_id
            assert request_trace_id == trace_id, "Incorrect trace-id in the request"
            assert request_span.parent.span_id == span_id, "Incorrect parent span-id in the request"
            # Check response
            response_traceparent = response.headers.get("traceparent")
            assert response_traceparent is not None, "Missing traceparent response header"
            assert traceparent_regex.match(response_traceparent), "Invalid traceparent header format"
            assert trace_id_s in response_traceparent, "Incorrect trace-id in traceparent header"
        finally:
            FastAPITelemetry.uninstrument(fastapi_app)

    @pytest.mark.skip
    def test_fastapi_instrumented_b3_propagator(self, fastapi_app, fastapi_client) -> None:
        """
        <b>Description:</b>
        Test FastAPI instrumented with B3 propagation format

        <b>Given:</b>
        FastAPI app is instrumented, incoming request contains B3 headers

        <b>When:</b>
        Application handles a request

        <b>Then:</b>
        The request contains tracing context
        The request context has the same trace-id and span-id as set in the header
        The response contains valid B3 headers
        The response trace-id matches the one in the request header
        """
        propagate.set_global_textmap(B3Format())
        try:
            with patch("telemetry.tracing.fastapi.fastapi_telemetry.propagator", propagate.get_global_textmap()):
                FastAPITelemetry.instrument(fastapi_app)

                trace_id = randint(1, 2**128 - 1)
                trace_id_s = trace_api.format_trace_id(trace_id)

                span_id = randint(1, 2**64 - 1)
                span_id_s = trace_api.format_span_id(span_id)

                try:
                    response = fastapi_client.get(
                        "/ping",
                        headers={
                            "x-b3-traceid": trace_id_s,
                            "x-b3-spanid": span_id_s,
                            "x-b3-sampled": "1",
                        },
                    )

                    # Check request
                    request_span = fastapi_app.request_span
                    assert request_span != INVALID_SPAN, "Expected to have a valid span"
                    span_context = request_span.get_span_context()
                    request_trace_id = span_context.trace_id
                    assert request_trace_id == trace_id, "Incorrect trace-id in the request"
                    assert request_span.parent.span_id == span_id, "Incorrect parent span-id in the request"
                    # # Check response
                    response_traceid = response.headers.get("x-b3-traceid")
                    response_spanid = response.headers.get("x-b3-spanid")
                    response_sampled = response.headers.get("x-b3-sampled")
                    assert response_traceid is not None, "Missing x-b3-traceid response header"
                    assert response_spanid is not None, "Missing x-b3-spanid response header"
                    assert response_sampled is not None, "Missing x-b3-sampled response header"
                    assert x_b3_traceid_regex.match(response_traceid), "Invalid x-b3-traceid header format"
                    assert x_b3_spanid_regex.match(response_spanid), "Invalid x-b3-spanid header format"
                    assert x_b3_sampled_regex.match(response_sampled), "Invalid x-b3-sampled header format"
                    assert trace_id_s in response_traceid, "Incorrect trace-id in x-b3-traceid header"
                finally:
                    FastAPITelemetry.uninstrument(fastapi_app)
        finally:
            propagate.set_global_textmap(CompositePropagator([TraceContextTextMapPropagator(), W3CBaggagePropagator()]))

    @pytest.mark.skip(reason="Jaeger exporter bug in opentelemetry-python 1.15")
    def test_fastapi_instrumented_jaeger_propagator(self, fastapi_app, fastapi_client) -> None:
        """
        <b>Description:</b>
        Test FastAPI instrumented with Jaeger propagation format

        <b>Given:</b>
        FastAPI app is instrumented, incoming request contains Jaeger headers

        <b>When:</b>
        Application handles a request

        <b>Then:</b>
        The request contains tracing context
        The request context has the same trace-id and span-id as set in the header
        The response contains valid Jaeger headers
        The response trace-id matches the one in the request header
        """
        propagate.set_global_textmap(JaegerPropagator())
        try:
            with patch("telemetry.tracing.fastapi.fastapi_telemetry.propagator", propagate.get_global_textmap()):
                FastAPITelemetry.instrument(fastapi_app)

                trace_id = randint(1, 2**128 - 1)
                trace_id_s = trace_api.format_trace_id(trace_id)

                span_id = randint(1, 2**64 - 1)
                span_id_s = trace_api.format_span_id(span_id)

                try:
                    response = fastapi_client.get(
                        "/ping",
                        headers={"uber-trace-id": f"{trace_id_s}:{span_id_s}:0:03"},
                    )

                    # Check request
                    request_span = fastapi_app.request_span
                    assert request_span != INVALID_SPAN, "Expected to have a valid span"
                    span_context = request_span.get_span_context()
                    request_trace_id = span_context.trace_id
                    assert request_trace_id == trace_id, "Incorrect trace-id in the request"
                    assert request_span.parent.span_id == span_id, "Incorrect parent span-id in the request"
                    # # Check response
                    response_uber_trace_id = response.headers.get("uber-trace-id")
                    assert response_uber_trace_id is not None, "Missing uber-trace-id response header"
                    assert uber_traceid_regex.match(response_uber_trace_id), "Invalid uber-trace-id header format"
                    assert trace_id_s in response_uber_trace_id, "Incorrect trace-id in uber-trace-id header"
                finally:
                    FastAPITelemetry.uninstrument(fastapi_app)
        finally:
            propagate.set_global_textmap(CompositePropagator([TraceContextTextMapPropagator(), W3CBaggagePropagator()]))
