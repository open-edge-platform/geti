# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""
This module initializes the FastAPI app and registers the used routers
"""

import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from communication.endpoints.export_endpoints import router as export_router
from communication.endpoints.import_endpoints import router as import_router
from communication.endpoints.upload_endpoints import router as upload_router

from geti_fastapi_tools.exceptions import GetiBaseException
from geti_fastapi_tools.responses import error_response_rest
from geti_telemetry_tools import ENABLE_TRACING, FastAPITelemetry

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore # noqa: ANN201
    """
    Defines startup and shutdown of the fastAPI app
    """
    # Startup
    yield
    # Shutdown
    if ENABLE_TRACING:
        FastAPITelemetry.uninstrument(app)


app = FastAPI(lifespan=lifespan)

if ENABLE_TRACING:
    FastAPITelemetry.instrument(app)

app.include_router(export_router)
app.include_router(import_router)
app.include_router(upload_router)


@app.exception_handler(GetiBaseException)
def handle_base_exception(request: Request, e: GetiBaseException) -> Response:
    """Base exception handler"""
    response = error_response_rest(e.error_code, e.message, e.http_status)
    headers: dict[str, str] | None = None
    # No content/Not modified can not return a JSONResponse due to missing 'content'
    if e.http_status in [204, 304] or e.http_status < 200:
        if request.method == "GET":
            headers = {"Cache-Control": "no-cache"}  # always revalidate
        return Response(status_code=int(e.http_status), headers=headers)
    return JSONResponse(content=response, status_code=int(e.http_status), headers=headers)


@app.exception_handler(RequestValidationError)
def validation_exception_handler(request: Request, exc: RequestValidationError) -> Response:  # noqa: ARG001
    """Overrides FastAPI RequestValidationError from 422 to 400."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=jsonable_encoder({"detail": exc.errors(), "body": exc.body}),
    )


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0")  # noqa: S104
