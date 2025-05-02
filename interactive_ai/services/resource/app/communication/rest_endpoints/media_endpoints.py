# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module contains the media endpoints"""

import logging
from enum import Enum
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Request, UploadFile
from starlette.responses import Response

from communication.constants import MAX_N_MEDIA_RETURNED
from communication.exceptions import NotEnoughSpaceException
from communication.rest_controllers.media_controller import MediaRESTController
from communication.rest_data_validator import MediaRestValidator
from communication.rest_utils import convert_numpy_to_jpeg_response, send_file_from_path_or_url, stream_to_jpeg_response
from usecases.dataset_filter import DatasetFilter, DatasetFilterField, DatasetFilterSortDirection

from geti_fastapi_tools.dependencies import (
    get_dataset_id,
    get_dataset_revision_id,
    get_dataset_storage_identifier,
    get_image_id,
    get_project_id,
    get_request_json,
    get_user_id_fastapi,
    get_video_id,
    get_workspace_id,
    setup_session_fastapi,
)
from geti_types import ID, DatasetStorageIdentifier, MediaType
from iai_core_py.utils.filesystem import check_free_space_for_upload

GENERIC_DS_RULE = {
    "rules": [
        {
            "field": "label_id",
            "operator": "not_equal",
            "value": "01234567890123456789abcd",
        },
    ]
}
logger = logging.getLogger(__name__)

media_api_prefix_url = (
    "/api/v1/organizations/{organization_id}/workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}"
)
media_router = APIRouter(prefix=media_api_prefix_url, tags=["Media"], dependencies=[Depends(setup_session_fastapi)])


Skip = Annotated[int, Query(ge=0)]
Fps = Annotated[int, Query(ge=0)]
UploadInfo = Depends(MediaRestValidator.validate_upload_info)


class VideoDisplayType(str, Enum):
    """Display types for a video"""

    stream = "stream"
    thumb = "thumb"
    thumb_stream = "thumb_stream"


class VideoFrameDisplayType(str, Enum):
    """Display types for a video frame"""

    full = "full"
    thumb = "thumb"


class SortBy(str, Enum):
    """Sort by fields for media"""

    media_upload_date = "media_upload_date"
    media_name = "media_name"
    media_width = "media_width"
    media_height = "media_height"
    media_size = "media_size"
    annotation_creation_date = "annotation_creation_date"


class SortDirection(str, Enum):
    """Sort direction for media filtering"""

    asc = "asc"
    dsc = "dsc"


@media_router.post("/media/images")
def post_image(
    request: Request,
    dataset_storage_identifier: Annotated[DatasetStorageIdentifier, Depends(get_dataset_storage_identifier)],
    file: UploadFile = Depends(MediaRestValidator.validate_image_file),  # noqa: FAST002
    upload_info: dict = UploadInfo,
    user_id: ID = Depends(get_user_id_fastapi),  # noqa: FAST002
) -> dict[str, Any]:
    """
    Upload an image to a dataset. Allowed formats are {MediaRestValidator.SUPPORTED_IMAGE_TYPES}.
    Height and width of the images must be between {MIN_MEDIA_SIZE} and {MAX_IMAGE_SIZE}
    pixels. For a classification project, the uploaded image can be annotated directly by
    specifying the labels in the field upload_info. If the image is being uploaded to an
    Anomaly type project then the label id given in 'upload_info' must belong to either
    the 'Anomalous' or the 'Normal' label id of the destination project, it also cannot
    be empty.
    """
    check_free_space_for_upload(
        upload_size=int(request.headers["content-length"]), exception_type=NotEnoughSpaceException
    )
    return MediaRESTController.upload_media(
        user_id=user_id,
        dataset_storage_identifier=dataset_storage_identifier,
        label_info=upload_info,
        media_type=MediaType.IMAGE,
        file_from_request=file,
    )


