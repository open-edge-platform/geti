# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import math

import numpy as np

from app.models import OmeImageInfo
from app.models.ome import ChannelProjection, RgbProjection
from app.services.base import InvalidImageError

_RGB_TARGETS: tuple[str, str, str] = ("red", "green", "blue")


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
    elif np.issubdtype(plane.dtype, np.integer):
        limits = np.iinfo(plane.dtype)
        minimum, maximum = limits.min, limits.max
    else:
        minimum, maximum = 0, 1
    scaled = (plane.astype(np.float64) - minimum) * (255.0 / (maximum - minimum))
    return np.nan_to_num(scaled).clip(0, 255).astype(np.uint8)
