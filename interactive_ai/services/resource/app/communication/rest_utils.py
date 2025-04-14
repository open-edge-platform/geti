# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import io
import logging
import os
from pathlib import Path
from typing import Annotated, BinaryIO, TypeVar

import cv2
import numpy as np
from fastapi import Query
from starlette.responses import FileResponse, RedirectResponse, Response, StreamingResponse

from communication.constants import DEFAULT_N_PROJECTS_RETURNED, MAX_N_PROJECTS_RETURNED

from geti_telemetry_tools import unified_tracing
from sc_sdk.repos.project_repo_helpers import ProjectQueryData, ProjectSortBy, ProjectSortDirection, SortDirection

API_GATEWAY_VERSION = 10
CACHE_CONTROL_HEADER = {"Cache-Control": "private, max-age=3600"}
JPEG_EXTENSION = ".jpg"
JPEG_MIME_TYPE = "image/jpeg"
logger = logging.getLogger(__name__)
T = TypeVar("T")


def project_query_data(
    limit: Annotated[int, Query(ge=1, le=MAX_N_PROJECTS_RETURNED)] = DEFAULT_N_PROJECTS_RETURNED,
    skip: Annotated[int, Query(ge=0)] = 0,
    name: Annotated[str, Query()] = "",
    sort_by: Annotated[ProjectSortBy, Query()] = ProjectSortBy.CREATION_DATE,
    sort_direction: Annotated[SortDirection, Query()] = SortDirection.DSC,
    with_size: Annotated[bool, Query()] = False,
) -> ProjectQueryData:
    """
    Create a ProjectQueryData object from items in a FastAPI request object. Raises an
    exception when any of the query parameters are not valid.
    """
    project_sort_direction = ProjectSortDirection[sort_direction.value.upper()]
    return ProjectQueryData(
        limit=limit,
        name=name,
        skip=skip,
        sort_by=sort_by,
        sort_direction=project_sort_direction,
        with_size=with_size,
    )


@unified_tracing
def send_file_from_path_or_url(
    request_host: str,
    file_location: Path | str,
    mimetype: str,
    filename: str | None = None,
) -> Response:
    """
    Sends the file  located at a local path or presigned URL to the user in the form of a starlette response.

    :param request_host: IP of the host that sent the request
    :param file_location: local path or presigned URL pointing to the file
    :param mimetype: Mimetype for the file
    :param filename: If desired, filename for the download. If not specified, it is
    :return: Response object with the file
    """
    if isinstance(file_location, Path):
        # In case the file is locally stored, use send_file to transfer the file
        return FileResponse(path=file_location, media_type=mimetype, filename=filename)
    if isinstance(file_location, str):
        # Create the base URL for the exposed S3 address
        request_base_ip = request_host.replace("http://", "").replace("https://", "").replace("/", "")
        s3_external_address = request_base_ip + "/api/v1/fileservice"

        # Create the URL to redirect the user to
        s3_internal_address = os.environ.get("S3_HOST", "impt-seaweed-fs:8333")
        file_location = file_location.replace(s3_internal_address, s3_external_address)
        file_location = file_location.replace("http://", "https://")

        headers = {
            "Content-Type": mimetype,
            "Accept-Ranges": "bytes",  # Enable byte range support
        }
        return RedirectResponse(url=file_location, headers=headers)
    raise ValueError(f"File must be located at a path or url, found {type(file_location)}")


def convert_numpy_to_jpeg_response(
    media_numpy: np.ndarray, jpg_quality: int = 100, cache: bool = False
) -> StreamingResponse:
    """
    Convert a NumPy array representing an image in RGB format to a JPEG file and return it as a StreamingResponse.

    This function performs the following steps:
    1. Converts the input image from RGB to BGR format.
    2. Encodes the BGR image to JPEG format with the specified quality.
    3. Converts the encoded image to a bytes stream.
    4. Returns the bytes stream as a StreamingResponse.

    :param media_numpy: np.ndarray
        The input image represented as a NumPy array in RGB format.
    :param jpg_quality: int, optional
        The quality of the JPEG encoding (default is 100).
    :param cache: bool, optional
        Whether the client can cache the media response or not (default is False).
    :return: StreamingResponse
        A StreamingResponse containing the encoded JPEG image.
    """
    media_bgr = cv2.cvtColor(media_numpy, cv2.COLOR_RGB2BGR)
    _, buffer_ = cv2.imencode(JPEG_EXTENSION, media_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), jpg_quality])
    stream = io.BytesIO(buffer_.tobytes())
    return stream_to_jpeg_response(stream=stream, cache=cache)


def stream_to_jpeg_response(stream: BinaryIO, cache: bool = False) -> StreamingResponse:
    """
    Transfers a bytes stream to an HTTP response.

    This function sets the appropriate headers and returns the bytes stream as a StreamingResponse.

    :param stream: BinaryIO
        The input bytes stream.
    :param cache: bool, optional
        Whether the client can cache the media response or not (default is False).
    :return: StreamingResponse
        A StreamingResponse containing the bytes stream with the appropriate media type and cache headers.
    """
    headers = CACHE_CONTROL_HEADER if cache else None
    stream.seek(0)
    return StreamingResponse(content=stream, media_type=JPEG_MIME_TYPE, headers=headers)
