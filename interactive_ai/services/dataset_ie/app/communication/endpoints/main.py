# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""
This module initializes the FastAPI app and registers the used routers
"""

import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from communication.endpoints.export_endpoints import router as export_router
from communication.endpoints.import_endpoints import router as import_router
from communication.endpoints.upload_endpoints import router as upload_router
from communication.kafka_handler import DatasetIEKafkaHandler

from geti_fastapi_tools.exceptions import GetiBaseException
from geti_fastapi_tools.responses import error_response_rest
from geti_telemetry_tools import ENABLE_TRACING, FastAPITelemetry, KafkaTelemetry

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore # noqa: ANN201
    """
    Defines startup and shutdown of the fastAPI app
    """
    # Startup
    if ENABLE_TRACING:
        KafkaTelemetry.instrument()
    DatasetIEKafkaHandler()
    yield
    # Shutdown
    DatasetIEKafkaHandler().stop()
    if ENABLE_TRACING:
        FastAPITelemetry.uninstrument(app)
        KafkaTelemetry.uninstrument()


app = FastAPI(lifespan=lifespan)

if ENABLE_TRACING:
    FastAPITelemetry.instrument(app)

app.include_router(upload_router)
app.include_router(import_router)
app.include_router(export_router)


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


# Override the default http exception handler to return error message under 'message' not 'detail'
@app.exception_handler(HTTPException)
def http_exception_handler(request: Request, exception: HTTPException) -> JSONResponse:  # noqa: ARG001
    """Handles HTTP Exceptions in the dataset IE MS"""
    logger.info(f"Exception: {str(exception)}")
    return JSONResponse({"message": str(exception.detail)}, status_code=exception.status_code)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0")  # noqa: S104
