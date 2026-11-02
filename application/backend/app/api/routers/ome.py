# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Endpoints specific to OME (multi-dimensional microscopy) images: structure, channel display and rendering."""

from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request, status
from starlette.responses import Response

from app.api.dependencies import get_ome_service, get_project
from app.api.io_utils import write_file_to_response
from app.api.schemas.ome import AnnotatedOmePlane, OmeChannelViewResponse, OmeChannelViewSettings, OmeImageInfoView
from app.api.validators import MediaID
from app.models import Project
from app.services import OmeService
from app.services.ome.rendering import InvalidChannelSettingsError
from app.services.ome_service import OmePlaneOutOfRangeError

router = APIRouter(prefix="/api/projects/{project_id}/dataset/media", tags=["Media"])

NOT_OME_IMAGE_RESPONSE = {"description": "Project not found, or media not found or not an OME image"}


@router.get(
    "/{media_id}/ome",
    responses={
        status.HTTP_200_OK: {"description": "Structure of the OME image", "model": OmeImageInfoView},
        status.HTTP_404_NOT_FOUND: NOT_OME_IMAGE_RESPONSE,
    },
)
def get_ome_image_info(
    project: Annotated[Project, Depends(get_project)],
    media_id: MediaID,
    ome_service: Annotated[OmeService, Depends(get_ome_service)],
) -> OmeImageInfoView:
    """Get the structure of an OME image: dimensions, channels and resolution levels"""
    info = ome_service.get_info(project_id=project.id, media_id=media_id)
    return OmeImageInfoView.model_validate(info.model_dump())


@router.get(
    "/{media_id}/channel-view",
    responses={
        status.HTTP_200_OK: {"description": "Channel display settings", "model": OmeChannelViewResponse},
        status.HTTP_404_NOT_FOUND: NOT_OME_IMAGE_RESPONSE,
    },
)
def get_channel_view(
    project: Annotated[Project, Depends(get_project)],
    media_id: MediaID,
    ome_service: Annotated[OmeService, Depends(get_ome_service)],
) -> OmeChannelViewResponse:
    """
    Get the channel display settings of an OME image.

    If the user has not set any, server-computed defaults are returned (`is_default` is true): the channel
    projection used for training, with intensity windows auto-contrasted from a sample of the image.
    """
    channel_view = ome_service.get_channel_view(project_id=project.id, media_id=media_id)
    return OmeChannelViewResponse(settings=channel_view.settings, is_default=channel_view.is_default)


@router.put(
    "/{media_id}/channel-view",
    responses={
        status.HTTP_200_OK: {"description": "Channel display settings updated", "model": OmeChannelViewResponse},
        status.HTTP_404_NOT_FOUND: NOT_OME_IMAGE_RESPONSE,
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": "Channel out of range, window_min >= window_max, or duplicate enabled RGB target"
        },
    },
)
def set_channel_view(
    project: Annotated[Project, Depends(get_project)],
    media_id: MediaID,
    ome_service: Annotated[OmeService, Depends(get_ome_service)],
    body: Annotated[OmeChannelViewSettings, Body()],
) -> OmeChannelViewResponse:
    """
    Set the channel display settings of an OME image, used to render it in the annotator.

    Display settings do not affect training, which always uses a fixed projection computed at upload time.
    """
    try:
        channel_view = ome_service.set_channel_view(project_id=project.id, media_id=media_id, settings=body.settings)
    except InvalidChannelSettingsError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(e))
    return OmeChannelViewResponse(settings=channel_view.settings, is_default=channel_view.is_default)


@router.get(
    "/{media_id}/render",
    response_model=None,
    responses={
        status.HTTP_200_OK: {"description": "Rendered plane", "content": {"image/png": {}}},
        status.HTTP_304_NOT_MODIFIED: {"description": "Rendered plane not modified since the given ETag"},
        status.HTTP_400_BAD_REQUEST: {"description": "Plane or resolution level out of range"},
        status.HTTP_404_NOT_FOUND: NOT_OME_IMAGE_RESPONSE,
    },
)
def render_plane(
    request: Request,
    project: Annotated[Project, Depends(get_project)],
    media_id: MediaID,
    ome_service: Annotated[OmeService, Depends(get_ome_service)],
    z: Annotated[int, Query(ge=0, description="Z index")] = 0,
    t: Annotated[int, Query(ge=0, description="T index")] = 0,
    level: Annotated[int, Query(ge=0, description="Pyramid level, 0 being the full resolution")] = 0,
) -> Response:
    """
    Render a (Z, T) plane of an OME image as an RGB PNG, using its current channel display settings.

    The `ETag` identifies the display settings: it changes whenever they are updated.
    """
    try:
        path, digest = ome_service.render_plane(project_id=project.id, media_id=media_id, z=z, t=t, level=level)
    except OmePlaneOutOfRangeError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    etag = f'"{digest}"'
    if request.headers.get("if-none-match") == etag:
        return Response(status_code=status.HTTP_304_NOT_MODIFIED, headers={"ETag": etag})
    response = write_file_to_response(path=path, filename=f"{media_id}_z{z}_t{t}_r{level}.png", cache_control="private")
    response.headers["ETag"] = etag
    return response


@router.get(
    "/{media_id}/planes",
    responses={
        status.HTTP_200_OK: {"description": "Annotated planes of the OME image", "model": list[AnnotatedOmePlane]},
        status.HTTP_404_NOT_FOUND: NOT_OME_IMAGE_RESPONSE,
    },
)
def list_annotated_planes(
    project: Annotated[Project, Depends(get_project)],
    media_id: MediaID,
    ome_service: Annotated[OmeService, Depends(get_ome_service)],
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> list[AnnotatedOmePlane]:
    """List the annotated (Z, T) planes of an OME image, e.g. to mark them on the Z slider and T timeline"""
    ome_image = ome_service.get_ome_image(project_id=project.id, media_id=media_id)
    planes = ome_service.list_annotated_planes(project=project, ome_image=ome_image, offset=offset, limit=limit)
    return [AnnotatedOmePlane(media_id=plane.id, z_index=plane.z_index, t_index=plane.t_index) for plane in planes]
