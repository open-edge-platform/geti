# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import hashlib
import json
from dataclasses import dataclass
from io import BytesIO
from uuid import UUID

import numpy as np
from PIL import Image

from app.models import MediaStorage, OmeImageInfo
from app.models.ome import OmeChannelSetting, OmeChannelSettings, OmeChannelView, OmeImageMetadata
from app.repositories.ome_channel_view_repo import OmeChannelViewRepository
from app.services.base import InvalidImageError, ResourceNotFoundError, ResourceType
from app.services.media_service import MediaService
from app.services.ome.projection import channel_intensity_range, window_channel
from app.services.ome.protocols import OmeImageHandle
from app.services.ome.registry import OmeReaderRegistry, UnsupportedOmeStorageError

_DEFAULT_COLORS: tuple[str, ...] = ("#FF0000", "#00FF00", "#0000FF")
_RENDER_VERSION: int = 1
_RENDER_MEMORY_BUDGET_BYTES: int = 256 * 1024 * 1024
_RENDER_DECODE_RESERVE_BYTES: int = 128 * 1024 * 1024
_RENDER_BASE_BYTES_PER_PIXEL: int = 128
_RENDER_SOURCE_BYTES_PER_PIXEL: int = 32


class InvalidChannelViewError(ValueError):
    """A channel view references channels outside the image."""


class InvalidRenderSelectionError(ValueError):
    """A render selection is out of bounds or exceeds the working-memory budget."""


def parse_channel_override(value: str) -> OmeChannelSettings:
    """Parse Geti's zero-based channel syntax; an empty override hides every channel."""
    try:
        settings = []
        for entry in value.split(",") if value else []:
            channel, window_color = entry.split("|")
            window, color = window_color.split("$")
            minimum, maximum = window.split(":")
            settings.append(
                OmeChannelSetting(
                    channel=int(channel),
                    color=f"#{color}",
                    window_min=float(minimum),
                    window_max=float(maximum),
                )
            )
        return OmeChannelSettings(settings=settings)
    except ValueError as error:
        raise InvalidChannelViewError("Malformed channel override.") from error


def composite_channels(pixels: np.ndarray, settings: list[OmeChannelSetting]) -> np.ndarray:
    """Additively composite CHW pixels, in setting order, into clipped uint8 RGB."""
    if pixels.ndim != 3 or pixels.shape[0] != len(settings):
        raise InvalidImageError("Pixel channels do not match display settings.")
    if np.iscomplexobj(pixels):
        raise InvalidImageError("Complex OME pixels cannot be rendered.")
    output = np.zeros((*pixels.shape[1:], 3), dtype=np.float64)
    for plane, setting in zip(pixels, settings):
        if setting.enabled:
            color = np.array([int(setting.color[index : index + 2], 16) for index in (1, 3, 5)])
            intensity = window_channel(plane, setting.window_min, setting.window_max)
            output += intensity[..., np.newaxis] * (color / 255)
    return output.clip(0, 255).astype(np.uint8)


@dataclass(frozen=True)
class OmeRender:
    """A resolved render, allowing HTTP revalidation before full-plane rendering."""

    etag: str
    storage: MediaStorage
    info: OmeImageMetadata
    settings: OmeChannelSettings
    z: int
    t: int
    level: int
    output_size: tuple[int, int] | None


