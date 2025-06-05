# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging
from http import HTTPStatus
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from geti_configuration_tools.training_configuration import PartialTrainingConfiguration

from communication.controllers.training_configuration_controller import TrainingConfigurationRESTController
from communication.views.training_configuration_rest_views import TrainingConfigurationRESTViews
from features.feature_flag_provider import FeatureFlag, FeatureFlagProvider

from geti_fastapi_tools.dependencies import get_project_identifier, get_request_json, setup_session_fastapi
from geti_fastapi_tools.exceptions import GetiBaseException
from geti_types import ID, ProjectIdentifier

logger = logging.getLogger(__name__)

training_configuration_prefix_url = (
    "/api/v1/organizations/{organization_id}/workspaces/{workspace_id}/projects/{project_id}"
)
training_configuration_router = APIRouter(
    prefix=training_configuration_prefix_url,
    tags=["Configuration"],
    dependencies=[Depends(setup_session_fastapi)],
)


def get_training_configuration_from_request(
    request_json: Annotated[dict, Depends(get_request_json)],
) -> PartialTrainingConfiguration:
    """Dependency to convert REST request body to PartialTrainingConfiguration."""
    return TrainingConfigurationRESTViews.training_configuration_from_rest(rest_input=request_json)


@training_configuration_router.get("/training_configuration")
def get_training_configuration(
    project_identifier: Annotated[ProjectIdentifier, Depends(get_project_identifier)],
    task_id: Annotated[str | None, Query()] = None,
    model_manifest_id: Annotated[str | None, Query()] = None,
    model_id: Annotated[str | None, Query()] = None,
) -> dict[str, Any]:
    """Retrieve the training configuration"""
    if not FeatureFlagProvider.is_enabled(FeatureFlag.FEATURE_FLAG_NEW_CONFIGURABLE_PARAMETERS):
        raise GetiBaseException(
            message="Feature not available",
            error_code="feature_not_available",
            http_status=HTTPStatus.FORBIDDEN,
        )
    return TrainingConfigurationRESTController.get_configuration(
        project_identifier=project_identifier,
        task_id=ID(task_id) if task_id else None,
        model_manifest_id=model_manifest_id,
        model_id=ID(model_id) if model_id else None,
    )


@training_configuration_router.patch("/training_configuration", status_code=HTTPStatus.NO_CONTENT)
def update_training_configuration(
    project_identifier: Annotated[ProjectIdentifier, Depends(get_project_identifier)],
    update_configuration: Annotated[PartialTrainingConfiguration, Depends(get_training_configuration_from_request)],
) -> None:
    """Update the configuration for a specific project."""
    if not FeatureFlagProvider.is_enabled(FeatureFlag.FEATURE_FLAG_NEW_CONFIGURABLE_PARAMETERS):
        raise GetiBaseException(
            message="Feature not available",
            error_code="feature_not_available",
            http_status=HTTPStatus.FORBIDDEN,
        )

    TrainingConfigurationRESTController.update_configuration(
        project_identifier=project_identifier,
        update_configuration=update_configuration,
    )
