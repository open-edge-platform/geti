# INTEL CONFIDENTIAL
#
# Copyright (C) 2024 Intel Corporation
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
"""
This module defines the user-exposed upload endpoints.
Endpoints only call the relevant controller classes and return the response.
"""

import logging
import os
from typing import Annotated

from fastapi import APIRouter, Body, Depends, Header
from starlette.requests import Request
from starlette.responses import Response

from communication.controllers.upload_controller import UploadController
from communication.http_exceptions import (
    PayloadTooLargeException,
    UnsupportedMediaTypeException,
    UnsupportedTUSVersionException,
)

from geti_fastapi_tools.dependencies import get_file_id, setup_session_fastapi
from geti_types import ID

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/organizations/{organization_id}/workspaces/{workspace_id}/projects/uploads",
    dependencies=[Depends(setup_session_fastapi)],
)

MAX_IMPORTABLE_PROJECT_SIZE = int(os.environ.get("MAX_IMPORTABLE_DATASET_SIZE_GB", "200")) * 2**30
TUS_VERSION = "1.0.0,"  # comma-separated list of version of TUS supported by the client


# TUS Protocol as defined in https://tus.io/protocols/resumable-upload.html
@router.options("/resumable")
def tus_options() -> Response:
    """
    TUS options endpoint
    """
    return UploadController.get_options_response()


@router.post("/resumable")
def create_tus_upload(
    request: Request,
    tus_resumable: str = Header(None),  # noqa: FAST002
    upload_length: int = Header(None),  # noqa: FAST002
) -> Response:
    """
    Create a resumable upload
    """
    validate_tus_version(tus_resumable)
    if upload_length > MAX_IMPORTABLE_PROJECT_SIZE:
        raise PayloadTooLargeException(upload_length)

    return UploadController.create_resumable_upload(upload_length=upload_length, request_url=request.url)


@router.head("/resumable/{file_id}")
def tus_upload_head(
    file_id: Annotated[ID, Depends(get_file_id)],
    tus_resumable: str = Header(None),  # noqa: FAST002
) -> Response:
    """
    Get information about a resumable upload process
    """
    validate_tus_version(tus_resumable)
    return UploadController.get_resumable_upload_info(operation_id=file_id)


@router.patch("/resumable/{file_id}")
def tus_upload_patch(
    file_id: Annotated[ID, Depends(get_file_id)],
    data: bytes = Body(None),  # noqa: FAST002
    tus_resumable: str = Header(None),  # noqa: FAST002
    content_type: str = Header(None),  # noqa: FAST002
    upload_offset: int = Header(None),  # noqa: FAST002
) -> Response:
    """
    Add data to a resumable upload
    """
    validate_tus_version(tus_resumable)

    if content_type != "application/offset+octet-stream":
        raise UnsupportedMediaTypeException(received_type=content_type, expected_type="application/offset+octet-stream")

    return UploadController.append_to_multipart_upload(operation_id=file_id, offset=upload_offset, data=data)


def validate_tus_version(tus_resumable: str) -> None:
    """
    Validate tus version based on the supported tus versions

    :param tus_resumable: version of tus used by the client
    :raises UnsupportedTUSVersionException: if tus version used by the client is not supported by the user
    """
    if tus_resumable not in TUS_VERSION.split(","):
        raise UnsupportedTUSVersionException(expected_versions=TUS_VERSION, received_version=tus_resumable)