class OmeRenderingService:
    """Resolve display views and render planes in memory independently of training."""

    def __init__(self, media_service: MediaService) -> None:
        self.media_service = media_service
        self.registry = OmeReaderRegistry()

    def _repository(self, project_id: UUID) -> OmeChannelViewRepository:
        return OmeChannelViewRepository(str(project_id), self.media_service.db_session)

    def _open_image(self, storage: MediaStorage) -> OmeImageHandle:
        try:
            return self.registry.get_reader(storage).open(storage)
        except UnsupportedOmeStorageError as error:
            raise InvalidImageError("The OME image payload is no longer readable.") from error

    def _context(self, project_id: UUID, media_id: UUID) -> tuple[OmeImageMetadata, MediaStorage, str]:
        info = self.media_service.get_ome_image_info(project_id, media_id)
        media = self.media_service.get_media_by_id(project_id, media_id)
        storage = self.media_service.get_media_storage(project_id, media)
        if not storage.effective_path.is_file():
            raise ResourceNotFoundError(ResourceType.MEDIA, str(media_id), "OME image payload was not found.")
        files = (
            sorted(path for path in storage.root.rglob("*") if path.is_file())
            if storage.is_directory
            else [storage.root]
        )
        versions = []
        for path in files:
            try:
                stat = path.stat()
            except FileNotFoundError as error:
                raise ResourceNotFoundError(
                    ResourceType.MEDIA, str(media_id), "OME image payload was not found."
                ) from error
            versions.append(
                (
                    path.relative_to(storage.root).as_posix() if storage.is_directory else "",
                    stat.st_size,
                    stat.st_mtime_ns,
                    stat.st_ctime_ns,
                )
            )
        version = hashlib.sha256(json.dumps(versions).encode()).hexdigest()
        return info, storage, version

    @staticmethod
    def _validate_settings(settings: OmeChannelSettings, info: OmeImageInfo) -> None:
        if any(setting.channel >= info.size_c for setting in settings.settings):
            raise InvalidChannelViewError("Display channel index is outside SizeC.")

    def get_channel_view(self, project_id: UUID, media_id: UUID) -> OmeChannelView:
        """Return the saved view or stable, bounded percentile-based defaults."""
        info, storage, _ = self._context(project_id, media_id)
        return self._get_channel_view(project_id, media_id, info, storage)

    def _get_channel_view(
        self, project_id: UUID, media_id: UUID, info: OmeImageInfo, storage: MediaStorage
    ) -> OmeChannelView:
        row = self._repository(project_id).get_by_id(str(media_id))
        if row is not None:
            return OmeChannelView(settings=row.settings, is_default=False)
        return self._default_view(info, storage)

    def _default_view(self, info: OmeImageInfo, storage: MediaStorage) -> OmeChannelView:
        """Compute display-only defaults without persisting them.

        Enable up to the first three channels, using 1st/99th-percentile windows
        from a sample with a maximum side of 256 pixels at mid-Z/mid-T of the lowest
        resolution level. Constant/non-finite samples and disabled channels use
        declared or dtype intensity ranges. Prefer metadata colors; otherwise use
        white for a single-channel image or RGB colors cyclically.
        """
        level = len(info.pyramid_levels) - 1 if info.pyramid_levels else 0
        width, height = self._level_size(info, level)
        scale = min(1.0, 256 / max(width, height))
        channels = list(range(min(3, info.size_c)))
        with self._open_image(storage) as handle:
            pixels = handle.read_region(
                level=level,
                z=info.size_z // 2,
                t=info.size_t // 2,
                channels=channels,
                output_size=(max(1, round(width * scale)), max(1, round(height * scale))),
            )
        if np.iscomplexobj(pixels):
            raise InvalidImageError("Complex OME pixels cannot be rendered.")
        settings = []
        for index in range(info.size_c):
            minimum, maximum = channel_intensity_range(pixels.dtype, info, index)
            if index < len(channels):
                sample = pixels[index][np.isfinite(pixels[index])]
                if sample.size:
                    low, high = np.percentile(sample, (1, 99))
                    if low < high:
                        minimum, maximum = float(low), float(high)
            metadata = next((channel for channel in info.channels if channel["index"] == index), {})
            color = metadata.get("color", "#FFFFFF" if info.size_c == 1 else _DEFAULT_COLORS[index % 3])
            if not isinstance(color, str):
                raise InvalidImageError("Invalid OME channel color.")
            settings.append(
                OmeChannelSetting(
                    channel=index,
                    color=color,
                    enabled=index < len(channels),
                    window_min=minimum,
                    window_max=maximum,
                )
            )
        return OmeChannelView(settings=settings, is_default=True)

    def set_channel_view(self, project_id: UUID, media_id: UUID, settings: OmeChannelSettings) -> OmeChannelView:
        """Replace only the mutable display view; structural metadata is never rewritten."""
        info = self.media_service.get_ome_image_info(project_id, media_id)
        self._validate_settings(settings, info)
        self._repository(project_id).save(str(media_id), [item.model_dump(mode="json") for item in settings.settings])
        return OmeChannelView(settings=settings.settings, is_default=False)

    @staticmethod
    def _level_size(info: OmeImageInfo, level: int) -> tuple[int, int]:
        if not 0 <= level < max(1, len(info.pyramid_levels)):
            raise InvalidRenderSelectionError("OME pyramid level is out of range.")
        if not info.pyramid_levels:
            return info.size_x, info.size_y
        dimensions = info.pyramid_levels[level]
        width, height = dimensions["width"], dimensions["height"]
        if not isinstance(width, int) or not isinstance(height, int) or min(width, height) <= 0:
            raise InvalidImageError("Invalid OME pyramid dimensions.")
        return width, height

    @staticmethod
    def _validate_render_budget(output_size: tuple[int, int], channel_count: int) -> None:
        """Conservatively budget decoding, source arrays, float64 RGB and temporary buffers.

        Reserve 128 MiB for encoded/decoded segments (each capped at 64 MiB by
        the TIFF reader), 128 bytes per output pixel for compositing/encoding,
        and two source arrays of up to 16 bytes per pixel per selected channel.
        This is a per-render estimate, not a process-wide memory limit.
        """
        width, height = output_size
        if min(width, height) <= 0:
            raise InvalidRenderSelectionError("OME output dimensions must be positive.")
        estimated_bytes = _RENDER_DECODE_RESERVE_BYTES + width * height * (
            _RENDER_BASE_BYTES_PER_PIXEL + channel_count * _RENDER_SOURCE_BYTES_PER_PIXEL
        )
        if estimated_bytes > _RENDER_MEMORY_BUDGET_BYTES:
            raise InvalidRenderSelectionError(
                f"OME render exceeds the {_RENDER_MEMORY_BUDGET_BYTES // (1024 * 1024)} MiB "
                f"estimated working-memory budget ({width}x{height}, {channel_count} enabled channels). "
                "Use a smaller max_size or a lower-resolution pyramid level."
            )

    def resolve_render(
        self,
        project_id: UUID,
        media_id: UUID,
        *,
        z: int = 0,
        t: int = 0,
        level: int = 0,
        override: OmeChannelSettings | None = None,
        max_size: int | None = None,
    ) -> OmeRender:
        """Resolve effective settings and a source-versioned, canonical ETag."""
        info, storage, version = self._context(project_id, media_id)
        width, height = self._level_size(info, level)
        if not 0 <= z < info.size_z or not 0 <= t < info.size_t:
            raise InvalidRenderSelectionError("OME z or t selection is out of range.")
        if max_size is not None and max_size <= 0:
            raise InvalidRenderSelectionError("OME max_size must be positive.")
        output_size = None
        if max_size is not None and max(width, height) > max_size:
            scale = max_size / max(width, height)
            output_size = max(1, round(width * scale)), max(1, round(height * scale))
        dimensions = output_size or (width, height)
        self._validate_render_budget(dimensions, 0)
        view = override if override is not None else self._get_channel_view(project_id, media_id, info, storage)
        self._validate_settings(view, info)
        settings = OmeChannelSettings(
            settings=sorted(
                (setting for setting in view.settings if setting.enabled), key=lambda setting: setting.channel
            )
        )
        self._validate_render_budget(dimensions, len(settings.settings))
        key = hashlib.sha256(
            json.dumps(
                {
                    "version": _RENDER_VERSION,
                    "source": version,
                    "media_id": str(media_id),
                    "z": z,
                    "t": t,
                    "level": level,
                    "settings": settings.model_dump(mode="json"),
                    "output_size": output_size,
                },
                sort_keys=True,
            ).encode()
        ).hexdigest()
        return OmeRender(f'"{key}"', storage, info, settings, z, t, level, output_size)

    def render(self, selection: OmeRender) -> bytes:
        """Read and composite a plane, encoding PNG bytes without filesystem writes."""
        self._validate_render_budget(
            selection.output_size or self._level_size(selection.info, selection.level),
            len(selection.settings.settings),
        )
        with self._open_image(selection.storage) as handle:
            pixels = handle.read_region(
                z=selection.z,
                t=selection.t,
                level=selection.level,
                channels=[setting.channel for setting in selection.settings.settings],
                output_size=selection.output_size,
            )
        with (
            Image.fromarray(composite_channels(pixels, selection.settings.settings)) as image,
            BytesIO() as buffer,
        ):
            image.save(buffer, format="PNG")
            return buffer.getvalue()
