# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import http
import logging
import os
from collections import defaultdict
from contextlib import asynccontextmanager

import jsonschema
import uvicorn
from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from starlette.responses import JSONResponse, Response

from communication.kafka_handlers.annotation_kafka_handler import AnnotationKafkaHandler
from communication.kafka_handlers.miscellaneous_kafka_handler import MiscellaneousKafkaHandler
from communication.kafka_handlers.thumb_video_kafka_handler import ThumbVideoKafkaHandler
from communication.rest_endpoints import (
    annotation_router,
    code_deployment_router,
    dataset_router,
    deployment_package_router,
    media_router,
    media_score_router,
    model_router,
    product_info_router,
    project_router,
    server_router,
    status_router,
    workspace_router,
)
from metrics.instruments import initialize_metrics

from geti_fastapi_tools.exceptions import GetiBaseException
from geti_fastapi_tools.responses import error_response_rest
from geti_fastapi_tools.validation import RestApiValidator
from geti_telemetry_tools import ENABLE_TRACING, FastAPITelemetry, KafkaTelemetry
from iai_core.algorithms import ModelTemplateList
from iai_core.utils.exceptions import InvalidProjectDataException


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore # noqa: ANN201
    """
    Defines startup and shutdown of the fastAPI app
    """
    # Startup
    # Initialize the model template list to speed up project creation and obtaining model storages from DB.
    # When called the first time, ModelTemplateList loads all model templates from disk taking several seconds.
    ModelTemplateList()
    initialize_metrics()
    if ENABLE_TRACING:
        KafkaTelemetry.instrument()
    AnnotationKafkaHandler()
    MiscellaneousKafkaHandler()
    ThumbVideoKafkaHandler()
    yield
    # Shutdown
    AnnotationKafkaHandler().stop()
    MiscellaneousKafkaHandler().stop()
    ThumbVideoKafkaHandler().stop()
    if ENABLE_TRACING:
        FastAPITelemetry.uninstrument(app)
        KafkaTelemetry.uninstrument()


app = FastAPI(lifespan=lifespan)

if ENABLE_TRACING:
    FastAPITelemetry.instrument(app)

logger = logging.getLogger(__name__)

app.include_router(annotation_router)
app.include_router(code_deployment_router)
app.include_router(deployment_package_router)
app.include_router(dataset_router)
app.include_router(media_router)
app.include_router(media_score_router)
app.include_router(model_router)
app.include_router(product_info_router)
app.include_router(server_router)
app.include_router(project_router)
app.include_router(status_router)
app.include_router(workspace_router)

base_dir = os.path.dirname(__file__) + "/../../../api/schemas/"
mongo_id_schema = RestApiValidator().load_schema_file_as_dict(base_dir + "mongo_id.yaml")


def handle_error(request, exception) -> JSONResponse:  # noqa: ANN001, ARG001
    """
    Handler for internal server errors
    """
    logger.exception(f"Internal server error: {exception}")
    headers = {"Cache-Control": "no-cache"}  # always revalidate
    return JSONResponse(
        {"internal_server_error": "An internal server error occurred."},
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        headers=headers,
    )


@app.exception_handler(404)
def handle_not_found(request, exception) -> JSONResponse:  # noqa: ANN001, ARG001
    """Handler for 'endpoint not found' errors"""
    message = f"Endpoint {request.url} is not found"
    logger.info(message)
    headers = {"Cache-Control": "no-cache"}  # always revalidate
    return JSONResponse(
        {"endpoint_not_found_response": message},
        status_code=status.HTTP_404_NOT_FOUND,
        headers=headers,
    )


@app.exception_handler(jsonschema.exceptions.ValidationError)
def handle_validation_error(request: Request, e: jsonschema.exceptions.ValidationError) -> JSONResponse:
    """
    Handler for invalid json schemas, improves error message for failed JSON schema validation for common cases.
    """
    if e.validator == "additionalProperties":
        # For the case of additional properties, the default message is informative.
        message = e.message
    elif e.schema.get("description") == mongo_id_schema["description"]:
        # The case of an incorrect mongo ID
        message = (
            f"Invalid value received for field '{e.relative_path[-1]}': This field is expected to be of format "
            f"ID, but found '{e.instance}' instead."
        )
    elif len(e.relative_path) > 0:
        # The case of a field that failed to validate a restriction
        message = (
            f"Invalid value received for field '{e.relative_path[-1]}': This field is expected to have {e.validator} "
            f"{e.validator_value}, but found '{e.instance}' instead."
        )
    else:
        # Other cases
        message = "Server received request with data that cannot be validated"

    # Special case for strings of ID format
    response = error_response_rest("bad_request", message, http.HTTPStatus.BAD_REQUEST.value)
    headers = {"Cache-Control": "no-cache"}  # always revalidate
    return JSONResponse(response, status_code=http.HTTPStatus.BAD_REQUEST.value, headers=headers)


@app.exception_handler(GetiBaseException)
def handle_base_exception(request: Request, e: GetiBaseException) -> Response:
    """
    Base exception handler
    """
    response = error_response_rest(e.error_code, e.message, e.http_status)
    headers: dict[str, str] | None = None
    # 204 skipped as No Content needs to be revalidated
    if e.http_status not in [200, 201, 202, 203, 205, 206, 207, 208, 226] and request.method == "GET":
        headers = {"Cache-Control": "no-cache"}  # always revalidate
    if e.http_status in [204, 304] or e.http_status < 200:
        return Response(status_code=int(e.http_status), headers=headers)
    return JSONResponse(content=response, status_code=int(e.http_status), headers=headers)


@app.exception_handler(InvalidProjectDataException)
def handle_project_data_exception(request: Request, e: InvalidProjectDataException) -> JSONResponse:
    """
    Base exception handler Returns bad request
    """
    response = error_response_rest("bad_request", e.message, http.HTTPStatus.BAD_REQUEST.value)
    headers = {"Cache-Control": "no-cache"}  # always revalidate
    return JSONResponse(content=response, status_code=http.HTTPStatus.BAD_REQUEST.value, headers=headers)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Converts a RequestValidationError to a better readable Bad request exception.
    """
    reformatted_message = defaultdict(list)
    for pydantic_error in exc.errors():
        # `loc` usually is a list with 2 items describing the location of the error.
        # The first item specifies if the error is a body, query or path parameter and
        # the second is the parameter name. Here, only the parameter name is used along
        # with a message explaining what the problem with the parameter is.
        loc, msg = pydantic_error["loc"], pydantic_error["msg"]
        filtered_loc = loc[1:] if loc[0] in ("body", "query", "path") else loc
        field_string = ".".join(str(filtered_loc))  # nested fields with dot-notation
        reformatted_message[field_string].append(msg)

    headers = {"Cache-Control": "no-cache"}  # always revalidate
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=jsonable_encoder(
            {
                "error_code": "bad_request",
                "message": reformatted_message,
                "http_status": http.HTTPStatus.BAD_REQUEST.value,
            }
        ),
        headers=headers,
    )


if __name__ == "__main__":
    uvicorn_port = int(os.environ.get("HTTP_RESOURCE_SERVICE_PORT", "5000"))
    uvicorn.run("main:app", host="0.0.0.0", port=uvicorn_port)  # noqa: S104
