# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging
from http import HTTPStatus
from typing import Annotated, Any

from geti_fastapi_tools.exceptions import GetiBaseException

from communication.controllers.project_configuration_controller import ProjectConfigurationRESTController
from fastapi import APIRouter, Depends
from features.feature_flag_provider import FeatureFlagProvider, FeatureFlag

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
    if not FeatureFlagProvider.is_enabled(FeatureFlag.FEATURE_FLAG_NEW_CONFIGURABLE_PARAMETERS):
        raise GetiBaseException(
            message="Feature not available",
            error_code="feature_not_available",
            http_status=HTTPStatus.NOT_FOUND,
        )
    return ProjectConfigurationRESTController().get_configuration(project_identifier=project_identifier)
