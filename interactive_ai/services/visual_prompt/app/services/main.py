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

from services.endpoints.prompt_endpoints import router as prompt_router
from services.kafka_handler import VPSKafkaHandler
from services.visual_prompt_service import VisualPromptService
from utils.feature_flag import FeatureFlag

from geti_fastapi_tools.exceptions import GetiBaseException
from geti_fastapi_tools.responses import error_response_rest
from geti_feature_tools import FeatureFlagProvider
from geti_telemetry_tools import ENABLE_TRACING, FastAPITelemetry, KafkaTelemetry

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore # noqa: ANN201
    """
    Defines startup and shutdown of the fastAPI app
    """
    # Startup
    logger.info("Starting up kafka handlers")
    VPSKafkaHandler()

    if ENABLE_TRACING:
        KafkaTelemetry.instrument()

    # Initialize the VisualPromptService by loading the SAM model in memory
    if FeatureFlagProvider.is_enabled(FeatureFlag.FEATURE_FLAG_VISUAL_PROMPT_SERVICE):
        app.visual_prompt_service = VisualPromptService()  # type: ignore[attr-defined]

    yield

    # Shutdown
    logger.info("Shutting down kafka handlers")

    VPSKafkaHandler().stop()

    if ENABLE_TRACING:
        FastAPITelemetry.uninstrument(app)
        KafkaTelemetry.uninstrument()


app = FastAPI(lifespan=lifespan)

if ENABLE_TRACING:
    FastAPITelemetry.instrument(app)

app.include_router(prompt_router)


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
