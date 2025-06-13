# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
Entry point of the director microservice.
"""

import http
import logging
import os
from collections import defaultdict
from collections.abc import Sequence
from contextlib import asynccontextmanager

import jsonschema
import pydantic
import uvicorn
from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from starlette.responses import JSONResponse, Response

from active_learning.communication import ActiveLearningKafkaHandler
from communication.endpoints.active_learning_endpoints import active_learning_router
from communication.endpoints.configuration_endpoints import configuration_router
from communication.endpoints.model_tests_endpoints import model_test_router
from communication.endpoints.optimization_endpoints import optimization_router
from communication.endpoints.prediction_endpoints import prediction_router
from communication.endpoints.project_configuration_endpoints import project_configuration_router
from communication.endpoints.status_endpoints import status_router
from communication.endpoints.supported_algorithms_endpoints import supported_algorithms_router
from communication.endpoints.training_configuration_endpoints import training_configuration_router
from communication.endpoints.training_endpoints import training_router
from communication.jobs_client import JobsClient
from communication.kafka_handler import JobKafkaHandler, ProjectKafkaHandler
from coordination.dataset_manager.kafka_handler import (
    DatasetManagementDatasetUpdatedKafkaHandler,
    DatasetManagementMediaAndAnnotationKafkaHandler,
    DatasetManagementProjectEventsKafkaHandler,
)
from environment import get_gpu_provider
from usecases.auto_train.kafka_handler import AutoTrainingKafkaHandler

from geti_fastapi_tools.exceptions import GetiBaseException
from geti_fastapi_tools.responses import error_response_rest
from geti_fastapi_tools.validation import RestApiValidator
from geti_telemetry_tools import ENABLE_TRACING, FastAPITelemetry, KafkaTelemetry
from iai_core.algorithms import ModelTemplateList


def init_model_template_list() -> None:
    """
    Initializes the model template list to speed up project creation and obtaining model storages from DB.
    When called the first time, ModelTemplateList loads all model templates from disk taking several seconds.
    """
    mtl = ModelTemplateList()
    # Workaround (ITEP-67586): change some model defaults for Intel GPU
    if get_gpu_provider() == "intel":
        mtl._model_template_list["Custom_Object_Detection_YOLOX"].model_template.is_default_for_task = True
        mtl._model_template_list["Custom_Object_Detection_Gen3_ATSS"].model_template.is_default_for_task = False


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore # noqa: ANN201
    """
    Defines startup and shutdown of the fastAPI app
    """
    init_model_template_list()

    if ENABLE_TRACING:
        KafkaTelemetry.instrument()
    app.state.kafka_handlers = []
    app.state.kafka_handlers.append(ActiveLearningKafkaHandler())
    app.state.kafka_handlers.append(AutoTrainingKafkaHandler())
    app.state.kafka_handlers.append(DatasetManagementProjectEventsKafkaHandler())
    app.state.kafka_handlers.append(DatasetManagementMediaAndAnnotationKafkaHandler())
    app.state.kafka_handlers.append(DatasetManagementDatasetUpdatedKafkaHandler())
    app.state.kafka_handlers.append(ProjectKafkaHandler())
    app.state.kafka_handlers.append(JobKafkaHandler())
    yield
    for kafka_handler in app.state.kafka_handlers:
        kafka_handler.stop()
    JobsClient().stop()
    if ENABLE_TRACING:
        FastAPITelemetry.uninstrument(app)
        KafkaTelemetry.uninstrument()


app = FastAPI(lifespan=lifespan)

# This can not be in the startup event because adding middleware to the app must be done before startup
if ENABLE_TRACING:
    FastAPITelemetry.instrument(app)
logger = logging.getLogger(__name__)

app.include_router(active_learning_router)
app.include_router(configuration_router)
app.include_router(model_test_router)
app.include_router(optimization_router)
app.include_router(prediction_router)
app.include_router(status_router)
app.include_router(training_router)
app.include_router(supported_algorithms_router)
app.include_router(project_configuration_router)
app.include_router(training_configuration_router)

base_dir = os.path.dirname(__file__) + "/../../../api/schemas/"
mongo_id_schema = RestApiValidator().load_schema_file_as_dict(base_dir + "mongo_id.yaml")


@app.exception_handler(500)
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
def handle_validation_error(request: Request, e: jsonschema.exceptions.ValidationError) -> JSONResponse:  # noqa: ARG001
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


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:  # noqa: ARG001
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


@app.exception_handler(pydantic.ValidationError)
async def pydantic_validation_exception_handler(request: Request, exc: pydantic.ValidationError) -> JSONResponse:  # noqa: ARG001
    """
    Converts a pydantic ValidationError to a better readable Bad request exception.
    """

    def format_location(loc: Sequence[str | int]) -> str:
        """
        Format location path with proper dot notation and array indices.

        Example:
            format_location(['a', 0, 'b', 1, 'c']) -> 'a[0].b[1].c'
        """
        result = ""
        for i, item in enumerate(loc):
            if isinstance(item, int):
                result += f"[{item}]"
            else:
                result += f".{item}" if i > 0 else str(item)
        return result

    errors = [
        {"message": error["msg"], "type": error["type"], "location": format_location(error.get("loc", []))}
        for error in exc.errors()
    ]

    headers = {"Cache-Control": "no-cache"}  # always revalidate
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=jsonable_encoder(
            {
                "error_code": "bad_request",
                "errors": errors,
                "http_status": http.HTTPStatus.BAD_REQUEST.value,
            }
        ),
        headers=headers,
    )


if __name__ == "__main__":
    uvicorn_port = int(os.environ.get("HTTP_DIRECTOR_SERVICE_PORT", "4999"))
    uvicorn.run("main:app", host="0.0.0.0", port=uvicorn_port)  # noqa: S104