@media_router.post("/media/videos")
def post_video(
    request: Request,
    dataset_storage_identifier: Annotated[DatasetStorageIdentifier, Depends(get_dataset_storage_identifier)],
    upload_info: dict = UploadInfo,
    file: UploadFile = Depends(MediaRestValidator.validate_video_file),  # noqa: FAST002
    user_id: ID = Depends(get_user_id_fastapi),  # noqa: FAST002
) -> dict[str, Any]:
    """
    Upload a video to a dataset. Allowed formats are {MediaRestValidator.SUPPORTED_VIDEO_TYPES}
    The maximum resolution for videos is {MAX_VIDEO_HEIGHT} x {MAX_VIDEO_WIDTH} and the
    file may not be larger than {MediaRestValidator.MAX_BYTES_SIZE / 1024 ** 3} GB. For a
    classification project, all frames of the uploaded video can be annotated directly by
    specifying the labels in the field upload_info. If the video is uploaded to an Anomaly
    type project then the label id given in 'upload_info' must belong to either the 'Anomalous'
    or 'Normal' label id of the destination project, it also cannot be empty.
    """
    check_free_space_for_upload(
        upload_size=int(request.headers["content-length"]), exception_type=NotEnoughSpaceException
    )
    return MediaRESTController.upload_media(
        user_id=user_id,
        dataset_storage_identifier=dataset_storage_identifier,
        label_info=upload_info,
        media_type=MediaType.VIDEO,
        file_from_request=file,
    )


@media_router.get("/media/images/{image_id}")
def get_image_details(
    dataset_storage_identifier: Annotated[DatasetStorageIdentifier, Depends(get_dataset_storage_identifier)],
    image_id: Annotated[ID, Depends(get_image_id)],
) -> dict[str, Any]:
    """Retrieves detailed information about an image."""
    return MediaRESTController.get_image_detail(
        dataset_storage_identifier=dataset_storage_identifier,
        image_id=image_id,
    )


@media_router.delete("/media/images/{image_id}")
def delete_image(
    dataset_storage_identifier: Annotated[DatasetStorageIdentifier, Depends(get_dataset_storage_identifier)],
    image_id: Annotated[ID, Depends(get_image_id)],
) -> dict[str, Any]:
    """Delete an image from a dataset"""
    return MediaRESTController.delete_image(
        dataset_storage_identifier=dataset_storage_identifier,
        image_id=image_id,
    )


@media_router.get("/media/videos/{video_id}")
def get_video_details(
    dataset_storage_identifier: Annotated[DatasetStorageIdentifier, Depends(get_dataset_storage_identifier)],
    video_id: Annotated[ID, Depends(get_video_id)],
) -> dict[str, Any]:
    """Retrieves detailed information about a video."""
    return MediaRESTController.get_video_detail(
        dataset_storage_identifier=dataset_storage_identifier,
        video_id=video_id,
    )


@media_router.delete("/media/videos/{video_id}")
def delete_video(
    dataset_storage_identifier: Annotated[DatasetStorageIdentifier, Depends(get_dataset_storage_identifier)],
    video_id: Annotated[ID, Depends(get_video_id)],
) -> dict[str, Any]:
    """Delete a video from a dataset"""
    return MediaRESTController.delete_video(
        dataset_storage_identifier=dataset_storage_identifier,
        video_id=video_id,
    )


