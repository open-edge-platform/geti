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
import http
import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from starlette.responses import JSONResponse, Response

from communication.rest_controllers.model_controller import ModelRESTController

from geti_fastapi_tools.dependencies import (
    get_model_group_id,
    get_model_id,
    get_optimized_model_id,
    get_optional_task_id,
    get_project_id,
    get_user_id_fastapi,
    get_workspace_id,
    setup_session_fastapi,
)
from geti_types import ID

logger = logging.getLogger(__name__)

model_api_prefix_url = "/api/v1/organizations/{organization_id}/workspaces/{workspace_id}/projects/{project_id}"
model_router = APIRouter(prefix=model_api_prefix_url, tags=["Model"], dependencies=[Depends(setup_session_fastapi)])


@model_router.get("/model_groups/{model_group_id}/models/{model_id}/statistics")
def get_model_statistics(
    project_id: Annotated[ID, Depends(get_project_id)],
    model_group_id: Annotated[ID, Depends(get_model_group_id)],
    model_id: Annotated[ID, Depends(get_model_id)],
) -> dict[str, Any]:
    """
    Get training statistics for a model. The response will be a list of charts, which
    have one of the following types: text, bar, radial_bar, line or matrix. For each type
    of chart, the response body has a different format. See the schemas for information
    on the format of the response.
    """
    return ModelRESTController.get_model_statistics(
        project_id=project_id, model_storage_id=model_group_id, model_id=model_id
    )


@model_router.get("/models")
def get_all_models(
    project_id: Annotated[ID, Depends(get_project_id)],
    active_only: Annotated[bool, Query(description="If set to true, only returns the active models.")] = True,
) -> dict[str, Any]:
    """
    Get all models for the project. If active_only is set to True, get the active inference models for the project.
    """
    return ModelRESTController.get_all_models(project_id=project_id, active_only=active_only)


@model_router.get("/model_groups")
def get_model_groups(
    project_id: Annotated[ID, Depends(get_project_id)],
    task_id: Annotated[ID | None, Depends(get_optional_task_id)],
    include_lifecycle_stage: bool = False,  # TODO CVS-159532 remove this parameter
) -> JSONResponse:
    """
    Get information on all models and their groups belonging to a project. Each model
    group corresponds with one of the neural network architectures used in the project,
    and each model corresponds with a training revision of a network. Parameter task_id
    can be used to filter the models by task (optional).
    """
    return JSONResponse(
        ModelRESTController.get_all_model_groups(
            project_id=project_id, task_id=task_id, include_lifecycle_stage=include_lifecycle_stage
        )
    )


@model_router.get("/model_groups/{model_group_id}")
def get_model_group(
    project_id: Annotated[ID, Depends(get_project_id)],
    model_group_id: Annotated[ID, Depends(get_model_group_id)],
    include_lifecycle_stage: bool = False,  # TODO CVS-159532 remove this parameter
) -> dict[str, Any]:
    """
    Get information about a specific model group (e.g. EfficientNet-B0), including the
    models in that group. A model group corresponds with one of the neural network
    architectures used in the project, and each model corresponds with a training revision
    of a network.
    """
    return ModelRESTController.get_model_group(
        project_id=project_id, model_storage_id=model_group_id, include_lifecycle_stage=include_lifecycle_stage
    )


@model_router.get("/model_groups/{model_group_id}/models/{model_id}")
def get_model_details(
    project_id: Annotated[ID, Depends(get_project_id)],
    model_group_id: Annotated[ID, Depends(get_model_group_id)],
    model_id: Annotated[ID, Depends(get_model_id)],
) -> dict[str, Any]:
    """
    Get detailed information on a model. Includes the optimized models that belong to this model
    """
    return ModelRESTController.get_model_detail(
        project_id=project_id, model_storage_id=model_group_id, model_id=model_id
    )


@model_router.post("/model_groups/{model_group_id}/models/{model_id}:purge")
def purge_model(
    workspace_id: Annotated[ID, Depends(get_workspace_id)],
    project_id: Annotated[ID, Depends(get_project_id)],
    model_group_id: Annotated[ID, Depends(get_model_group_id)],
    model_id: Annotated[ID, Depends(get_model_id)],
    user_id: ID = Depends(get_user_id_fastapi),  # noqa: FAST002
) -> Response:
    """
    Purge the binaries of a model
    """
    ModelRESTController.purge_model(
        workspace_id=workspace_id,
        project_id=project_id,
        model_storage_id=model_group_id,
        model_id=model_id,
        user_id=user_id,
    )
    return Response(status_code=http.HTTPStatus.NO_CONTENT)


@model_router.get("/model_groups/{model_group_id}/models/{model_id}/export")
def export_model(
    project_id: Annotated[ID, Depends(get_project_id)],
    model_group_id: Annotated[ID, Depends(get_model_group_id)],
    model_id: Annotated[ID, Depends(get_model_id)],
) -> Response:
    """
    Exports a zip file with data for the model. For optimized models, this zip file will contain files that
    can be used to deploy the model.
    """
    model_bytes, filename = ModelRESTController.export_model(
        project_id=project_id, model_storage_id=model_group_id, model_id=model_id, model_only=True
    )
    content = model_bytes.getvalue()
    model_bytes.close()
    return Response(
        headers={"Content-Disposition": f"attachment; filename={filename}"},
        content=content,
        media_type="application/zip",
    )


@model_router.get("/model_groups/{model_group_id}/models/{model_id}/optimized_models/{optimized_model_id}/export")
def export_optimized_model(
    project_id: Annotated[ID, Depends(get_project_id)],
    model_group_id: Annotated[ID, Depends(get_model_group_id)],
    optimized_model_id: Annotated[ID, Depends(get_optimized_model_id)],
    model_only: bool = False,
) -> Response:
    """
    Exports a zip file with data for the optimized model. This zip file will contain
    files that can be used to deploy the model.
    """
    model_bytes, filename = ModelRESTController.export_model(
        project_id=project_id, model_storage_id=model_group_id, model_id=optimized_model_id, model_only=model_only
    )
    content = model_bytes.getvalue()
    model_bytes.close()
    return Response(
        headers={"Content-Disposition": f"attachment; filename={filename}"},
        content=content,
        media_type="application/zip",
    )


@model_router.post("/model_groups/{model_group_id}:activate")
def activate_model_storage(
    workspace_id: Annotated[ID, Depends(get_workspace_id)],
    project_id: Annotated[ID, Depends(get_project_id)],
    model_group_id: Annotated[ID, Depends(get_model_group_id)],
    include_lifecycle_stage: bool = False,  # TODO CVS-159532 remove this parameter
) -> dict[str, Any]:
    """
    Activate and get information on a model group. A model group corresponds with one of
    the neural network architectures used in the project, and each model corresponds with
    a training revision of a network.
    """
    return ModelRESTController.activate_model_storage(
        workspace_id=workspace_id,
        project_id=project_id,
        model_storage_id=model_group_id,
        include_lifecycle_stage=include_lifecycle_stage,
    )
