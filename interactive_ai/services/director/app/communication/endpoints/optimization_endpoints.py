# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module contains the optimization endpoints"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Request

from communication.controllers.optimization_controller import OptimizationController

from geti_fastapi_tools.dependencies import (
    get_model_group_id,
    get_model_id,
    get_project_id,
    get_user_id_fastapi,
    setup_session_fastapi,
)
from geti_fastapi_tools.deprecation import RestApiDeprecation
from geti_types import ID

logger = logging.getLogger(__name__)

optimization_api_prefix_url = (
    "/api/v1/organizations/{organization_id}/workspaces/{workspace_id}/projects/{project_id}/model_groups/"
    "{model_group_id}/models/{model_id}"
)
optimization_router = APIRouter(
    prefix=optimization_api_prefix_url,
    tags=["Optimization"],
    dependencies=[Depends(setup_session_fastapi)],
)

# Deprecation information for the /optimize endpoint
LEGACY_OPTIMIZE_ENDPOINT = "/optimize"
LEGACY_OPTIMIZE_ENDPOINT_DEPRECATION_DATE = "2024-11-01"
LEGACY_OPTIMIZE_ENDPOINT_SUNSET_DATE = "2025-03-31"
LEGACY_OPTIMIZE_ENDPOINT_INFO = "Deprecated Endpoint. Use the new endpoint `:optimize` instead."


@optimization_router.post("/optimize")
@optimization_router.post(":optimize")
def model_optimization_endpoint(
    request: Request,
    project_id: Annotated[ID, Depends(get_project_id)],
    model_group_id: Annotated[ID, Depends(get_model_group_id)],
    model_id: Annotated[ID, Depends(get_model_id)],
    user_id: ID = Depends(get_user_id_fastapi),  # noqa: FAST002
) -> dict:
    """
    Endpoint that can perform model optimization using Post Training Optimization (POT).
    """
    response = OptimizationController().start_optimization(
        project_id=project_id,
        model_storage_id=model_group_id,
        model_id=model_id,
        author=user_id,
    )

    if request.url.path.endswith(LEGACY_OPTIMIZE_ENDPOINT):
        headers = RestApiDeprecation(
            deprecation_date=LEGACY_OPTIMIZE_ENDPOINT_DEPRECATION_DATE,
            sunset_date=LEGACY_OPTIMIZE_ENDPOINT_SUNSET_DATE,
            additional_info=LEGACY_OPTIMIZE_ENDPOINT_INFO,
        )
        response = headers.add_headers(response)

    return response
