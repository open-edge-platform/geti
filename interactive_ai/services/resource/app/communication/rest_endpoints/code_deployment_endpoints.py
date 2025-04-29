# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import logging
import pathlib
from enum import Enum
from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from starlette.background import BackgroundTask
from starlette.responses import FileResponse, Response

from communication.rest_controllers.code_deployment_controller import CodeDeploymentRESTController
from communication.rest_controllers.deployment_package_controller import DeploymentPackageRESTController
from communication.rest_utils import send_file_from_path_or_url

from geti_fastapi_tools.dependencies import (
    get_deployment_id,
    get_organization_id,
    get_project_id,
    get_project_identifier,
    get_request_json,
    get_user_id_fastapi,
    get_workspace_id,
    setup_session_fastapi,
)
from geti_types import ID, ProjectIdentifier

logger = logging.getLogger(__name__)

api_project_pattern = "/api/v1/organizations/{organization_id}/workspaces/{workspace_id}/projects/{project_id}"
code_deployment_router = APIRouter(
    prefix=api_project_pattern,
    tags=["Code Deployment"],
    dependencies=[Depends(setup_session_fastapi)],
)

deployment_package_router = APIRouter(
    prefix=api_project_pattern,
    tags=["Deployment Package"],
    dependencies=[Depends(setup_session_fastapi)],
)


@code_deployment_router.post("/code_deployments:prepare")
def prepare_code_deployment(
    request_json: Annotated[dict, Depends(get_request_json)],
    organization_id: Annotated[ID, Depends(get_organization_id)],
    workspace_id: Annotated[ID, Depends(get_workspace_id)],
    project_id: Annotated[ID, Depends(get_project_id)],
    user_id: ID = Depends(get_user_id_fastapi),  # noqa: FAST002
) -> dict:
    """
    This endpoint triggers preparation for code deployment for a specific project.
    For single-task projects (Detection, Segmentation, etc), it will export the only model used.
    For task-chain projects, it will export all the models.
    Only models in OpenVINO IR format are supported
    """
    data = {} if request_json is None else request_json
    return CodeDeploymentRESTController.prepare_for_code_deployment(
        organization_id=organization_id,
        workspace_id=workspace_id,
        project_id=project_id,
        model_list_rest=data,
        user_id=user_id,
    )


@code_deployment_router.get(
    "/code_deployments/{deployment_id}",
)
def get_code_deployment_detail(
    project_identifier: Annotated[ProjectIdentifier, Depends(get_project_identifier)],
    deployment_id: Annotated[ID, Depends(get_deployment_id)],
) -> dict:
    """
    Get details for the code deployment process, which includes the state, the progress,
    models, the creator id and creation time.
    """
    return CodeDeploymentRESTController.get_code_deployment_detail(
        project_identifier=project_identifier,
        code_deployment_id=deployment_id,
    )


class DeploymentPackageType(Enum):
    OVMS = "ovms"
    GETI_SDK = "geti_sdk"


def _cleanup_deployment_package_from_temp(package_path: pathlib.Path) -> None:
    package_path.unlink(missing_ok=True)
    try:
        package_path.parent.rmdir()
    except Exception:
        logger.exception(f"Failed to cleanup deployment package temporary directory {package_path}")


@deployment_package_router.post("/deployment_package:download")
def download_deployment_package(
    request_json: Annotated[dict, Depends(get_request_json)],
    project_identifier: Annotated[ProjectIdentifier, Depends(get_project_identifier)],
) -> Response:
    """
    Download deployment package as zip file
    """
    deployment_package_json = {} if request_json is None else request_json
    package_path = None
    try:
        package_type = DeploymentPackageType(deployment_package_json["package_type"])
    except (KeyError, TypeError, ValueError):
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail=f"Missing package_type in request. Supported types are: {[t.value for t in DeploymentPackageType]}",
        )
    match package_type:
        case DeploymentPackageType.OVMS:
            package_path = DeploymentPackageRESTController.download_ovms_package(
                project_identifier=project_identifier, deployment_package_json=deployment_package_json
            )
        case DeploymentPackageType.GETI_SDK:
            package_path = DeploymentPackageRESTController.download_geti_sdk_package(
                project_identifier=project_identifier, deployment_package_json=deployment_package_json
            )

    return FileResponse(
        path=package_path,
        media_type="application/zip",
        filename=package_path.name,
        background=BackgroundTask(_cleanup_deployment_package_from_temp, package_path),
    )


@code_deployment_router.get(
    "/code_deployments/{deployment_id}/download",
)
def download_code_deployment(
    request: Request,
    project_identifier: Annotated[ProjectIdentifier, Depends(get_project_identifier)],
    deployment_id: Annotated[ID, Depends(get_deployment_id)],
) -> Response:
    """Download the deployed code as a zip file"""
    (
        filepath,
        desired_filename,
    ) = CodeDeploymentRESTController.get_filepath_by_deployment_id(
        project_identifier=project_identifier,
        code_deployment_id=deployment_id,
    )
    return send_file_from_path_or_url(
        request_host=str(request.base_url),
        file_location=filepath,
        mimetype="application/zip",
        filename=desired_filename,
    )
