# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
A module containing logging endpoint and methods
"""

import logging
from datetime import datetime
from http import HTTPStatus

from fastapi import HTTPException, Query
from fastapi.responses import FileResponse
from opentelemetry import trace  # type: ignore[attr-defined]
from starlette.background import BackgroundTask

from endpoints.logs.router import logs_router

from common.endpoint_logger import EndpointLogger
from common.telemetry import DateError, LogType
from common.telemetry import get_archive as get_telemetry_archive

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


@logs_router.get(
    "/",
    responses={
        int(HTTPStatus.OK): {
            "content": {"application/octet-stream": {}},
            "description": "Return the tar.gz archive with logs.",
        },
        int(HTTPStatus.FORBIDDEN): {
            "content": {"text/plain": {}},
            "description": "Access denied - user is not an administrator.",
        },
        int(HTTPStatus.UNPROCESSABLE_ENTITY): {
            "content": {"text/plain": {}},
            "description": "Request validation failed.",
        },
    },
)
@EndpointLogger.extended_logging
async def logs_endpoint(  # noqa: ANN201
    log_type: LogType | None = Query(default=None, alias="type"),
    start_date: datetime | None = Query(default=None),
    end_date: datetime | None = Query(default=None),
):
    """GET logs endpoint."""
    try:
        path_archive = get_telemetry_archive(log_type=log_type, start=start_date, end=end_date)
    except DateError as err:
        raise HTTPException(status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail=str(err)) from err

    # Respond with scheduled background archive removal.
    return FileResponse(
        path_archive,
        media_type="application/octet-stream",
        filename=path_archive.name,
        background=BackgroundTask(path_archive.unlink),
    )
