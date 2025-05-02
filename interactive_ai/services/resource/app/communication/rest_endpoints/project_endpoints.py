# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import http
import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Request
from starlette.responses import JSONResponse, Response

from communication.rest_controllers.annotation_template_controller import AnnotationTemplateRESTController
from communication.rest_controllers.media_controller import MediaRESTController
from communication.rest_controllers.project_controller import ProjectRESTController
from communication.rest_utils import project_query_data, stream_to_jpeg_response
from features.feature_flags import FeatureFlag
from managers.project_manager import ProjectManager

from geti_fastapi_tools.dependencies import (
    get_organization_id,
    get_project_id,
    get_request_json,
    get_user_id_fastapi,
    get_workspace_id,
    setup_session_fastapi,
)
from geti_feature_tools import FeatureFlagProvider
from geti_types import ID, DatasetStorageIdentifier, ProjectIdentifier
from iai_core.repos.project_repo_helpers import ProjectQueryData

DEFAULT_THUMBNAIL_JPG_QUALITY = 85

logger = logging.getLogger(__name__)

project_api_prefix_url = "/api/v1/organizations/{organization_id}/workspaces/{workspace_id}"

project_router = APIRouter(
    prefix=project_api_prefix_url,
    tags=["Project"],
    dependencies=[Depends(setup_session_fastapi)],
)


@project_router.get("/projects_names")
def get_projects_names(
    organization_id: Annotated[ID, Depends(get_organization_id)],  # noqa: ARG001
    workspace_id: Annotated[ID, Depends(get_workspace_id)],  # noqa: ARG001
    user_id: ID = Depends(get_user_id_fastapi),  # noqa: FAST002
) -> dict[str, Any]:
    """
    Get all available projects names.
    """
    return ProjectRESTController.get_projects_names(user_id=user_id)


@project_router.get("/projects")
def get_projects(
    request: Request,
    organization_id: Annotated[ID, Depends(get_organization_id)],
    workspace_id: Annotated[ID, Depends(get_workspace_id)],  # noqa: ARG001
    user_id: ID = Depends(get_user_id_fastapi),  # noqa: FAST002
    query_data: ProjectQueryData = Depends(project_query_data),  # noqa: FAST002
) -> tuple[dict[str, Any], int] | dict[str, Any]:
    """
    Get all projects in the workspace. Includes the IDs of the labels, datasets, and
    the tasks and their connections
    """
    return ProjectRESTController.get_projects(
        user_id=user_id,
        organization_id=organization_id,
        query_data=query_data,
        url=str(request.url),
        include_hidden=False,
    )


@project_router.post("/projects")
def post_projects(
    request_json: Annotated[dict, Depends(get_request_json)],
    organization_id: Annotated[ID, Depends(get_organization_id)],
    workspace_id: Annotated[ID, Depends(get_workspace_id)],
    user_id: ID = Depends(get_user_id_fastapi),  # noqa: FAST002
) -> JSONResponse:
    """
    "Create a project. The user must provide a project name, as well as a list of tasks
    and their connections. Please refer to the schema to see all the supported tasks and
    please refer to the examples to see how the project is constructed. At the moment,
    Geti supports projects with a single deep learning task, or with two in a chain
    (Detection -> Classification and Detection -> Segmentation).

    There are label constraints:

    - Detection projects must have at least 1 label provided.
    - A default 'No object' label is automatically created for detection and segmentation
    tasks.
    - Classification projects require at least two labels (top-level, if hierarchical).
    For binary classification, please declare the negative label explicitly.
    - A default 'No class' label is automatically created for classification tasks if
    there are no exclusive groups with 2+ labels. In practice, multilabel classification
    has the empty label, multiclass classification does not.
    - Anomaly project must either have 2 labels provided (one being is_anomalous), or no
    labels provided."
    """
    return JSONResponse(
        ProjectRESTController.create_project(
            data=request_json,
            organization_id=organization_id,
            creator_id=user_id,
            workspace_id=workspace_id,
        ),
        http.HTTPStatus.CREATED,
    )


