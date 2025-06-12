# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module contains the optimization endpoints"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends

from communication.controllers.optimization_controller import OptimizationController

from geti_fastapi_tools.dependencies import (
    get_model_group_id,
    get_model_id,
    get_project_id,
    get_user_id_fastapi,
    setup_session_fastapi,
)
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


@optimization_router.post(":optimize")
def model_optimization_endpoint(
    project_id: Annotated[ID, Depends(get_project_id)],
    model_group_id: Annotated[ID, Depends(get_model_group_id)],
    model_id: Annotated[ID, Depends(get_model_id)],
    user_id: ID = Depends(get_user_id_fastapi),  # noqa: FAST002
) -> dict:
    """
    Endpoint that can perform model optimization using Post Training Optimization (POT).
    """
    return OptimizationController().start_optimization(
        project_id=project_id,
        model_storage_id=model_group_id,
        model_id=model_id,
        author=user_id,
    )
