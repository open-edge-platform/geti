# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import math
from collections.abc import Iterator

import numpy as np

from app.models import OmeImageInfo, Region
from app.models.ome import ChannelProjection, RgbProjection
from app.services.base import InvalidImageError
from app.services.ome.protocols import OmeImageHandle

_RGB_TARGETS: tuple[str, str, str] = ("red", "green", "blue")
# Warm-cache macOS arm64 benchmarks (six settings, eight uint16 workloads, three runs each):
# 1M pixels / 256 rows reduced geometric-mean runtime by 16% versus 256K pixels / 64 rows.
# A 2M-pixel / 512-row budget saved 17%, but peak RSS growth above the import baseline rose
# from 68 to 139 MiB (112 to 207 MiB in float64 validation). Keep the smaller memory tradeoff.
PROJECTION_STRIP_PIXELS: int = 1024 * 1024
PROJECTION_MAX_STRIP_HEIGHT: int = 256


def iter_projected_regions(
    handle: OmeImageHandle, info: OmeImageInfo, projection: ChannelProjection, *, z: int, t: int
) -> Iterator[tuple[Region, np.ndarray]]:
    """Yield bounded level-zero HWC uint8 regions with the immutable training projection."""
    strip_height = max(1, min(PROJECTION_MAX_STRIP_HEIGHT, PROJECTION_STRIP_PIXELS // info.size_x))
    for y in range(0, info.size_y, strip_height):
        height = min(strip_height, info.size_y - y)
        chunk_width = max(1, PROJECTION_STRIP_PIXELS // height)
        for x in range(0, info.size_x, chunk_width):
            region = Region(x=x, y=y, width=min(chunk_width, info.size_x - x), height=height)
            pixels = handle.read_region(level=0, region=region, z=z, t=t, channels=projection.source_channels)
            if pixels.shape != (len(projection.source_channels), region.height, region.width):
                raise InvalidImageError("OME reader returned unexpected projected region dimensions.")
            yield region, render_channel_projection(pixels, info, projection)


def projected_plane_bytes(info: OmeImageInfo, projection: ChannelProjection) -> int:
    """Return full-plane uint8 output size, excluding bounded decode/projection temporaries."""
    return info.size_x * info.size_y * (3 if isinstance(projection, RgbProjection) else 1)


def render_channel_projection(pixels: np.ndarray, info: OmeImageInfo, projection: ChannelProjection) -> np.ndarray:
    """Window selected CHW pixels into an HWC uint8 image with three or one channels.

    Args:
        pixels: Pixels in the order of ``projection.source_channels``.
        info: Immutable metadata supplying source-channel intensity ranges.
        projection: The stored RGB or grayscale projection to execute.

    Returns:
        An array shaped (H, W, 3) for RGB or (H, W, 1) for grayscale.

    Raises:
        InvalidImageError: If channels, pixel shape, dtype or intensity windows are invalid.
    """
    if any(channel >= info.size_c for channel in projection.source_channels):
        raise InvalidImageError("Channel projection references a channel outside SizeC.")
    if pixels.ndim != 3 or pixels.shape[0] != len(projection.source_channels):
        raise InvalidImageError("Pixel channels do not match the channel projection.")
    if np.iscomplexobj(pixels):
        raise InvalidImageError("Complex OME pixels cannot be projected to an image.")
    output = np.zeros((*pixels.shape[1:], 3 if isinstance(projection, RgbProjection) else 1), dtype=np.uint8)
    for index, channel_index in enumerate(projection.source_channels):
        target_index = (
            _RGB_TARGETS.index(projection.channels[index].target) if isinstance(projection, RgbProjection) else 0
        )
        output[..., target_index] = _window_channel(pixels[index], info, channel_index)
    return output


def _window_channel(plane: np.ndarray, info: OmeImageInfo, channel_index: int) -> np.ndarray:
    minimum, maximum = channel_intensity_range(plane.dtype, info, channel_index)
    return window_channel(plane, minimum, maximum)


def channel_intensity_range(dtype: np.dtype, info: OmeImageInfo, channel_index: int) -> tuple[float, float]:
    """Resolve a channel's declared range, falling back to its pixel dtype."""
    channel = next((channel for channel in info.channels if channel["index"] == channel_index), None)
    window = channel.get("window") if channel else None
    if isinstance(window, dict):
        minimum, maximum = window["min"], window["max"]
        if (
            not isinstance(minimum, int | float)
            or not isinstance(maximum, int | float)
            or not math.isfinite(minimum)
            or not math.isfinite(maximum)
            or minimum >= maximum
        ):
            raise InvalidImageError("Invalid OME channel intensity window.")
    elif np.issubdtype(dtype, np.integer):
        limits = np.iinfo(dtype)
        minimum, maximum = limits.min, limits.max
    else:
        minimum, maximum = 0, 1
    return float(minimum), float(maximum)


def window_channel(plane: np.ndarray, minimum: float, maximum: float) -> np.ndarray:
    """Map a valid intensity window to uint8, clipping endpoints and non-finite pixels."""
    values = plane.astype(np.float64).clip(minimum, maximum)
    if math.isfinite(maximum - minimum):
        scaled = (values - minimum) / (maximum - minimum)
    else:
        scaled = (values / 2 - minimum / 2) / (maximum / 2 - minimum / 2)
    scaled *= 255
    return np.nan_to_num(scaled).clip(0, 255).astype(np.uint8)
