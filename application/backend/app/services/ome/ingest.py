# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import errno
import shutil
import stat
import zlib
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import IO, BinaryIO
from zipfile import BadZipFile, ZipFile, ZipInfo

import numpy as np
from PIL import Image

from app.models import MediaStorage
from app.models.ome import ChannelProjection
from app.services.base import InvalidImageError

from .projection import render_channel_projection
from .protocols import OmeImageHandle
from .registry import OmeReaderRegistry, UnsupportedOmeStorageError

_COPY_CHUNK_SIZE: int = 1024 * 1024


class OmeMediaTooLargeError(Exception):
    """The OME payload exceeds the configured size or available storage."""


def check_storage_space(path: Path, size: int, source: Path | None = None) -> None:
    """Reject writes that exceed available disk space."""
    if source is not None and source.stat().st_dev == path.stat().st_dev:
        return
    if size > shutil.disk_usage(path).free:
        raise OmeMediaTooLargeError("Insufficient storage space for the OME image.")


def copy_ome_file(data: IO[bytes], target: Path, max_size: int) -> None:
    """Copy a stream while enforcing the configured limit on actual bytes."""
    total = 0
    with target.open("wb") as output:
        while chunk := data.read(_COPY_CHUNK_SIZE):
            total += len(chunk)
            if total > max_size:
                raise OmeMediaTooLargeError(f"OME image exceeds the maximum size of {max_size} bytes.")
            check_storage_space(target.parent, len(chunk))
            output.write(chunk)


def ome_payload_size(data: BinaryIO | Path) -> int:
    """Get upload size and rewind streams before ingest."""
    if isinstance(data, Path):
        return data.stat().st_size
    data.seek(0, 2)
    size = data.tell()
    data.seek(0)
    return size


def _validate_archive_members(members: list[ZipInfo], root: Path, max_size: int) -> None:
    if not members:
        raise InvalidImageError("The OME archive is empty.")
    size = sum(member.file_size for member in members)
    if size > max_size:
        raise OmeMediaTooLargeError(f"Expanded OME archive exceeds the maximum size of {max_size} bytes.")
    check_storage_space(root.parent, size)
    destinations: set[str] = set()
    for member in members:
        path = PurePosixPath(member.filename)
        mode = member.external_attr >> 16
        if (
            not path.parts
            or path.is_absolute()
            or ".." in path.parts
            or "\\" in member.filename
            or PureWindowsPath(member.filename).drive
            or any(":" in part or part.endswith((".", " ")) for part in path.parts)
            or (stat.S_IFMT(mode) not in (0, stat.S_IFREG, stat.S_IFDIR))
            or member.flag_bits & 1
        ):
            raise InvalidImageError("The OME archive contains an unsafe or encrypted member.")
        destination = path.as_posix().casefold()
        if destination in destinations:
            raise InvalidImageError("The OME archive contains duplicate member paths.")
        destinations.add(destination)


def _find_archive_entrypoint(root: Path, registry: OmeReaderRegistry) -> MediaStorage:
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix.lower() in (".tif", ".tiff"):
            storage = MediaStorage(root=root, entrypoint=path.relative_to(root))
            try:
                registry.get_reader(storage)
            except UnsupportedOmeStorageError:
                continue
            return storage
    raise InvalidImageError("The OME archive does not contain an OME-TIFF entrypoint.")


def extract_ome_archive(data: BinaryIO | Path, root: Path, max_size: int, registry: OmeReaderRegistry) -> MediaStorage:
    """Extract a bounded companion set without allowing links or unsafe member paths."""
    if not isinstance(data, Path):
        data.seek(0)
    try:
        with ZipFile(data) as archive:
            members = archive.infolist()
            _validate_archive_members(members, root, max_size)
            root.mkdir()
            remaining = max_size
            for member in members:
                target = root / member.filename
                if member.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(member) as source:
                    copy_ome_file(source, target, remaining)
                remaining -= target.stat().st_size
    except (BadZipFile, EOFError, NotImplementedError, RuntimeError, zlib.error) as error:
        raise InvalidImageError(f"Cannot extract OME archive: {error}") from error
    except OSError as error:
        if error.errno == errno.ENOSPC:
            raise OmeMediaTooLargeError("Insufficient storage space for the OME archive.") from error
        if error.errno in (errno.ENOTDIR, errno.EISDIR, errno.EEXIST, errno.EINVAL, errno.ENAMETOOLONG):
            raise InvalidImageError("The OME archive contains invalid member paths.") from error
        raise

    return _find_archive_entrypoint(root, registry)


def create_ingest_thumbnail(handle: OmeImageHandle, projection: ChannelProjection) -> Image.Image:
    """Project the lowest-resolution mid-Z/mid-T plane to RGB or single-channel grayscale."""
    if any(channel >= handle.info.size_c for channel in projection.source_channels):
        raise InvalidImageError("Channel projection references a channel outside SizeC.")
    pixels = _read_thumbnail_pixels(handle, list(projection.source_channels))
    rendered = render_channel_projection(pixels, handle.info, projection)
    return Image.fromarray(rendered[..., 0] if rendered.shape[-1] == 1 else rendered)


def _read_thumbnail_pixels(handle: OmeImageHandle, channels: list[int]) -> np.ndarray:
    """Sample large planes without allocating a full-resolution plane."""
    info = handle.info
    level = len(info.pyramid_levels) - 1 if info.pyramid_levels else 0
    width = info.pyramid_levels[level]["width"] if info.pyramid_levels else info.size_x
    height = info.pyramid_levels[level]["height"] if info.pyramid_levels else info.size_y
    if not isinstance(width, int) or not isinstance(height, int) or min(width, height) <= 0:
        raise InvalidImageError("Invalid OME pyramid dimensions.")
    if not channels:
        scale = min(1.0, 256 / max(width, height))
        return np.empty((0, max(1, round(height * scale)), max(1, round(width * scale))), dtype=np.uint8)
    if max(width, height) <= 1024:
        return handle.read_region(level=level, z=info.size_z // 2, t=info.size_t // 2, channels=channels)
    scale = 256 / max(width, height)
    return handle.read_region(
        level=level,
        z=info.size_z // 2,
        t=info.size_t // 2,
        channels=channels,
        output_size=(max(1, round(width * scale)), max(1, round(height * scale))),
    )
