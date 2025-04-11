# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from exceptions.custom_exceptions import InvalidStateTransitionException, NoDatabaseResult, SubscriptionExistsException

logger = logging.getLogger(__name__)


def custom_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Centralized exception handler for FastAPI routes.
    Logs details of the exception and returns a generic error response.

    Args:
        request (Request): The incoming request object.
        exc (Exception): The exception object.

    Returns:
        JSONResponse: A response object with an error message.
    """
    if isinstance(exc, SubscriptionExistsException | ValueError | InvalidStateTransitionException):
        return exception_handler(request=request, exc=exc, status_code=status.HTTP_400_BAD_REQUEST)
    if isinstance(exc, NoDatabaseResult):
        return exception_handler(request=request, exc=exc, status_code=status.HTTP_404_NOT_FOUND)
    if isinstance(exc, RuntimeError):
        return exception_handler(request=request, exc=exc, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    if isinstance(exc, RequestValidationError):
        return validation_exception_handler(request=request, exc=exc, status_code=status.HTTP_400_BAD_REQUEST)
    return exception_handler(request=request, exc=exc, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


def exception_handler(request: Request, exc: Exception, status_code: int) -> JSONResponse:
    """
    Handles exceptions by returning an appropriate response with a status code and message.
    """
    debug_message = (
        f"Custom exception handler called: For request {request.method} {request.url} with exception {exc}. "
        f"Request Headers: {request.headers}. Request Body: {request.body}."
    )
    logger.debug(debug_message)

    match status_code:
        case status.HTTP_400_BAD_REQUEST:
            message = (
                "Invalid request. Please ensure all parameters are present and correctly formatted, and try again."
            )
        case status.HTTP_404_NOT_FOUND:
            message = "Item not found."
        case _:
            message = "Internal server error occurred. Please try again later or contact support for assistance."
            error_log = (
                f"Exception of type {type(exc).__name__} occurred for request {request.method} {request.url}. "
                f"Request Headers: {request.headers}. Request Body: {request.body}. "
                f"Additional details: {str(exc)}"
            )
            logger.error(error_log)

    return JSONResponse(status_code=status_code, content={"message": message})


def validation_exception_handler(request: Request, exc: RequestValidationError, status_code: int) -> JSONResponse:
    """
    Handles RequestValidationError by returning an appropriate response with a status code and message.
    """
    debug_message = (
        f"Custom exception handler called: For request {request.method} {request.url} with exception {exc}. "
        f"Request Headers: {request.headers}. Request Body: {request.body}."
    )
    logger.debug(debug_message)

    error_message = []
    details = exc.errors()
    for error in details:
        field_name = error["loc"][-1]
        error_message.append(f"The field '{field_name}': {error['msg'].lower()}.")
    message = " ".join(error_message)
    return JSONResponse(status_code=status_code, content={"message": message})
