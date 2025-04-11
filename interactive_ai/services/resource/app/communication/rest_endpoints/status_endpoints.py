# INTEL CONFIDENTIAL
#
# Copyright (C) 2021 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and
# your use of them is governed by the express license under which they were provided to
# you ("License"). Unless the License provides otherwise, you may not use, modify, copy,
# publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is,
# with no express or implied warranties, other than those that are expressly stated
# in the License.

import http
import logging
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from communication.exceptions import FailedHealthCheck
from resource_management.resource_utils import health_check

from geti_fastapi_tools.responses import success_response_rest

logger = logging.getLogger(__name__)

status_router = APIRouter(tags=["Status"])


# Filter to not log healthz endpoint
class HealthFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return record.args and len(record.args) >= 3 and record.args[2] != "/healthz"  # type: ignore


# Add filter to the logger
logging.getLogger("uvicorn.access").addFilter(HealthFilter())


@status_router.get("/healthz")
def get_health_check(
    mongodb: Annotated[bool, Query()] = False,
    kafka: Annotated[bool, Query()] = False,
) -> dict:
    """
    This function checks whether the server is healthy.
    """
    try:
        health_check(mongodb_check=mongodb, kafka_check=kafka)
    except FailedHealthCheck as ex:
        raise HTTPException(status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR.value, detail=str(ex)) from ex

    return success_response_rest()