@project_router.get("/projects/{project_id}")
def get_project(
    organization_id: Annotated[ID, Depends(get_organization_id)],
    workspace_id: Annotated[ID, Depends(get_workspace_id)],  # noqa: ARG001
    project_id: Annotated[ID, Depends(get_project_id)],
    with_size: Annotated[bool, Query()] = False,
    include_deleted_labels: Annotated[bool, Query()] = False,
) -> dict[str, Any]:
    """
    Get information about a project. Includes the IDs of the labels, datasets, and the
    tasks and their connections
    """
    return ProjectRESTController.get_project(
        organization_id=organization_id,
        project_id=project_id,
        with_size=with_size,
        include_deleted_labels=include_deleted_labels,
    )


@project_router.delete("/projects/{project_id}")
def delete_project(
    workspace_id: Annotated[ID, Depends(get_workspace_id)],  # noqa: ARG001
    project_id: Annotated[ID, Depends(get_project_id)],
) -> dict[str, Any]:
    """Delete a project"""
    return ProjectRESTController.delete_project(project_id=project_id)


@project_router.put("/projects/{project_id}")
def edit_project(
    request_json: Annotated[dict, Depends(get_request_json)],
    organization_id: Annotated[ID, Depends(get_organization_id)],
    workspace_id: Annotated[ID, Depends(get_workspace_id)],  # noqa: ARG001
    project_id: Annotated[ID, Depends(get_project_id)],
) -> dict[str, Any]:
    """
    Edit the name of a project or its labels properties (name, color, parent_id). The
    tasks or datasets in a project cannot be edited in this way."""
    return ProjectRESTController.update_project(
        organization_id=organization_id, project_id=project_id, data=request_json
    )


@project_router.get("/projects/{project_id}/thumbnail", response_model=None)
def get_project_thumbnail(
    workspace_id: Annotated[ID, Depends(get_workspace_id)],
    project_id: Annotated[ID, Depends(get_project_id)],
) -> Response:
    """Download a project thumbnail"""
    project = ProjectManager().get_project_by_id(project_id)
    dataset_storage_id = project.training_dataset_storage_id
    dataset_storage_identifier = DatasetStorageIdentifier(
        workspace_id=workspace_id,
        project_id=project_id,
        dataset_storage_id=dataset_storage_id,
    )

    thumbnail = MediaRESTController.get_project_thumbnail(dataset_storage_identifier=dataset_storage_identifier)
    return stream_to_jpeg_response(stream=thumbnail, cache=True)


@project_router.post("/projects/{project_id}/settings/annotation_templates")
def post_annotation_templates(
    request_json: Annotated[dict, Depends(get_request_json)],
    workspace_id: Annotated[ID, Depends(get_workspace_id)],
    project_id: Annotated[ID, Depends(get_project_id)],
) -> dict[str, Any]:
    """Creates an annotation template for the project"""
    if not FeatureFlagProvider.is_enabled(FeatureFlag.FEATURE_FLAG_KEYPOINT_DETECTION):
        raise NotImplementedError

    project_identifier = ProjectIdentifier(
        workspace_id=workspace_id,
        project_id=project_id,
    )
    return AnnotationTemplateRESTController.make_annotation_template(
        project_identifier=project_identifier,
        data=request_json,
    )


@project_router.get("/projects/{project_id}/settings/annotation_templates")
def get_annotation_templates(
    workspace_id: Annotated[ID, Depends(get_workspace_id)],
    project_id: Annotated[ID, Depends(get_project_id)],
) -> dict[str, Any]:
    """Gets a list of AnnotationTemplates belonging to the project"""
    if not FeatureFlagProvider.is_enabled(FeatureFlag.FEATURE_FLAG_KEYPOINT_DETECTION):
        raise NotImplementedError

    project_identifier = ProjectIdentifier(
        workspace_id=workspace_id,
        project_id=project_id,
    )
    return AnnotationTemplateRESTController.get_annotation_templates(project_identifier=project_identifier)
