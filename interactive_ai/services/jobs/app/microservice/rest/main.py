# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""
This module initializes the FastAPI app and the gRPC server
"""

import os
from contextlib import asynccontextmanager
from multiprocessing import Process

import uvicorn
from fastapi import FastAPI
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse

from microservice.grpc_api.grpc_job_service import GRPCJobService
from microservice.rest.job_endpoints import router as jobs_router

from geti_telemetry_tools import ENABLE_TRACING, FastAPITelemetry, GrpcServerTelemetry


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore # noqa: ANN201
    """
    Defines startup and shutdown of the fastAPI app
    """
    # Startup
    if ENABLE_TRACING:
        GrpcServerTelemetry.instrument()
    grpc_api_server_process = Process(target=GRPCJobService.serve)
    grpc_api_server_process.start()
    yield
    # Shutdown
    grpc_api_server_process.kill()
    grpc_api_server_process.join()
    grpc_api_server_process.close()
    if ENABLE_TRACING:
        FastAPITelemetry.uninstrument(app)
        GrpcServerTelemetry.uninstrument()


app = FastAPI(lifespan=lifespan)
if ENABLE_TRACING:
    FastAPITelemetry.instrument(app)

app.include_router(jobs_router)


# Override the default http exception handler to return error message under 'message' not 'detail'
@app.exception_handler(HTTPException)
def my_exception_handler(request, exception) -> JSONResponse:  # noqa: ANN001, ARG001
    """
    HTTPException handler for the jobs microservice
    """
    return JSONResponse({"message": str(exception.detail)}, status_code=exception.status_code)


if __name__ == "__main__":
    uvicorn_port = int(os.environ.get("HTTP_JOB_SERVICE_PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=uvicorn_port)  # noqa: S104
