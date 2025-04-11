# INTEL CONFIDENTIAL
#
# Copyright (C) 2025 Intel Corporation
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

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query

from communication.controllers.supported_algorithm_controller import SupportedAlgorithmRESTController

from geti_fastapi_tools.dependencies import get_project_identifier, setup_session_fastapi
from geti_types import ProjectIdentifier
from sc_sdk.repos import TaskNodeRepo

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
