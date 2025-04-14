# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import fastapi
import pytest
from fastapi import Request
from opentelemetry.trace import get_current_span  # type: ignore[attr-defined]

from geti_telemetry_tools import FastAPITelemetry


@pytest.fixture
def fast_api():
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


class TestUnitOtelFastapi:
    def test_instrument_uninstrument(self, fast_api) -> None:
        """Test that a FastAPI app can be instrumented and un-instrumented."""
        assert not getattr(fast_api, "_is_instrumented_by_opentelemetry", False)

        FastAPITelemetry.instrument(fast_api)
        assert fast_api._is_instrumented_by_opentelemetry

        FastAPITelemetry.uninstrument(fast_api)
        assert not fast_api._is_instrumented_by_opentelemetry
