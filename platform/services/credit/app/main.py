# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import os
from contextlib import asynccontextmanager
from multiprocessing import Process

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

import rest.endpoints  # noqa: F401, pylint: disable=unused-import  # Importing for endpoint registration
from exceptions.custom_exception_handler import custom_exception_handler
from geti_logger_tools.logger_config import initialize_logger
from geti_telemetry_tools import ENABLE_TRACING, FastAPITelemetry, GrpcServerTelemetry
from grpc_api.grpc_service import run_grpc_server
from kafka_events.handler import KafkaHandler
from routers import internal_router, orgs_router, products_router
from utils.existing_orgs_subscription import subscribe_existing_organizations

logger = initialize_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore # noqa: ANN201
    """
    Defines startup and shutdown of the fastAPI app
    """
    # Startup
    if ENABLE_TRACING:
        GrpcServerTelemetry.instrument()
    grpc_api_server_process = Process(target=run_grpc_server)
    grpc_api_server_process.start()
    KafkaHandler()
    if not os.environ.get("TESTING_ENV", False):  # noqa: PLW1508
        subscribe_existing_organizations()
    yield

    # Shutdown
    KafkaHandler().stop()
    grpc_api_server_process.kill()
    grpc_api_server_process.join()
    grpc_api_server_process.close()
    if ENABLE_TRACING:
        FastAPITelemetry.uninstrument(app)
        GrpcServerTelemetry.uninstrument()


app = FastAPI(lifespan=lifespan)
app.add_exception_handler(Exception, custom_exception_handler)
app.add_exception_handler(RequestValidationError, custom_exception_handler)

if ENABLE_TRACING:
    FastAPITelemetry.instrument(app)

app.include_router(products_router, prefix="/api/v1")
app.include_router(orgs_router, prefix="/api/v1")
app.include_router(internal_router, prefix="/api/v1")
