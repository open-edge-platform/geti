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

"""Endpoints related to project import"""

from typing import Annotated

from fastapi import APIRouter, Depends
from starlette import status
from starlette.responses import JSONResponse

from communication.controllers import ImportController
from communication.models import ImportOperation

from geti_fastapi_tools.dependencies import get_user_id_fastapi, setup_session_fastapi
from geti_types import ID

router = APIRouter(
    prefix="/api/v1/organizations/{organization_id}/workspaces/{workspace_id}/projects",
    dependencies=[Depends(setup_session_fastapi)],
)


@router.post(":import", status_code=status.HTTP_200_OK)
def start_project_import(
    user_id: Annotated[ID, Depends(get_user_id_fastapi)],
    import_operation: ImportOperation,
) -> JSONResponse:
    """Start importing the selected project from the uploaded zip file"""
    job_id = ImportController.submit_project_import_job(import_operation=import_operation, author_id=user_id)
    return JSONResponse({"job_id": job_id})
