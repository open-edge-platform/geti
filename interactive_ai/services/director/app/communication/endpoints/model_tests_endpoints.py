# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
Endpoints for model tests
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends

from communication.controllers.model_test_controller import ModelTestController
from communication.exceptions import NotEnoughSpaceHTTPException

from geti_fastapi_tools.dependencies import (
    get_prediction_id,
    get_project_id,
    get_request_json,
    get_test_id,
    get_user_id_fastapi,
    get_workspace_id,
    setup_session_fastapi,
)
from geti_types import ID
from iai_core_py.utils.filesystem import check_free_space_for_operation

logger = logging.getLogger(__name__)


model_test_api_prefix_url = "/api/v1/organizations/{organization_id}/workspaces/{workspace_id}/projects/{project_id}"
model_test_router = APIRouter(
    prefix=model_test_api_prefix_url,
    tags=["Model test"],
    dependencies=[Depends(setup_session_fastapi)],
)


@model_test_router.get("/tests")
def get_model_test(
    workspace_id: Annotated[ID, Depends(get_workspace_id)],
    project_id: Annotated[ID, Depends(get_project_id)],
):
    """
    Endpoint to get information about all the model tests in a project.

    All the model tests for the given workspace_id and project_id will be returned.

    :param workspace_id: ID of the workspace to return the model tests for
    :param project_id: ID of the project to return the model tests for
    :return: REST response and return code
    """
    return ModelTestController().get_all_model_test_results(workspace_id, project_id)


@model_test_router.post("/tests")
def post_model_test(
    workspace_id: Annotated[ID, Depends(get_workspace_id)],
    project_id: Annotated[ID, Depends(get_project_id)],
    request_json: Annotated[dict, Depends(get_request_json)],
    user_id: ID = Depends(get_user_id_fastapi),  # noqa: FAST002
):
    """
    Endpoint to start a test job
    """
    check_free_space_for_operation(
        operation="Model test",
        exception_type=NotEnoughSpaceHTTPException,
    )
    return ModelTestController().create_and_submit_job(
        workspace_id=workspace_id,
        project_id=project_id,
        data=request_json,
        author=user_id,
    )


@model_test_router.get("/tests/{test_id}")
def get_model_test_by_id(
    workspace_id: Annotated[ID, Depends(get_workspace_id)],
    project_id: Annotated[ID, Depends(get_project_id)],
    test_id: Annotated[ID, Depends(get_test_id)],
):
    """
    Endpoint to get information about a model test in a project.

    :param workspace_id: ID of the workspace containing the project
    :param project_id: ID of the project containing the test
    :param test_id: ID of the test to get/delete
    :return: REST response and return code
    """
    return ModelTestController().get_model_test_result(
        workspace_id=workspace_id,
        project_id=project_id,
        model_test_result_id=test_id,
    )


@model_test_router.delete("/tests/{test_id}")
def delete_model_test_by_id(
    workspace_id: Annotated[ID, Depends(get_workspace_id)],
    project_id: Annotated[ID, Depends(get_project_id)],
    test_id: Annotated[ID, Depends(get_test_id)],
):
    """
    Endpoint to delete a model test such information from the system.

    :param workspace_id: ID of the workspace containing the project
    :param project_id: ID of the project containing the test
    :param test_id: ID of the test to get/delete
    :return: REST response and return code
    """
    return ModelTestController().delete_model_test_result(
        workspace_id=workspace_id,
        project_id=project_id,
        model_test_result_id=test_id,
    )


@model_test_router.get("/tests/{test_id}/predictions/{prediction_id}")
def model_test_predictions_endpoint(
    workspace_id: Annotated[ID, Depends(get_workspace_id)],
    project_id: Annotated[ID, Depends(get_project_id)],
    test_id: Annotated[ID, Depends(get_test_id)],
    prediction_id: Annotated[ID, Depends(get_prediction_id)],
):
    """
    Endpoint to get a prediction on an image or video_frame within a model test result.

    :param workspace_id: ID of the workspace the project belongs to
    :param project_id: ID of the project the image belongs to
    :param test_id: ID of the test to get/delete
    :param prediction_id: ID of prediction
    :return: REST response and return code
    """
    return ModelTestController().get_model_test_prediction(
        workspace_id=workspace_id,
        project_id=project_id,
        model_test_result_id=test_id,
        prediction_id=prediction_id,
    )
