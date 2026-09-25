# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Endpoints for managing video files uploaded for use as 'video_file' pipeline sources."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.api.dependencies import get_file_name_and_extension, get_source_media_service, get_source_service
from app.api.schemas import SourceMediaDeletionView, SourceMediaUploadView
from app.services import SourceMediaService, SourceService
from app.services.base import ResourceInUseError, ResourceNotFoundError

router = APIRouter(prefix="/api/sources/media", tags=["Sources"])

# Formats supported by OpenCV's VideoCapture for streaming a video file source. Not constrained by
# the dataset media pipeline's thumbnailing requirements, so a broader set of formats is allowed here.
ALLOWED_VIDEO_EXTENSIONS = {"mp4", "avi", "mov", "mkv", "webm", "flv", "wmv", "m4v", "mpg", "mpeg"}


@router.post(
    "",
    response_model=SourceMediaUploadView,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {"description": "Video uploaded successfully"},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"description": "Unsupported video format"},
    },
)
async def upload_source_media(
    file: Annotated[UploadFile, File()],
    file_name_and_extension: Annotated[tuple[str, str], Depends(get_file_name_and_extension)],
    source_media_service: Annotated[SourceMediaService, Depends(get_source_media_service)],
) -> SourceMediaUploadView:
    """Upload a video file to be used as the 'video_path' of a 'video_file' pipeline source.

    The file is stored on the server at a fixed, non-project-scoped location. No dataset media
    record is created; the resulting filesystem path is returned so it can be stored directly as
    the source's 'video_path'.
    """
    name, extension = file_name_and_extension
    if extension.lower() not in ALLOWED_VIDEO_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=(
                f"Unsupported video format '{extension}'. "
                f"Supported formats: {', '.join(sorted(ALLOWED_VIDEO_EXTENSIONS))}."
            ),
        )

    try:
        video_path = await source_media_service.upload(filename=f"{name}.{extension}", file_obj=file.file)
        return SourceMediaUploadView(video_path=str(video_path))
    finally:
        await file.close()


@router.delete(
    "/{source_media_id}",
    response_model=SourceMediaDeletionView,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {"description": "Unreferenced video deleted successfully"},
        status.HTTP_404_NOT_FOUND: {"description": "No uploaded video with this UUID was found"},
        status.HTTP_409_CONFLICT: {"description": "A source is using the media"},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"description": "Malformed source media UUID"},
    },
)
def delete_source_media(
    source_media_id: UUID,
    source_service: Annotated[SourceService, Depends(get_source_service)],
) -> SourceMediaDeletionView:
    """Delete an uploaded video file that is not referenced by any source.

    Uploads are addressed by their UUID (the subdirectory created on upload). Malformed
    UUIDs are rejected with 422 by request validation; a well-formed UUID that does not
    match a stored upload yields 404, and a source still using the media yields 409 with
    nothing deleted.
    """
    try:
        deleted_video_path = source_service.delete_unreferenced_media(source_media_id)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except ResourceInUseError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e
    return SourceMediaDeletionView(deleted_video_path=deleted_video_path)
