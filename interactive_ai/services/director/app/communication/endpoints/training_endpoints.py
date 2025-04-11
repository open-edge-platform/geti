# INTEL CONFIDENTIAL
#
# Copyright (C) 2021 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and
# your use of them is governed by the express license under which they were provided to
# you ("License"). Unless the License provides otherwise, you may not use, modify, copy,
# publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is,
# with no express or implied warranties, other than those that are expressly stated
# in the License.

"""
Training related endpoints
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Request

from communication.controllers.training_controller import TrainingController

from geti_fastapi_tools.dependencies import (
    get_optional_request_json,
    get_project_id,
    get_user_id_fastapi,
    setup_session_fastapi,
)
from geti_fastapi_tools.deprecation import RestApiDeprecation
from geti_types import ID

logger = logging.getLogger(__name__)

training_api_prefix_url = "/api/v1/organizations/{organization_id}/workspaces/{workspace_id}/projects/{project_id}"

training_router = APIRouter(
    prefix=training_api_prefix_url,
    tags=["Training"],
    dependencies=[Depends(setup_session_fastapi)],
)

# Deprecation information for the /train endpoint
LEGACY_TRAIN_ENDPOINT = "/train"
LEGACY_TRAIN_ENDPOINT_DEPRECATION_DATE = "2024-11-01"
LEGACY_TRAIN_ENDPOINT_SUNSET_DATE = "2025-03-31"
LEGACY_TRAIN_ENDPOINT_INFO = "Deprecated Endpoint. Use the new endpoint `:train` instead."


@training_router.post("/train")
@training_router.post(":train")
def train_endpoint(
    request: Request,
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
    response = TrainingController.train_task(project_id=project_id, author=user_id, raw_train_config=request_json)

    # If the deprecated /train endpoint is used, add deprecation headers
    if request.url.path.endswith(LEGACY_TRAIN_ENDPOINT):
        headers = RestApiDeprecation(
            deprecation_date=LEGACY_TRAIN_ENDPOINT_DEPRECATION_DATE,
            sunset_date=LEGACY_TRAIN_ENDPOINT_SUNSET_DATE,
            additional_info=LEGACY_TRAIN_ENDPOINT_INFO,
        )
        response = headers.add_headers(response)

    return response