@media_router.get(
    "/media/videos/{video_id}/display/{display_type}",
)
def get_video_display(  # noqa: ANN201
    request: Request,
    workspace_id: Annotated[ID, Depends(get_workspace_id)],
    project_id: Annotated[ID, Depends(get_project_id)],
    dataset_id: Annotated[ID, Depends(get_dataset_id)],
    video_id: Annotated[ID, Depends(get_video_id)],
    display_type: VideoDisplayType,
):
    """Display a video"""
    dataset_storage_identifier = DatasetStorageIdentifier(
        workspace_id=workspace_id,
        project_id=project_id,
        dataset_storage_id=dataset_id,
    )
    if display_type == VideoDisplayType.stream:
        media_location = MediaRESTController.download_video_stream(
            dataset_storage_identifier=dataset_storage_identifier,
            video_id=video_id,
        )
        return send_file_from_path_or_url(
            request_host=str(request.base_url), file_location=media_location, mimetype="video/mp4"
        )

    if display_type == VideoDisplayType.thumb_stream:
        media_location = MediaRESTController.get_video_thumbnail_stream_location(
            dataset_storage_identifier=dataset_storage_identifier,
            video_id=video_id,
        )

        return send_file_from_path_or_url(
            request_host=str(request.base_url),
            file_location=media_location,
            mimetype="video/mp4",
        )

    if display_type == VideoDisplayType.thumb:
        thumbnail = MediaRESTController.get_video_thumbnail(
            dataset_storage_identifier=dataset_storage_identifier,
            video_id=video_id,
        )
        return stream_to_jpeg_response(stream=thumbnail, cache=True)


@media_router.get("/media/videos/{video_id}/frames/{frame_index}/display/{display_type}")
def video_frame_endpoint(
    dataset_storage_identifier: Annotated[DatasetStorageIdentifier, Depends(get_dataset_storage_identifier)],
    video_id: Annotated[ID, Depends(get_video_id)],
    frame_index: int,
    display_type: VideoFrameDisplayType,
) -> Response:
    """Display a video frame"""
    if display_type == VideoFrameDisplayType.full:
        frame = MediaRESTController.download_video_frame(
            dataset_storage_identifier=dataset_storage_identifier,
            video_id=video_id,
            frame_index=frame_index,
        )
        return convert_numpy_to_jpeg_response(frame, cache=True)
    if display_type == VideoFrameDisplayType.thumb:
        thumb = MediaRESTController.download_video_frame_thumbnail(
            dataset_storage_identifier=dataset_storage_identifier,
            video_id=video_id,
            frame_index=frame_index,
        )
        return convert_numpy_to_jpeg_response(thumb, cache=True)


@media_router.post("/media:query")
def media_query(
    request_json: Annotated[dict, Depends(get_request_json)],
    dataset_storage_identifier: Annotated[DatasetStorageIdentifier, Depends(get_dataset_storage_identifier)],
    skip: Skip = 0,
    limit: Annotated[int, Query(ge=1, le=MAX_N_MEDIA_RETURNED)] = MAX_N_MEDIA_RETURNED,
    sort_direction: SortDirection = SortDirection.asc,
    sort_by: SortBy = SortBy.media_name,
) -> dict:
    """Query media in the dataset"""
    query = {} if request_json is None else request_json
    dataset_filter = DatasetFilter.from_dict(
        query=query,
        limit=limit,
        skip=skip,
        sort_direction=DatasetFilterSortDirection[sort_direction.upper()],
        sort_by=DatasetFilterField[sort_by.upper()],
    )
    return MediaRESTController.get_filtered_items(
        dataset_storage_identifier=dataset_storage_identifier,
        dataset_filter=dataset_filter,
    )


@media_router.post("/media/videos/{video_id}:query")
def video_query(
    request_json: Annotated[dict, Depends(get_request_json)],
    dataset_storage_identifier: Annotated[DatasetStorageIdentifier, Depends(get_dataset_storage_identifier)],
    video_id: Annotated[ID, Depends(get_video_id)],
    skip: Skip = 0,
    limit: Annotated[int, Query(ge=1, le=MAX_N_MEDIA_RETURNED)] = MAX_N_MEDIA_RETURNED,
    fps: Fps = 0,
    include_frame_details: bool = True,
) -> dict:
    """Query frames in a video"""
    # Generic rule to ensure annotation based query is used if no input is provided.
    query = request_json if request_json else GENERIC_DS_RULE
    dataset_filter = DatasetFilter.from_dict(
        query=query,
        limit=limit,
        skip=skip,
    )

    return MediaRESTController.get_filtered_items(
        dataset_storage_identifier=dataset_storage_identifier,
        dataset_filter=dataset_filter,
        video_id=video_id,
        fps=fps,
        include_frame_details=include_frame_details,
    )


