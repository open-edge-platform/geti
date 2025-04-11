# INTEL CONFIDENTIAL
#
# Copyright (C) 2022 Intel Corporation
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
import http
import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends
from starlette.responses import JSONResponse

from communication.rest_controllers import DatasetRESTController

from geti_fastapi_tools.dependencies import (
    get_dataset_id,
    get_dataset_revision_id,
    get_optional_task_id,
    get_project_id,
    get_request_json,
    get_workspace_id,
    setup_session_fastapi,
)
from geti_types import ID

logger = logging.getLogger(__name__)

dataset_api_prefix_url = "/api/v1/organizations/{organization_id}/workspaces/{workspace_id}/projects/{project_id}"
dataset_router = APIRouter(
    prefix=dataset_api_prefix_url,
    tags=["Dataset"],
    dependencies=[Depends(setup_session_fastapi)],
)


@dataset_router.get("/datasets")
def get_dataset_storages(
    workspace_id: Annotated[ID, Depends(get_workspace_id)],  # noqa: ARG001
    project_id: Annotated[ID, Depends(get_project_id)],
) -> tuple[Any, int] | dict[str, Any]:
    """Get a dataset"""
    return DatasetRESTController.get_dataset_storages(project_id=project_id)


@dataset_router.post("/datasets")
def post_dataset_storage(
    request_json: Annotated[dict, Depends(get_request_json)],
    workspace_id: Annotated[ID, Depends(get_workspace_id)],  # noqa: ARG001
    project_id: Annotated[ID, Depends(get_project_id)],
) -> JSONResponse:
    """Post a new dataset"""
    return JSONResponse(
        DatasetRESTController.create_dataset_storage(project_id=project_id, data=request_json),
        http.HTTPStatus.CREATED,
    )


@dataset_router.get("/datasets/{dataset_id}")
def get_dataset_storage(
    workspace_id: Annotated[ID, Depends(get_workspace_id)],  # noqa: ARG001
    project_id: Annotated[ID, Depends(get_project_id)],
    dataset_id: Annotated[ID, Depends(get_dataset_id)],
) -> dict[str, Any]:
    """Get information about a dataset"""
    return DatasetRESTController.get_dataset_storage(project_id=project_id, dataset_storage_id=dataset_id)


@dataset_router.delete("/datasets/{dataset_id}")
def delete_dataset_storage(
    workspace_id: Annotated[ID, Depends(get_workspace_id)],  # noqa: ARG001
    project_id: Annotated[ID, Depends(get_project_id)],
    dataset_id: Annotated[ID, Depends(get_dataset_id)],
) -> dict[str, Any]:
    """Delete dataset storage along with its media and annotations"""
    return DatasetRESTController.delete_dataset_storage(project_id=project_id, dataset_storage_id=dataset_id)


@dataset_router.put("/datasets/{dataset_id}")
def put_dataset_storage(
    request_json: Annotated[dict, Depends(get_request_json)],
    workspace_id: Annotated[ID, Depends(get_workspace_id)],  # noqa: ARG001
    project_id: Annotated[ID, Depends(get_project_id)],
    dataset_id: Annotated[ID, Depends(get_dataset_id)],
) -> dict[str, Any]:
    """Update dataset info. It is only supported to edit the dataset's name."""
    return DatasetRESTController.update_dataset_storage(
        project_id=project_id, dataset_storage_id=dataset_id, data=request_json
    )


@dataset_router.get("/datasets/{dataset_id}/statistics")
def get_dataset_storage_statistics(
    workspace_id: Annotated[ID, Depends(get_workspace_id)],  # noqa: ARG001
    project_id: Annotated[ID, Depends(get_project_id)],
    dataset_id: Annotated[ID, Depends(get_dataset_id)],
    task_id: Annotated[ID | None, Depends(get_optional_task_id)],
) -> dict[str, Any]:
    """
    Gets the statistics for a project.

    :param workspace_id: ID of the workspace
    :param project_id: ID of the project
    :param dataset_id: ID of the dataset storage
    :param task_id: If passed, only returns result for this task.
    :return: REST view of the dataset or task level statistics
    """
    if task_id is None:
        return DatasetRESTController.get_dataset_storage_statistics(
            project_id=project_id, dataset_storage_id=dataset_id
        )
    return DatasetRESTController.get_dataset_storage_statistics_for_task(
        project_id=project_id, dataset_storage_id=dataset_id, task_id=task_id
    )


@dataset_router.get(
    "/datasets/{dataset_id}/training_revisions/{dataset_revision_id}",
)
def get_dataset_statistics(
    workspace_id: Annotated[ID, Depends(get_workspace_id)],  # noqa: ARG001
    project_id: Annotated[ID, Depends(get_project_id)],
    dataset_id: Annotated[ID, Depends(get_dataset_id)],
    dataset_revision_id: Annotated[ID, Depends(get_dataset_revision_id)],
) -> dict:
    """
    Gets the statistics for a dataset.

    :param workspace_id: ID of the workspace
    :param project_id: ID of the project
    :param dataset_id: ID of the dataset storage
    :param dataset_revision_id: ID of the dataset
    :return: REST view of the dataset statistics
    """
    return DatasetRESTController.get_dataset_statistics(
        project_id=project_id, dataset_storage_id=dataset_id, dataset_id=dataset_revision_id
    )
