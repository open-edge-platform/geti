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
import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from starlette import status
from starlette.responses import JSONResponse

from communication.rest_controllers.annotation_controller import AnnotationRESTController

from geti_fastapi_tools.dependencies import (
    get_annotation_id,
    get_dataset_id,
    get_dataset_storage_identifier,
    get_image_id,
    get_project_id,
    get_request_json,
    get_user_id_fastapi,
    get_video_id,
    get_workspace_id,
    setup_session_fastapi,
)
from geti_types import ID, DatasetStorageIdentifier, ImageIdentifier, VideoFrameIdentifier

logger = logging.getLogger(__name__)

annotation_api_prefix_url = (
    "/api/v1/organizations/{organization_id}/workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}"
)
annotation_router = APIRouter(
    prefix=annotation_api_prefix_url,
    tags=["Annotation"],
    dependencies=[Depends(setup_session_fastapi)],
)

LabelOnly = Annotated[bool, Query(description="If set to true, only returns the label, not the shape.")]


@annotation_router.post("/media/images/{image_id}/annotations")
def post_image_annotation(
    request_json: Annotated[dict, Depends(get_request_json)],
    dataset_storage_identifier: Annotated[DatasetStorageIdentifier, Depends(get_dataset_storage_identifier)],
    image_id: Annotated[ID, Depends(get_image_id)],
    user_id: ID = Depends(get_user_id_fastapi),  # noqa: FAST002
) -> dict[str, Any]:
    """Post annotation for an image"""
    return AnnotationRESTController.make_image_annotation(
        dataset_storage_identifier=dataset_storage_identifier,
        image_id=image_id,
        data=request_json,
        user_id=user_id,
    )


@annotation_router.get("/media/images/{image_id}/annotations/{annotation_id}")
def get_image_annotation(
    dataset_storage_identifier: Annotated[DatasetStorageIdentifier, Depends(get_dataset_storage_identifier)],
    image_id: Annotated[ID, Depends(get_image_id)],
    annotation_id: Annotated[ID, Depends(get_annotation_id)],
    label_only: LabelOnly = False,
) -> dict[str, Any]:
    """Get annotation for an image"""
    media_identifier = ImageIdentifier(image_id=image_id)
    return AnnotationRESTController.get_annotation(
        dataset_storage_identifier=dataset_storage_identifier,
        annotation_id=annotation_id,
        media_identifier=media_identifier,
        label_only=label_only,
    )


@annotation_router.get("/media/videos/{video_id}/annotations/{annotation_id}")
def get_video_annotations(  # noqa: PLR0913
    workspace_id: Annotated[ID, Depends(get_workspace_id)],  # noqa: ARG001
    project_id: Annotated[ID, Depends(get_project_id)],
    dataset_id: Annotated[ID, Depends(get_dataset_id)],
    video_id: Annotated[ID, Depends(get_video_id)],
    annotation_id: Annotated[ID, Depends(get_annotation_id)],
    label_only: LabelOnly = False,
    start_frame: Annotated[int | None, Query()] = None,
    end_frame: Annotated[int | None, Query()] = None,
    frameskip: Annotated[int, Query(ge=1)] = 1,
) -> JSONResponse:
    """Get annotations for a video"""
    result = AnnotationRESTController.get_video_frame_annotations(
        project_id=project_id,
        dataset_storage_id=dataset_id,
        video_id=video_id,
        annotation_id=annotation_id,
        label_only=label_only,
        start_frame=int(start_frame) if start_frame is not None else start_frame,
        end_frame=int(end_frame) if end_frame is not None else end_frame,
        frameskip=int(frameskip),
    )
    return JSONResponse(result, status_code=status.HTTP_200_OK)


@annotation_router.post(
    "/media/videos/{video_id}/frames/{frame_index}/annotations",
)
def post_video_frame_annotation(
    request_json: Annotated[dict, Depends(get_request_json)],
    dataset_storage_identifier: Annotated[DatasetStorageIdentifier, Depends(get_dataset_storage_identifier)],
    video_id: Annotated[ID, Depends(get_video_id)],
    frame_index: str,
    user_id: ID = Depends(get_user_id_fastapi),  # noqa: FAST002
) -> dict[str, Any]:
    """Post annotations for a video frame"""
    return AnnotationRESTController.make_video_frame_annotation(
        dataset_storage_identifier=dataset_storage_identifier,
        video_id=video_id,
        frame_index=int(frame_index),
        data=request_json,
        user_id=user_id,
    )


@annotation_router.get("/media/videos/{video_id}/frames/{frame_index}/annotations/{annotation_id}")
def get_video_frame_annotation(
    dataset_storage_identifier: Annotated[DatasetStorageIdentifier, Depends(get_dataset_storage_identifier)],
    video_id: Annotated[ID, Depends(get_video_id)],
    frame_index: str,
    annotation_id: Annotated[ID, Depends(get_annotation_id)],
    label_only: LabelOnly = False,
) -> dict[str, Any]:
    """Get annotation for a video frame"""
    media_identifier = VideoFrameIdentifier(video_id=video_id, frame_index=int(frame_index))
    return AnnotationRESTController.get_annotation(
        dataset_storage_identifier=dataset_storage_identifier,
        annotation_id=annotation_id,
        media_identifier=media_identifier,
        label_only=label_only,
    )


@annotation_router.get("/media/videos/{video_id}/range_annotation")
def get_video_range_annotation(
    dataset_storage_identifier: Annotated[DatasetStorageIdentifier, Depends(get_dataset_storage_identifier)],
    video_id: Annotated[ID, Depends(get_video_id)],
) -> dict[str, Any]:
    """Get annotation range for a video"""
    return AnnotationRESTController.get_video_range_annotation(
        dataset_storage_identifier=dataset_storage_identifier,
        video_id=video_id,
    )


@annotation_router.post("/media/videos/{video_id}/range_annotation")
def post_video_range_annotation(
    request_json: Annotated[dict, Depends(get_request_json)],
    dataset_storage_identifier: Annotated[DatasetStorageIdentifier, Depends(get_dataset_storage_identifier)],
    video_id: Annotated[ID, Depends(get_video_id)],
    skip_frame: Annotated[int, Query(ge=0)] = 0,
    user_id: ID = Depends(get_user_id_fastapi),  # noqa: FAST002
) -> dict[str, Any]:
    """Create or update a video annotation range"""
    return AnnotationRESTController.make_video_range_annotation(
        video_annotation_range_data=request_json,
        dataset_storage_identifier=dataset_storage_identifier,
        video_id=video_id,
        user_id=user_id,
        skip_frame=skip_frame,
    )
