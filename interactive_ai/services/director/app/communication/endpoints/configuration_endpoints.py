# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query

from communication.controllers.configuration_controller import ConfigurationRESTController
from communication.exceptions import NotEnoughSpaceHTTPException

from geti_fastapi_tools.dependencies import (
    get_organization_id,
    get_project_id,
    get_request_json,
    get_task_id,
    get_workspace_id,
    setup_session_fastapi,
)
from geti_types import ID
from iai_core_py.utils.filesystem import check_free_space_for_operation

logger = logging.getLogger(__name__)

configuration_prefix_url = "/api/v1/organizations/{organization_id}/workspaces/{workspace_id}/projects/{project_id}"
configuration_router = APIRouter(
    prefix=configuration_prefix_url, tags=["Configuration"], dependencies=[Depends(setup_session_fastapi)]
)


@configuration_router.get("/configuration")
def get_full_configuration(
    organization_id: Annotated[ID, Depends(get_organization_id)],  # noqa: ARG001
    workspace_id: Annotated[ID, Depends(get_workspace_id)],
    project_id: Annotated[ID, Depends(get_project_id)],
) -> dict[str, Any]:
    """
    Endpoint to retrieve full configuration for the project
    """
    return ConfigurationRESTController().get_full_configuration(workspace_id=workspace_id, project_id=project_id)


@configuration_router.post("/configuration")
def post_full_configuration(
    workspace_id: Annotated[ID, Depends(get_workspace_id)],
    project_id: Annotated[ID, Depends(get_project_id)],
    request_json: Annotated[dict, Depends(get_request_json)],
) -> dict[str, Any]:
    """
    Endpoint to retrieve set the configuration for a project
    """
    check_free_space_for_operation(
        operation="Set full configuration",
        exception_type=NotEnoughSpaceHTTPException,
    )
    return ConfigurationRESTController().set_full_configuration(
        workspace_id=workspace_id,
        project_id=project_id,
        set_request=request_json,
    )


@configuration_router.get("/configuration/global")
def get_global_configuration(
    workspace_id: Annotated[ID, Depends(get_workspace_id)],
    project_id: Annotated[ID, Depends(get_project_id)],
) -> dict[str, Any]:
    """
    Endpoint to retrieve configuration for the global components in the project
    """
    return ConfigurationRESTController().get_global_configuration(workspace_id=workspace_id, project_id=project_id)


@configuration_router.post("/configuration/global")
def post_global_configuration(
    workspace_id: Annotated[ID, Depends(get_workspace_id)],
    project_id: Annotated[ID, Depends(get_project_id)],
    request_json: Annotated[dict, Depends(get_request_json)],
) -> dict[str, Any]:
    """
    Endpoint to set configuration for the global components in the project
    """
    check_free_space_for_operation(
        operation="Set global configuration",
        exception_type=NotEnoughSpaceHTTPException,
    )
    return ConfigurationRESTController().validate_and_set_global_configuration(
        workspace_id=workspace_id,
        project_id=project_id,
        set_request=request_json,
    )


@configuration_router.get("/configuration/task_chain")
def get_task_chain_configuration(
    workspace_id: Annotated[ID, Depends(get_workspace_id)],
    project_id: Annotated[ID, Depends(get_project_id)],
) -> dict[str, Any]:
    """
    Endpoint to retrieve configuration for the full task chain
    """
    return ConfigurationRESTController().get_task_chain_configuration(workspace_id=workspace_id, project_id=project_id)


@configuration_router.post("/configuration/task_chain")
def post_task_chain_configuration(
    workspace_id: Annotated[ID, Depends(get_workspace_id)],
    project_id: Annotated[ID, Depends(get_project_id)],
    request_json: Annotated[dict, Depends(get_request_json)],
) -> dict[str, Any]:
    """
    Endpoint to set configuration for the full task chain
    """
    check_free_space_for_operation(
        operation="Set task chain configuration",
        exception_type=NotEnoughSpaceHTTPException,
    )
    return ConfigurationRESTController().validate_and_set_task_chain_configuration(
        workspace_id=workspace_id,
        project_id=project_id,
        set_request=request_json,
    )


@configuration_router.get("/configuration/task_chain/{task_id}")
def get_task_configuration(
    workspace_id: Annotated[ID, Depends(get_workspace_id)],
    project_id: Annotated[ID, Depends(get_project_id)],
    task_id: Annotated[ID, Depends(get_task_id)],
    model_id: Annotated[str | None, Query()] = None,
    algorithm_name: Annotated[str | None, Query()] = None,
) -> dict[str, Any]:
    """
    Endpoint to retrieve configuration for a single task in the task chain, identified by task_id
    """
    model_id_ = ID(model_id) if model_id is not None else None
    return ConfigurationRESTController().get_task_or_model_configuration(
        workspace_id=workspace_id,
        project_id=project_id,
        task_id=task_id,
        model_id=model_id_,
        algorithm_name=algorithm_name,
    )


@configuration_router.post("/configuration/task_chain/{task_id}")
def post_task_configuration(
    workspace_id: Annotated[ID, Depends(get_workspace_id)],
    project_id: Annotated[ID, Depends(get_project_id)],
    task_id: Annotated[ID, Depends(get_task_id)],
    request_json: Annotated[dict, Depends(get_request_json)],
) -> dict[str, Any]:
    """
    Endpoint to set the configuration for a single task in the task chain, identified by task_id
    """
    configuration_controller = ConfigurationRESTController()
    check_free_space_for_operation(
        operation="Set task configuration",
        exception_type=NotEnoughSpaceHTTPException,
    )
    return configuration_controller.set_task_configuration(
        workspace_id=workspace_id,
        project_id=project_id,
        task_id=task_id,
        set_request=request_json,
    )
