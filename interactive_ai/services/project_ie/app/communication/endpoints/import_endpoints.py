# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
