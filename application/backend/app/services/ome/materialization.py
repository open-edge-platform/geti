# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Bounded-memory, level-zero PNG materialization for training revisions."""

import json
import struct
import zlib
from pathlib import Path
from typing import BinaryIO
from uuid import UUID

import numpy as np

from app.models import Region
from app.models.media import OmePlane
from app.models.ome import OmeImageMetadata, RgbProjection
from app.services.base import InvalidImageError
from app.services.media_service import MediaService
from app.services.ome.projection import render_channel_projection
from app.services.ome.protocols import OmeImageHandle
from app.services.ome.registry import OmeReaderRegistry

OME_PROJECTIONS_FILENAME: str = "ome_channel_projections.json"
# Warm-cache macOS arm64 benchmarks (six settings, eight uint16 workloads, three runs each):
# 1M pixels / 256 rows reduced geometric-mean runtime by 16% versus 256K pixels / 64 rows.
# A 2M-pixel / 512-row budget saved 17%, but peak RSS growth above the import baseline rose
# from 68 to 139 MiB (112 to 207 MiB in float64 validation). Keep the smaller memory tradeoff.
# The separate 8 MiB scanline guard bounds exceptionally wide rows; it is not a total RAM limit.
_STRIP_PIXELS: int = 1024 * 1024
_MAX_STRIP_HEIGHT: int = 256
_MAX_ROW_BYTES: int = 8 * 1024 * 1024


def _write_chunk(stream: BinaryIO, kind: bytes, content: bytes) -> None:
    stream.write(struct.pack(">I", len(content)))
    stream.write(kind)
    stream.write(content)
    stream.write(struct.pack(">I", zlib.crc32(content, zlib.crc32(kind))))


def _write_plane(stream: BinaryIO, handle: OmeImageHandle, info: OmeImageMetadata, plane: OmePlane) -> None:
    """Write PNG scanlines incrementally without allocating the complete plane."""
    projection = info.channel_projection
    components = 3 if isinstance(projection, RgbProjection) else 1
    if info.size_x * components > _MAX_ROW_BYTES:
        raise InvalidImageError("OME training plane exceeds the 8 MiB PNG scanline budget.")
    stream.write(b"\x89PNG\r\n\x1a\n")
    _write_chunk(
        stream, b"IHDR", struct.pack(">IIBBBBB", info.size_x, info.size_y, 8, 2 if components == 3 else 0, 0, 0, 0)
    )
    compressor = zlib.compressobj()
    strip_height = max(1, min(_MAX_STRIP_HEIGHT, _STRIP_PIXELS // info.size_x))
    for y in range(0, info.size_y, strip_height):
        height = min(strip_height, info.size_y - y)
        # Horizontal chunks also bound source/projection buffers for exceptionally wide images.
        output = np.empty((height, info.size_x, components), dtype=np.uint8)
        chunk_width = max(1, _STRIP_PIXELS // height)
        for x in range(0, info.size_x, chunk_width):
            width = min(chunk_width, info.size_x - x)
            pixels = handle.read_region(
                level=0,
                region=Region(x=x, y=y, width=width, height=height),
                z=plane.z_index,
                t=plane.t_index,
                channels=projection.source_channels,
            )
            if pixels.shape != (len(projection.source_channels), height, width):
                raise InvalidImageError("OME reader returned unexpected training region dimensions.")
            output[:, x : x + width] = render_channel_projection(pixels, info, projection)
        for row in output:
            compressed = compressor.compress(b"\x00" + row.tobytes())
            if compressed:
                _write_chunk(stream, b"IDAT", compressed)
    _write_chunk(stream, b"IDAT", compressor.flush())
    _write_chunk(stream, b"IEND", b"")


class OmeTrainingMaterializer:
    """Materialize selected planes using only their immutable ingest-time projections."""

    def __init__(self, media_service: MediaService, directory: Path) -> None:
        self._media_service = media_service
        self._directory = directory
        self._registry = OmeReaderRegistry()
        self._images: dict[UUID, OmeImageMetadata] = {}
        self._planes: dict[str, UUID] = {}

    def materialize(self, project_id: UUID, plane: OmePlane) -> Path:
        """Write one complete level-zero PNG into the caller-owned temporary workspace."""
        info = self._media_service.validate_ome_plane_selection(
            project_id, plane.ome_image_id, z=plane.z_index, t=plane.t_index
        )
        parent = self._media_service.get_media_by_id(project_id, plane.ome_image_id)
        storage = self._media_service.get_media_storage(project_id, parent)
        self._directory.mkdir(parents=True, exist_ok=True)
        path = self._directory / f"{plane.id}.png"
        # The workspace is private to one conversion; never reuse incomplete or stale PNGs.
        stream = path.open("xb")
        try:
            with stream, self._registry.get_reader(storage).open(storage, series=info.series_index) as handle:
                _write_plane(stream, handle, info, plane)
        except BaseException:
            path.unlink(missing_ok=True)
            raise
        self._images[plane.ome_image_id] = info
        self._planes[str(plane.id)] = plane.ome_image_id
        return path

    def write_projections(self, included_ids: list[str]) -> Path | None:
        """Record projections only for source images represented in the converted dataset."""
        included_images = {self._planes[item_id] for item_id in included_ids if item_id in self._planes}
        if not included_images:
            return None
        records = [
            {
                "media_id": str(media_id),
                "container_format": self._images[media_id].container_format,
                "size_c": self._images[media_id].size_c,
                "channel_projection": self._images[media_id].channel_projection.model_dump(mode="json"),
            }
            for media_id in sorted(included_images, key=str)
        ]
        path = self._directory / OME_PROJECTIONS_FILENAME
        path.write_text(json.dumps({"format_version": 1, "images": records}, indent=2) + "\n", encoding="utf-8")
        return path
