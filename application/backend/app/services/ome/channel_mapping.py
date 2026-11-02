# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Fixed, deterministic channel->RGB projection used to materialize OME planes as training images."""

from collections.abc import Callable

import numpy as np

from app.models.ome import ChannelMapping, OmeChannel, OmeImageInfo, RgbTarget

# Emission wavelength boundaries (nm) between the blue, green and red targets
BLUE_GREEN_BOUNDARY_NM = 500.0
GREEN_RED_BOUNDARY_NM = 580.0

# Reference hue of each target, used to break ties between channels of the same wavelength band
_TARGET_RGB = {
    RgbTarget.RED: np.array([255, 0, 0]),
    RgbTarget.GREEN: np.array([0, 255, 0]),
    RgbTarget.BLUE: np.array([0, 0, 255]),
}
# Reference wavelength of each target, used to break ties when channels declare no color
_TARGET_WAVELENGTH_NM = {RgbTarget.RED: 620.0, RgbTarget.GREEN: 540.0, RgbTarget.BLUE: 460.0}


def declared_value_range(pixel_type: str, significant_bits: int | None) -> tuple[float, float] | None:
    """
    Range of values a pixel can take according to the OME metadata.

    Args:
        pixel_type: OME pixel type, e.g. 'uint16'.
        significant_bits: Number of meaningful bits, if declared (e.g. 12 for 12-bit data stored as uint16).

    Returns:
        The (min, max) range, or None for floating point types whose range is not declared.
    """
    if pixel_type == "bit":
        return 0.0, 1.0
    try:
        dtype = np.dtype(pixel_type)
    except TypeError:
        return None
    if not np.issubdtype(dtype, np.integer):
        return None
    info = np.iinfo(dtype.name)
    if significant_bits is not None and 0 < significant_bits < info.bits:
        if np.issubdtype(dtype, np.signedinteger):
            return float(-(2 ** (significant_bits - 1))), float(2 ** (significant_bits - 1) - 1)
        return 0.0, float(2**significant_bits - 1)
    return float(info.min), float(info.max)


def _target_for_wavelength(wavelength: float) -> RgbTarget:
    if wavelength < BLUE_GREEN_BOUNDARY_NM:
        return RgbTarget.BLUE
    if wavelength <= GREEN_RED_BOUNDARY_NM:
        return RgbTarget.GREEN
    return RgbTarget.RED


def _color_distance(channel: OmeChannel, target: RgbTarget) -> float:
    if channel.color is None:
        return float("inf")
    rgb = np.array([int(channel.color[i : i + 2], 16) for i in (1, 3, 5)])
    return float(np.linalg.norm(rgb - _TARGET_RGB[target]))


def _map_by_wavelength(channels: list[OmeChannel]) -> list[tuple[int, RgbTarget]]:
    """Map each wavelength band to its best channel, preferring the declared color closest to the target hue."""
    candidates: dict[RgbTarget, list[OmeChannel]] = {}
    for channel in channels:
        candidates.setdefault(_target_for_wavelength(channel.emission_wavelength or 0.0), []).append(channel)
    mapping = []
    for target in RgbTarget:
        if target not in candidates:
            continue
        best = min(
            candidates[target],
            key=lambda c: (
                _color_distance(c, target),
                abs((c.emission_wavelength or 0.0) - _TARGET_WAVELENGTH_NM[target]),
                c.index,
            ),
        )
        mapping.append((best.index, target))
    return mapping


def compute_training_channel_mapping(
    info: OmeImageInfo, sample_value_range: Callable[[], tuple[float, float]]
) -> list[ChannelMapping]:
    """
    Compute the fixed channel->RGB projection of an OME image, used to render its planes for training.

    Strategy, in priority order:
    1. Every channel declares an emission wavelength: each RGB band gets the channel emitting in it
       (<500nm blue, 500-580nm green, >580nm red); collisions are resolved by declared color, then wavelength.
    2. Exactly 3 channels: identity mapping (channel i -> target i).
    3. A single channel: grayscale, replicated on all three targets.
    4. Otherwise: the first channels are mapped to red, green, blue in index order; extra channels are dropped.

    The intensity window is the declared value range of the pixel type, so that the projection only depends on
    immutable metadata. Floating point images declare no range: `sample_value_range` is used instead.

    Args:
        info: Parsed structure of the image.
        sample_value_range: Returns the (min, max) value range sampled from the image, for float pixel types.

    Returns:
        The channel mapping.
    """
    channels = info.channels
    if channels and all(channel.emission_wavelength is not None for channel in channels):
        pairs = _map_by_wavelength(channels)
    elif info.size_c == 3:
        pairs = list(zip(range(3), RgbTarget))
    elif info.size_c == 1:
        pairs = [(0, target) for target in RgbTarget]
    else:
        pairs = list(zip(range(min(info.size_c, 3)), RgbTarget))

    value_range = declared_value_range(info.pixel_type, info.significant_bits)
    if value_range is None:
        value_range = sample_value_range()
    window_min, window_max = value_range
    if window_min >= window_max:
        window_max = window_min + 1.0
    return [
        ChannelMapping(channel=channel, target=target, window_min=window_min, window_max=window_max)
        for channel, target in pairs
    ]
