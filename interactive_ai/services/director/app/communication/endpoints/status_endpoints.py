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

"""
Endpoints to get the status of the server and its projects.
"""

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends
from starlette.responses import JSONResponse

from communication.controllers.status_controller import StatusController

from geti_fastapi_tools.dependencies import (
    get_project_id,
    get_user_id_fastapi,
    get_workspace_id,
    setup_default_session_fastapi,
    setup_session_fastapi,
)
from geti_fastapi_tools.responses import success_response_rest
from geti_types import ID

logger = logging.getLogger(__name__)

status_router = APIRouter(
    tags=["Status"],
)


@status_router.get(
    "/api/v1/organizations/{organization_id}/workspaces/{workspace_id}/projects/{project_id}/status",
    dependencies=[Depends(setup_session_fastapi)],
)
def project_status_endpoint(
    workspace_id: Annotated[ID, Depends(get_workspace_id)],
    project_id: Annotated[ID, Depends(get_project_id)],
) -> dict[str, Any]:
    """
    Endpoint to get the status of a project.

    :param organization_id: ID of the organization
    :param workspace_id: ID of the workspace the project belongs to
    :param project_id: ID of the project to get information for
    :return: REST response and return code
    """
    return StatusController.get_project_status(workspace_id=workspace_id, project_id=project_id)


@status_router.get("/api/v1/status", dependencies=[Depends(setup_default_session_fastapi)])
def server_status_endpoint(
    user_id: ID = Depends(get_user_id_fastapi),  # noqa: FAST002
) -> JSONResponse:
    """
    Endpoint to get the status of the server.

    Note: currently server status only contains the number of running jobs.

    :return: REST response and return code
    """
    return JSONResponse(StatusController.get_server_status(user_id=user_id))


@status_router.get(
    "/api/v1/organizations/{organization_id}/status", dependencies=[Depends(setup_default_session_fastapi)]
)
def organization_status_endpoint(
    user_id: ID = Depends(get_user_id_fastapi),  # noqa: FAST002
) -> JSONResponse:
    """
    Endpoint to get the status of the server for a given organization.

    Note: currently server status only contains the number of running jobs.

    :return: REST response and return code
    """
    return JSONResponse(StatusController.get_server_status(user_id=user_id))


# Filter to not log healthz endpoint
class HealthFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return record.args and len(record.args) >= 3 and record.args[2] != "/healthz"  # type: ignore


# Add filter to the logger
logging.getLogger("uvicorn.access").addFilter(HealthFilter())


@status_router.get("/healthz")
def health_check_director_endpoint() -> dict:
    """
    This endpoint can be used to check if the server is up and ready.
    """
    return success_response_rest()


@status_router.get(
    "/api/v1/organizations/{organization_id}/workspaces/{workspace_id}/projects/{project_id}/incremental_learning_status",
    dependencies=[Depends(setup_session_fastapi)],
)
def incremental_learning_status_endpoint(
    workspace_id: Annotated[ID, Depends(get_workspace_id)],
    project_id: Annotated[ID, Depends(get_project_id)],
) -> dict[str, Any]:
    """
    Endpoint to get the incremental learning status of a project.

    :param workspace_id: ID of the workspace the project belongs to
    :param project_id: ID of the project to get information for
    :return: REST response and return code
    """
    return StatusController.get_incremental_learning_status(workspace_id=workspace_id, project_id=project_id)
