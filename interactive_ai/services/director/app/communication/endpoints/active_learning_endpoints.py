# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
Endpoints for active learning.
"""

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query

from communication.constants import DEFAULT_N_MEDIA_RETURNED, MAX_N_MEDIA_RETURNED
from communication.controllers.active_learning_controller import ActiveLearningController

from geti_fastapi_tools.dependencies import (
    get_optional_task_id,
    get_project_id,
    get_user_id_fastapi,
    get_workspace_id,
    setup_session_fastapi,
)
from geti_types import ID

logger = logging.getLogger(__name__)


active_learning_api_prefix_url = (
    "/api/v1/organizations/{organization_id}/workspaces/{workspace_id}/projects/{project_id}"
)

active_learning_router = APIRouter(
    prefix=active_learning_api_prefix_url,
    tags=["Active Learning"],
    dependencies=[Depends(setup_session_fastapi)],
)


@active_learning_router.get("/datasets/active")
def get_active_media(
    workspace_id: Annotated[ID, Depends(get_workspace_id)],
    project_id: Annotated[ID, Depends(get_project_id)],
    task_id: Annotated[ID | None, Depends(get_optional_task_id)],
    limit: Annotated[int, Query(description="Max number of media to return")] = DEFAULT_N_MEDIA_RETURNED,
    user_id: ID = Depends(get_user_id_fastapi),  # noqa: FAST002
) -> dict[str, Any]:
    """
    Endpoint to get one or more images from the active set for a project.
    """
    limit = min(limit, MAX_N_MEDIA_RETURNED)
    return ActiveLearningController.get_active_set(
        workspace_id=workspace_id,
        project_id=project_id,
        limit=limit,
        user_id=user_id,
        task_id=task_id,
    )
