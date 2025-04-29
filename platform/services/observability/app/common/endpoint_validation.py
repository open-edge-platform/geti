"""
Custom FastAPI endpoint validation handlers.
"""

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging

from fastapi import Request, status
from fastapi.openapi.utils import validation_error_response_definition
from fastapi.responses import JSONResponse, Response

logger = logging.getLogger(__name__)


validation_error_response_definition["properties"] = {
    "msg": {"type": "string", "title": "Error message"},
    "code": {"type": "integer", "default": 422, "title": "Error code"},
}


async def handle_request_validation_error(request: Request, exc: Exception) -> Response:
    """Handles request validation errors.

    Logs the validation error and returns HTTP 422 with empty content as a response.

    :param request: The handled request.
    :param exc: The request validation error to handle.
    :return Response: Empty response with HTTP 422 status code.
    """
    logger.error(f"Request validation failed for {repr(request.method)} {repr(str(request.url))}: {exc}")
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    return JSONResponse(status_code=status_code, content={"code": status_code, "msg": "Request validation failed."})
