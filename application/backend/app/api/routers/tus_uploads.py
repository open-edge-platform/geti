# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""TUS 1.0.0 resumable upload endpoints."""

from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from anyio import to_thread
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from loguru import logger

from app.api.dependencies import get_tus_upload_service
from app.services.tus_upload_service import (
    TUS_VERSION,
    TusUploadConflictError,
    TusUploadError,
    TusUploadInvalidError,
    TusUploadNotFoundError,
    TusUploadService,
    TusUploadTooLargeError,
)

router = APIRouter(prefix="/api/uploads", tags=["Resumable Uploads"])


def _protocol_error(error: Exception) -> HTTPException:
    if isinstance(error, TusUploadNotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error))
    if isinstance(error, TusUploadConflictError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error))
    if isinstance(error, TusUploadTooLargeError):
        return HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=str(error))
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


def _require_version(request: Request) -> None:
    if request.headers.get("Tus-Resumable") != TUS_VERSION:
        raise HTTPException(
            status_code=status.HTTP_412_PRECONDITION_FAILED,
            detail=f"Tus-Resumable must be {TUS_VERSION}.",
            headers={"Tus-Version": TUS_VERSION},
        )


def _state_headers(length: int, offset: int, expires_at: float) -> dict[str, str]:
    return {
        "Tus-Resumable": TUS_VERSION,
        "Upload-Offset": str(offset),
        "Upload-Length": str(length),
        "Upload-Expires": datetime.fromtimestamp(expires_at, tz=UTC).strftime("%a, %d %b %Y %H:%M:%S GMT"),
        "Cache-Control": "no-store",
    }


@router.options("")
async def tus_options(service: Annotated[TusUploadService, Depends(get_tus_upload_service)]) -> Response:
    """Advertise supported TUS protocol capabilities."""
    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
        headers={
            "Tus-Version": TUS_VERSION,
            "Tus-Extension": "creation,expiration,termination",
            "Tus-Max-Size": str(service.max_size),
            "Tus-Resumable": TUS_VERSION,
        },
    )


@router.options("/{upload_id}")
async def tus_upload_options(upload_id: UUID) -> Response:  # noqa: ARG001
    """Advertise protocol version for a specific upload resource."""
    return Response(status_code=status.HTTP_204_NO_CONTENT, headers={"Tus-Version": TUS_VERSION})


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_upload(
    request: Request,
    service: Annotated[TusUploadService, Depends(get_tus_upload_service)],
) -> Response:
    """Create an empty upload resource with a declared byte length."""
    _require_version(request)
    raw_length = request.headers.get("Upload-Length")
    if raw_length is None or not raw_length.isdecimal():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Upload-Length must be a non-negative integer.",
        )
    try:
        upload = await to_thread.run_sync(service.create, int(raw_length), request.headers.get("Upload-Metadata"))
    except TusUploadInvalidError as error:
        raise _protocol_error(error) from error
    logger.info("Created TUS upload {} ({} bytes)", upload.id, upload.length)
    return Response(
        status_code=status.HTTP_201_CREATED,
        headers={
            "Location": str(request.url_for("get_upload", upload_id=str(upload.id))),
            **_state_headers(upload.length, upload.offset, upload.expires_at),
        },
    )


@router.head("/{upload_id}", name="get_upload")
async def get_upload(
    upload_id: UUID,
    request: Request,
    service: Annotated[TusUploadService, Depends(get_tus_upload_service)],
) -> Response:
    """Return the acknowledged offset and upload length."""
    _require_version(request)
    try:
        upload = service.get(upload_id)
    except TusUploadNotFoundError as error:
        raise _protocol_error(error) from error
    return Response(
        status_code=status.HTTP_200_OK,
        headers=_state_headers(upload.length, upload.offset, upload.expires_at),
    )


@router.patch("/{upload_id}", status_code=status.HTTP_204_NO_CONTENT)
async def patch_upload(
    upload_id: UUID,
    request: Request,
    service: Annotated[TusUploadService, Depends(get_tus_upload_service)],
) -> Response:
    """Append bytes to an upload when the supplied offset matches server state."""
    _require_version(request)
    if request.headers.get("Content-Type", "").split(";")[0].strip().lower() != "application/offset+octet-stream":
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Content-Type must be application/offset+octet-stream.",
        )
    raw_offset = request.headers.get("Upload-Offset")
    if raw_offset is None or not raw_offset.isdecimal():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Upload-Offset must be a non-negative integer.",
        )
    try:
        upload = await service.append(upload_id, int(raw_offset), request.stream())
    except TusUploadConflictError as error:
        try:
            upload = service.get(upload_id)
        except TusUploadNotFoundError as missing_error:
            raise _protocol_error(missing_error) from missing_error
        return Response(
            status_code=status.HTTP_409_CONFLICT,
            content=str(error),
            media_type="text/plain",
            headers=_state_headers(upload.length, upload.offset, upload.expires_at),
        )
    except TusUploadError as error:
        raise _protocol_error(error) from error
    logger.debug("TUS upload {} advanced to {}/{} bytes", upload.id, upload.offset, upload.length)
    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
        headers=_state_headers(upload.length, upload.offset, upload.expires_at),
    )


@router.delete("/{upload_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_upload(
    upload_id: UUID,
    request: Request,
    service: Annotated[TusUploadService, Depends(get_tus_upload_service)],
) -> Response:
    """Cancel and remove an upload that has not been consumed."""
    _require_version(request)
    try:
        await service.delete(upload_id)
    except TusUploadError as error:
        raise _protocol_error(error) from error
    return Response(status_code=status.HTTP_204_NO_CONTENT, headers={"Tus-Resumable": TUS_VERSION})
