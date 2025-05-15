# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging
from typing import Annotated, Any

from communication.controllers.project_configuration_controller import ProjectConfigurationRESTController
from fastapi import APIRouter, Depends

from geti_fastapi_tools.dependencies import setup_session_fastapi, get_project_identifier
from geti_types import ProjectIdentifier

logger = logging.getLogger(__name__)

project_configuration_prefix_url = "/api/v1/organizations/{organization_id}/workspaces/{workspace_id}/projects/{project_id}"
project_configuration_router = APIRouter(
    prefix=project_configuration_prefix_url,
    tags=["Configuration"],
    dependencies=[Depends(setup_session_fastapi)],
)


@project_configuration_router.get("/project_configuration")
def get_project_configuration(
    project_identifier: Annotated[ProjectIdentifier, Depends(get_project_identifier)],
) -> dict[str, Any]:
    return ProjectConfigurationRESTController().get_configuration(project_identifier=project_identifier)