@media_router.get(
    "/training_revisions/{dataset_revision_id}/media",
)
def training_revision(
    dataset_storage_identifier: Annotated[DatasetStorageIdentifier, Depends(get_dataset_storage_identifier)],
    dataset_revision_id: Annotated[ID, Depends(get_dataset_revision_id)],
    sort_direction: SortDirection = SortDirection.asc,
    sort_by: SortBy = SortBy.media_name,
    skip: Skip = 0,
    limit: Annotated[int, Query(ge=1, le=MAX_N_MEDIA_RETURNED)] = MAX_N_MEDIA_RETURNED,
) -> dict:
    """Endpoint to get items in a specific dataset in a dataset storage"""
    dataset_filter = DatasetFilter.from_dict(
        query={},
        limit=limit,
        skip=skip,
        sort_direction=DatasetFilterSortDirection[sort_direction.upper()],
        sort_by=DatasetFilterField[sort_by.upper()],
    )
    return MediaRESTController.get_filtered_items(
        dataset_storage_identifier=dataset_storage_identifier,
        dataset_filter=dataset_filter,
        dataset_id=dataset_revision_id,
    )


@media_router.post(
    "/training_revisions/{dataset_revision_id}/media:query",
)
def training_revision_query(
    request_json: Annotated[dict, Depends(get_request_json)],
    dataset_storage_identifier: Annotated[DatasetStorageIdentifier, Depends(get_dataset_storage_identifier)],
    dataset_revision_id: Annotated[ID, Depends(get_dataset_revision_id)],
    sort_direction: Annotated[SortDirection, Query()] = SortDirection.asc,
    sort_by: Annotated[SortBy, Query()] = SortBy.media_name,
    skip: Skip = 0,
    limit: Annotated[int, Query(ge=1, le=MAX_N_MEDIA_RETURNED)] = MAX_N_MEDIA_RETURNED,
) -> dict:
    """Endpoint to query specific items in a dataset in a dataset storage"""
    query: dict = request_json if request_json is not None else {}
    dataset_filter = DatasetFilter.from_dict(
        query=query,
        limit=limit,
        skip=skip,
        sort_direction=DatasetFilterSortDirection[sort_direction.upper()],
        sort_by=DatasetFilterField[sort_by.upper()],
    )
    return MediaRESTController.get_filtered_items(
        dataset_storage_identifier=dataset_storage_identifier,
        dataset_filter=dataset_filter,
        dataset_id=dataset_revision_id,
    )


@media_router.post(
    "/training_revisions/{dataset_revision_id}/media/videos/{video_id}:query",
)
def training_revision_video_query_endpoint(
    request_json: Annotated[dict, Depends(get_request_json)],
    dataset_storage_identifier: Annotated[DatasetStorageIdentifier, Depends(get_dataset_storage_identifier)],
    dataset_revision_id: Annotated[ID, Depends(get_dataset_revision_id)],
    video_id: Annotated[ID, Depends(get_video_id)],
    skip: Skip = 0,
    limit: Annotated[int, Query(ge=1, le=MAX_N_MEDIA_RETURNED)] = MAX_N_MEDIA_RETURNED,
) -> dict:
    """Query media in a specific dataset revision"""
    # Generic rule to ensure annotation based query is used if no input is provided.
    query = request_json if request_json else GENERIC_DS_RULE
    dataset_filter = DatasetFilter.from_dict(query=query, limit=limit, skip=skip)
    return MediaRESTController.get_filtered_items(
        dataset_storage_identifier=dataset_storage_identifier,
        dataset_filter=dataset_filter,
        video_id=video_id,
        dataset_id=dataset_revision_id,
    )
