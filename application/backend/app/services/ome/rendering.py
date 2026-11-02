# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Rendering of OME planes to 8-bit RGB: per-channel intensity windowing and compositing."""

import hashlib
import json
from collections.abc import Mapping, Sequence

import numpy as np

from app.models.ome import ChannelDisplaySetting, ChannelMapping, OmeImageInfo, RgbTarget

DEFAULT_LOW_PERCENTILE = 0.5
DEFAULT_HIGH_PERCENTILE = 99.5


class InvalidChannelSettingsError(ValueError):
    """Raised when channel display settings are inconsistent with the image."""


def apply_window(data: np.ndarray, window_min: float, window_max: float) -> np.ndarray:
    """
    Map values linearly from [window_min, window_max] to [0, 255]; values outside the window are clipped.

    Args:
        data: Channel values.
        window_min: Value mapped to 0.
        window_max: Value mapped to 255.

    Returns:
        The windowed channel, as uint8.
    """
    scaled = (data.astype(np.float32) - window_min) * (255.0 / (window_max - window_min))
    return np.clip(np.rint(scaled), 0, 255).astype(np.uint8)


def compose_rgb(channel_data: Mapping[int, np.ndarray], mappings: Sequence[ChannelMapping]) -> np.ndarray:
    """
    Composite windowed channels into an RGB image. Disabled display settings contribute nothing.

    Args:
        channel_data: 2D arrays of the channels referenced by `mappings`, by channel index.
        mappings: Channel projections; when several channels target the same color, the brightest wins.

    Returns:
        An (H, W, 3) uint8 RGB image.
    """
    height, width = next(iter(channel_data.values())).shape[:2]
    rgb = np.zeros((height, width, 3), dtype=np.uint8)
    for mapping in mappings:
        if isinstance(mapping, ChannelDisplaySetting) and not mapping.enabled:
            continue
        windowed = apply_window(channel_data[mapping.channel], mapping.window_min, mapping.window_max)
        target = mapping.target.rgb_index
        np.maximum(rgb[..., target], windowed, out=rgb[..., target])
    return rgb


def default_display_settings(
    info: OmeImageInfo, channel_samples: Mapping[int, np.ndarray]
) -> list[ChannelDisplaySetting]:
    """
    Server-computed display settings: the training projection, auto-contrasted from a sample of each channel.

    Channels not used by the training projection are listed disabled, so that clients can enable them.

    Args:
        info: Structure of the image, including its training channel mapping.
        channel_samples: Sampled values of every channel, by channel index.

    Returns:
        The display settings.
    """
    settings = []
    mapped_channels = set()
    for mapping in info.channel_mapping:
        mapped_channels.add(mapping.channel)
        sample = channel_samples[mapping.channel]
        low, high = np.percentile(sample, [DEFAULT_LOW_PERCENTILE, DEFAULT_HIGH_PERCENTILE])
        window_min, window_max = (float(low), float(high)) if high > low else (mapping.window_min, mapping.window_max)
        settings.append(
            ChannelDisplaySetting(
                channel=mapping.channel,
                target=mapping.target,
                window_min=window_min,
                window_max=window_max,
                enabled=True,
            )
        )
    fallback_window = info.channel_mapping[0] if info.channel_mapping else None
    for channel in info.channels:
        if channel.index in mapped_channels:
            continue
        settings.append(
            ChannelDisplaySetting(
                channel=channel.index,
                target=list(RgbTarget)[channel.index % 3],
                window_min=fallback_window.window_min if fallback_window else 0.0,
                window_max=fallback_window.window_max if fallback_window else 255.0,
                enabled=False,
            )
        )
    return settings


def validate_display_settings(info: OmeImageInfo, settings: Sequence[ChannelDisplaySetting]) -> None:
    """
    Check display settings against the image.

    Raises:
        InvalidChannelSettingsError: If a channel index is out of range, or two enabled channels share a target.
    """
    for setting in settings:
        if setting.channel >= info.size_c:
            raise InvalidChannelSettingsError(
                f"Channel {setting.channel} does not exist, the image has {info.size_c} channel(s)."
            )
    enabled_targets = [setting.target for setting in settings if setting.enabled]
    if len(enabled_targets) != len(set(enabled_targets)):
        raise InvalidChannelSettingsError("Several enabled channels are mapped to the same RGB target.")


def settings_hash(settings: Sequence[ChannelMapping]) -> str:
    """Stable short hash of channel settings, used as render cache key and ETag."""
    payload = json.dumps([setting.model_dump(mode="json") for setting in settings], sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()[:16]
