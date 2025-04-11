# INTEL CONFIDENTIAL
#
# Copyright (C) 2023 Intel Corporation
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

"""Endpoints related to project export"""

from typing import Annotated

from fastapi import APIRouter, Depends
from starlette import status
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse

from communication.controllers import ExportController
from communication.dependencies import get_export_operation_id, get_request_domain

from geti_fastapi_tools.dependencies import get_project_identifier, get_user_id_fastapi, setup_session_fastapi
from geti_types import ID, ProjectIdentifier

router = APIRouter(
    prefix="/api/v1/organizations/{organization_id}/workspaces/{workspace_id}/projects/{project_id}",
    dependencies=[Depends(setup_session_fastapi)],
)


@router.post(":export", status_code=status.HTTP_200_OK)
def initialize_project_export(
    project_identifier: Annotated[ProjectIdentifier, Depends(get_project_identifier)],
    user_id: Annotated[ID, Depends(get_user_id_fastapi)],
) -> JSONResponse:
    """Start exporting the selected project"""
    job_id = ExportController.submit_project_export_job(project_identifier=project_identifier, author_id=user_id)
    return JSONResponse({"job_id": job_id})


@router.get("/exports/{export_operation_id}/download", status_code=status.HTTP_200_OK)
def download_exported_project(
    request: Request,  # noqa: ARG001
    project_identifier: Annotated[ProjectIdentifier, Depends(get_project_identifier)],
    export_operation_id: Annotated[ID, Depends(get_export_operation_id)],
    domain_name: Annotated[str, Depends(get_request_domain)],
) -> RedirectResponse:
    """Get the pre-signed URL to download the exported project archive"""
    return ExportController.get_exported_archive_presigned_url(
        project_identifier=project_identifier, export_operation_id=export_operation_id, domain_name=domain_name
    )
