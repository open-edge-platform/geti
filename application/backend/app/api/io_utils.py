# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
from collections.abc import Generator
from io import BytesIO
from pathlib import Path
from urllib.parse import quote

from PIL.Image import Image
from starlette.responses import FileResponse, Response, StreamingResponse


def file_iterator(filepath: Path, chunk_size: int = 1024 * 1024) -> Generator[bytes]:
    """
    Stream a file from disk in fixed-size binary chunks.

    This helper opens the file at `filepath` for reading in binary mode and yields its contents in chunks of
    `chunk_size` bytes. It is suitable for use with streaming HTTP responses where the whole file should not be loaded
    into memory at once.

    Args:
        filepath: Path to the file that will be streamed.
        chunk_size: Maximum number of bytes to read and yield per chunk.

    Yields:
        Consecutive chunks of the file content as `bytes` until EOF.
    """
    with filepath.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            yield chunk


def file_etag(path: Path, variant: str) -> str:
    """
    Build a weak ETag for content derived from a file, which changes whenever the file is modified.

    The tag is derived from the file's modification time and size rather than its bytes, hence weak.

    Args:
        path: Path to the source file.
        variant: Identifies how the content is derived from the file, so different derivations never share an ETag.

    Returns:
        Weak ETag value.
    """
    stat = path.stat()
    return f'W/"{variant}-{stat.st_mtime_ns:x}-{stat.st_size:x}"'


def is_not_modified(if_none_match: str | None, etag: str) -> bool:
    """
    Check whether the client already has the current content, according to its If-None-Match header.

    Args:
        if_none_match: Value of the request's If-None-Match header, if any.
        etag: Current ETag of the content.

    Returns:
        True if a 304 Not Modified response can be returned instead of the content.
    """
    if if_none_match is None:
        return False
    # If-None-Match uses weak comparison: the W/ prefix is ignored on both sides
    current = etag.removeprefix("W/")
    return any(tag.strip().removeprefix("W/") in (current, "*") for tag in if_none_match.split(","))


def write_bytes_to_response(
    content: bytes | Generator[bytes], filename: str, media_type: str | None = None, cache_control: str | None = None
) -> Response:
    """
    Stream a binary content to FastAPI response.
    Additionally, method sets file name, MIME type and cache control headers if provided,

    Args:
        content: Binary content.
        filename: File name.
        media_type: Content MIME type, optional.
        cache_control: Cache control header, optional.

    Returns:
        FastAPI Response if content is bytes, StreamingResponse otherwise.
    """
    # Header values must be latin-1, so non-ASCII names (e.g. media names) are sent percent-encoded (RFC 6266)
    quoted_filename = quote(filename, safe="")
    disposition = (
        f'inline; filename="{filename}"'
        if quoted_filename == filename
        else f"inline; filename*=utf-8''{quoted_filename}"
    )
    headers = {"Content-Disposition": disposition}
    if cache_control:
        headers["Cache-Control"] = cache_control
    if isinstance(content, bytes):
        return Response(content=content, media_type=media_type, headers=headers)
    return StreamingResponse(content, media_type=media_type, headers=headers)


def write_image_to_response(image: Image, filename: str, cache_control: str | None = None) -> Response:
    """
    Return a Pillow image as JPEG in a FastAPI response.
    Additionally, method sets file name and cache control headers if provided.

    Args:
        image: Pillow image.
        filename: File name.
        cache_control: Cache control header, optional.

    Returns:
        FastAPI ``Response`` containing the JPEG-encoded image.
    """
    buffer = BytesIO()
    image.save(buffer, format="JPEG")
    return write_bytes_to_response(
        content=buffer.getvalue(), filename=filename, media_type="image/jpeg", cache_control=cache_control
    )


def write_file_to_response(path: Path, filename: str, cache_control: str | None = None) -> FileResponse:
    """
    Return a file from file system as FastAPI FileResponse.
    Additionally, method sets file name and cache control headers if provided.

    Args:
        path: Path to the file.
        filename: File name.
        cache_control: Cache control header, optional.

    Returns:
        FastAPI FileResponse.
    """
    headers = {}
    if cache_control:
        headers["Cache-Control"] = cache_control
    return FileResponse(path=path, filename=filename, headers=headers)
