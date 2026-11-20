# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from starlette.responses import Response

from app.api.dependencies import get_media_service, get_ome_rendering_service, get_project
from app.api.schemas.media import OmeChannelViewResponse
from app.api.validators import MediaID
from app.models import Project
from app.models.ome import OmeChannelSettings, OmeImageMetadata
from app.services import MediaService
from app.services.base import InvalidImageError
from app.services.ome.rendering import (
    InvalidChannelViewError,
    InvalidRenderSelectionError,
    OmeRenderingService,
    parse_channel_override,
)

router = APIRouter(prefix="/api/projects/{project_id}/dataset/media", tags=["Media"])

OME_RENDER_RESPONSE_HEADERS: dict[str, Any] = {
    "ETag": {"description": "Quoted hash of the source and effective display settings.", "schema": {"type": "string"}},
    "Cache-Control": {
        "description": "Private caching policy for saved or explicit settings.",
        "schema": {"type": "string"},
    },
}


@router.get(
    "/{media_id}/ome",
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Media is not an OME image"},
        status.HTTP_404_NOT_FOUND: {"description": "Project or media not found"},
    },
)
def get_ome_image_info(
    project: Annotated[Project, Depends(get_project)],
    media_id: MediaID,
    media_service: Annotated[MediaService, Depends(get_media_service)],
) -> OmeImageMetadata:
    """Get OME dimensions, channels, pyramid levels, provenance and fixed training projection."""
    try:
        return media_service.get_ome_image_info(project.id, media_id)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.get(
    "/{media_id}/channel-view",
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Media is not an OME image"},
        status.HTTP_404_NOT_FOUND: {"description": "Project or media not found"},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"description": "OME pixels cannot be read to compute display defaults"},
    },
)
def get_ome_channel_view(
    project: Annotated[Project, Depends(get_project)],
    media_id: MediaID,
    rendering_service: Annotated[OmeRenderingService, Depends(get_ome_rendering_service)],
) -> OmeChannelViewResponse:
    """Get saved channel colors and windows, or sampled server defaults."""
    try:
        view = rendering_service.get_channel_view(project.id, media_id)
        return OmeChannelViewResponse.model_validate(view, from_attributes=True)
    except InvalidImageError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.put(
    "/{media_id}/channel-view",
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Media is not an OME image"},
        status.HTTP_404_NOT_FOUND: {"description": "Project or media not found"},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"description": "Invalid channel indices, colors or intensity windows"},
    },
)
def set_ome_channel_view(
    project: Annotated[Project, Depends(get_project)],
    media_id: MediaID,
    rendering_service: Annotated[OmeRenderingService, Depends(get_ome_rendering_service)],
    body: OmeChannelSettings,
) -> OmeChannelViewResponse:
    """Replace display settings without changing immutable training preprocessing."""
    try:
        view = rendering_service.set_channel_view(project.id, media_id, body)
        return OmeChannelViewResponse.model_validate(view, from_attributes=True)
    except InvalidChannelViewError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.get(
    "/{media_id}/render",
    response_class=Response,
    responses={
        status.HTTP_200_OK: {
            "description": "Rendered OME plane",
            "content": {"image/png": {"schema": {"type": "string", "format": "binary"}}},
            "headers": OME_RENDER_RESPONSE_HEADERS,
        },
        status.HTTP_304_NOT_MODIFIED: {
            "description": "Effective display settings and source are unchanged",
            "headers": OME_RENDER_RESPONSE_HEADERS,
        },
        status.HTTP_400_BAD_REQUEST: {"description": "Media is not OME or the channel override is malformed"},
        status.HTTP_404_NOT_FOUND: {"description": "Project or media not found"},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": "Invalid pyramid level, plane selection or unreadable pixels"
        },
    },
)
def render_ome_plane(  # noqa: PLR0913
    project: Annotated[Project, Depends(get_project)],
    media_id: MediaID,
    rendering_service: Annotated[OmeRenderingService, Depends(get_ome_rendering_service)],
    z: Annotated[int, Query(ge=0)] = 0,
    t: Annotated[int, Query(ge=0)] = 0,
    level: Annotated[int, Query(ge=0)] = 0,
    c: Annotated[
        str | None, Query(description="Zero-based index|min:max$RRGGBB entries; empty hides all channels.")
    ] = None,
    max_size: Annotated[
        int | None, Query(ge=1, le=16384, description="Downsample to fit this maximum side length.")
    ] = None,
    if_none_match: Annotated[str | None, Header()] = None,
) -> Response:
    """Render a plane with saved settings or a non-persistent channel override."""
    try:
        override = parse_channel_override(c) if c is not None else None
        selection = rendering_service.resolve_render(
            project.id, media_id, z=z, t=t, level=level, override=override, max_size=max_size
        )
    except InvalidImageError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)) from error
    except InvalidRenderSelectionError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    headers = {
        "ETag": selection.etag,
        "Cache-Control": "private, no-cache" if c is None else "private, max-age=31536000, immutable",
    }
    if if_none_match is not None and any(
        tag.strip().removeprefix("W/") in ("*", selection.etag) for tag in if_none_match.split(",")
    ):
        return Response(status_code=status.HTTP_304_NOT_MODIFIED, headers=headers)
    try:
        content = rendering_service.render(selection)
    except InvalidImageError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)) from error
    return Response(content=content, media_type="image/png", headers=headers)
