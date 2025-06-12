# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
Training related endpoints
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends

from communication.controllers.training_controller import TrainingController

from geti_fastapi_tools.dependencies import (
    get_optional_request_json,
    get_project_id,
    get_user_id_fastapi,
    setup_session_fastapi,
)
from geti_types import ID

logger = logging.getLogger(__name__)

training_api_prefix_url = "/api/v1/organizations/{organization_id}/workspaces/{workspace_id}/projects/{project_id}"

training_router = APIRouter(
    prefix=training_api_prefix_url,
    tags=["Training"],
    dependencies=[Depends(setup_session_fastapi)],
)


@training_router.post(":train")
def train_endpoint(
    project_id: Annotated[ID, Depends(get_project_id)],
    request_json: Annotated[dict, Depends(get_optional_request_json)],
    user_id: ID = Depends(get_user_id_fastapi),  # noqa: FAST002
) -> dict:
    """
    Training endpoint for a project.

    The request body, if provided, should contain the training configuration, specifying e.g. which task to train,
    what model architecture to use and the hyper-parameters.
    The task_id in the training configuration is optional for single-task projects, required for task chain.
    If model_template_id is not provided, the active model will be used.
    """
    if request_json is None:
        request_json = {}

    # Perform the training task
    return TrainingController.train_task(project_id=project_id, author=user_id, raw_train_config=request_json)
