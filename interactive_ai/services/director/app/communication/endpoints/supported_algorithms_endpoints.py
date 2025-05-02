# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query

from communication.controllers.supported_algorithm_controller import SupportedAlgorithmRESTController

from geti_fastapi_tools.dependencies import get_project_identifier, setup_session_fastapi
from geti_types import ProjectIdentifier
from iai_core_py.repos import TaskNodeRepo

logger = logging.getLogger(__name__)

project_api_prefix_url = "/api/v1/organizations/{organization_id}/workspaces/{workspace_id}/projects/{project_id}"
supported_algorithms_router = APIRouter(
    prefix=project_api_prefix_url, tags=["Model"], dependencies=[Depends(setup_session_fastapi)]
)


@supported_algorithms_router.get("/supported_algorithms")
def get_supported_algorithms(
    project_identifier: Annotated[ProjectIdentifier, Depends(get_project_identifier)],
    include_obsolete: Annotated[bool, Query()] = True,
) -> dict[str, Any]:
    """Get information on the algorithms that are available"""
    task_node_repo = TaskNodeRepo(project_identifier)
    project_trainable_task_nodes = task_node_repo.get_trainable_task_nodes()
    project_trainable_tasks = {task_node.task_properties.task_type for task_node in project_trainable_task_nodes}
    return SupportedAlgorithmRESTController.get_supported_algorithms(
        task_types=project_trainable_tasks, include_obsolete=include_obsolete
    )
