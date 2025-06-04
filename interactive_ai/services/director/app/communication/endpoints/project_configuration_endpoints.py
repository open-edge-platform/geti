# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging
from http import HTTPStatus
from typing import Annotated, Any

from fastapi import APIRouter, Depends

from communication.views.project_configuration_rest_views import ProjectConfigurationRESTViews
from geti_configuration_tools.project_configuration import PartialProjectConfiguration

from communication.controllers.project_configuration_controller import ProjectConfigurationRESTController
from features.feature_flag_provider import FeatureFlag, FeatureFlagProvider

from geti_fastapi_tools.dependencies import get_project_identifier, setup_session_fastapi
from geti_fastapi_tools.exceptions import GetiBaseException
from geti_types import ProjectIdentifier

logger = logging.getLogger(__name__)

project_configuration_prefix_url = (
    "/api/v1/organizations/{organization_id}/workspaces/{workspace_id}/projects/{project_id}"
)
project_configuration_router = APIRouter(
    prefix=project_configuration_prefix_url,
    tags=["Configuration"],
    dependencies=[Depends(setup_session_fastapi)],
)


@project_configuration_router.get("/project_configuration")
def get_project_configuration(
    project_identifier: Annotated[ProjectIdentifier, Depends(get_project_identifier)],
) -> dict[str, Any]:
    """Retrieve the configuration for a specific project."""
    if not FeatureFlagProvider.is_enabled(FeatureFlag.FEATURE_FLAG_NEW_CONFIGURABLE_PARAMETERS):
        raise GetiBaseException(
            message="Feature not available",
            error_code="feature_not_available",
            http_status=HTTPStatus.FORBIDDEN,
        )
    return ProjectConfigurationRESTController().get_configuration(project_identifier=project_identifier)


@project_configuration_router.patch("/project_configuration", status_code=HTTPStatus.NO_CONTENT)
def update_project_configuration(
    project_identifier: Annotated[ProjectIdentifier, Depends(get_project_identifier)],
    update_configuration: Annotated[PartialProjectConfiguration, Depends(ProjectConfigurationRESTViews.project_configuration_from_rest)],
) -> None:
    """Update the configuration for a specific project."""
    if not FeatureFlagProvider.is_enabled(FeatureFlag.FEATURE_FLAG_NEW_CONFIGURABLE_PARAMETERS):
        raise GetiBaseException(
            message="Feature not available",
            error_code="feature_not_available",
            http_status=HTTPStatus.FORBIDDEN,
        )
    ProjectConfigurationRESTController.update_configuration(
        project_identifier=project_identifier,
        update_configuration=update_configuration,
    )
