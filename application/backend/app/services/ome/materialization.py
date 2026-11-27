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

from app.models.media import OmePlane
from app.models.ome import OmeImageMetadata, RgbProjection
from app.services.base import InvalidImageError
from app.services.media_service import MediaService
from app.services.ome.projection import PROJECTION_MAX_STRIP_HEIGHT as _MAX_STRIP_HEIGHT
from app.services.ome.projection import PROJECTION_STRIP_PIXELS as _STRIP_PIXELS
from app.services.ome.projection import iter_projected_regions
from app.services.ome.protocols import OmeImageHandle
from app.services.ome.registry import OmeReaderRegistry

OME_PROJECTIONS_FILENAME: str = "ome_channel_projections.json"
# The separate 8 MiB scanline guard bounds exceptionally wide rows; it is not a total RAM limit.
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
    output = np.empty((strip_height, info.size_x, components), dtype=np.uint8)
    for region, pixels in iter_projected_regions(handle, info, projection, z=plane.z_index, t=plane.t_index):
        if region.height != output.shape[0]:
            output = np.empty((region.height, info.size_x, components), dtype=np.uint8)
        output[:, region.x : region.x + region.width] = pixels
        if region.x + region.width == info.size_x:
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

    def get_plane_path(self, plane_id: UUID) -> Path:
        """Return the expected PNG path without reading or materializing the plane."""
        return self._directory / f"{plane_id}.png"

    def materialize(self, project_id: UUID, plane: OmePlane) -> Path:
        """Write one complete level-zero PNG into the caller-owned temporary workspace."""
        info = self._media_service.validate_ome_plane_selection(
            project_id, plane.ome_image_id, z=plane.z_index, t=plane.t_index
        )
        parent = self._media_service.get_media_by_id(project_id, plane.ome_image_id)
        storage = self._media_service.get_media_storage(project_id, parent)
        self._directory.mkdir(parents=True, exist_ok=True)
        path = self.get_plane_path(plane.id)
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
