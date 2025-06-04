# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from contextlib import asynccontextmanager

from fastapi import FastAPI

import rest.endpoints  # noqa: F401, pylint: disable=unused-import  # Importing for endpoint registration
from geti_telemetry_tools import ENABLE_TRACING, FastAPITelemetry
from routers import platform_router


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore # noqa: ANN201
    """
    Defines startup and shutdown of the fastAPI app
    """
    # Startup actions

    yield

    # Shutdown actions
    if ENABLE_TRACING:
        FastAPITelemetry.uninstrument(app)


app = FastAPI(lifespan=lifespan)

if ENABLE_TRACING:
    FastAPITelemetry.instrument(app)

app.include_router(platform_router, prefix="/api/v1")
