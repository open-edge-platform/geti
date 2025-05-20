# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging
from http import HTTPStatus
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query

from communication.controllers.training_configuration_controller import TrainingConfigurationRESTController
from features.feature_flag_provider import FeatureFlag, FeatureFlagProvider

from geti_fastapi_tools.dependencies import get_project_identifier, setup_session_fastapi
from geti_fastapi_tools.exceptions import GetiBaseException
from geti_types import ProjectIdentifier

logger = logging.getLogger(__name__)

training_configuration_prefix_url = (
    "/api/v1/organizations/{organization_id}/workspaces/{workspace_id}/projects/{project_id}"
)
training_configuration_router = APIRouter(
    prefix=training_configuration_prefix_url,
    tags=["Configuration"],
    dependencies=[Depends(setup_session_fastapi)],
)


@training_configuration_router.get("/training_configuration")
def get_training_configuration(
    project_identifier: Annotated[ProjectIdentifier, Depends(get_project_identifier)],
    task_id: Annotated[str | None, Query()] = None,
    model_manifest_id: Annotated[str | None, Query()] = None,
    model_id: Annotated[str | None, Query()] = None,
    exclude_none: Annotated[bool, Query()] = False,
) -> dict[str, Any]:
    """"""
    if not FeatureFlagProvider.is_enabled(FeatureFlag.FEATURE_FLAG_NEW_CONFIGURABLE_PARAMETERS):
        raise GetiBaseException(
            message="Feature not available",
            error_code="feature_not_available",
            http_status=HTTPStatus.FORBIDDEN,
        )
    return TrainingConfigurationRESTController.get_configuration(
        project_identifier=project_identifier,
        task_id=task_id,
        model_manifest_id=model_manifest_id,
        model_id=model_id,
        exclude_none=exclude_none,
    )
