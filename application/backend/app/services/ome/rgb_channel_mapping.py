# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import colorsys
import math
from typing import Literal

from app.models import OmeImageInfo
from app.models.ome import RgbChannelAssignment, RgbProjection
from app.services.base import InvalidImageError

_TARGETS: tuple[Literal["red", "green", "blue"], ...] = ("red", "green", "blue")
_TARGET_COLORS: tuple[tuple[int, int, int], ...] = ((255, 0, 0), (0, 255, 0), (0, 0, 255))


class MetadataRgbChannelMappingStrategy:
    """Map channels to RGB using wavelength metadata, falling back to the first three channels."""

    def compute(self, info: OmeImageInfo) -> RgbProjection:
        """Compute the fixed RGB projection without reading pixels or mutable display settings."""
        candidates: dict[str, list[tuple[float, int]]] = {target: [] for target in _TARGETS}
        units = {"nm": 1.0, "\u00b5m": 1000.0, "um": 1000.0, "mm": 1e6, "m": 1e9, "pm": 1e-3}
        for channel in info.channels:
            wavelength = channel.get("emission_wavelength")
            index = channel.get("index")
            factor = units.get(str(channel.get("emission_wavelength_unit", "nm")))
            if not isinstance(wavelength, int | float) or not isinstance(index, int) or factor is None:
                break
            wavelength *= factor
            if not math.isfinite(wavelength) or wavelength <= 0:
                break
            target = "blue" if wavelength < 500 else "green" if wavelength <= 580 else "red"
            color = channel.get("color")
            distance = math.inf
            if isinstance(color, str) and len(color) == 7 and color.startswith("#"):
                try:
                    rgb = tuple(int(color[i : i + 2], 16) for i in (1, 3, 5))
                except ValueError as error:
                    raise InvalidImageError("Invalid OME channel color.") from error
                hue, saturation, _ = colorsys.rgb_to_hsv(*(value / 255 for value in rgb))
                target_hue = colorsys.rgb_to_hsv(*_TARGET_COLORS[_TARGETS.index(target)])[0]
                delta = abs(hue - target_hue)
                distance = min(delta, 1 - delta) if saturation else math.inf
            candidates[target].append((distance, index))
        else:
            if len(info.channels) == info.size_c:
                return RgbProjection(
                    channels=tuple(
                        RgbChannelAssignment(channel=min(candidates[target])[1], target=target)
                        for target in _TARGETS
                        if candidates[target]
                    )
                )
        return RgbProjection(
            channels=tuple(
                RgbChannelAssignment(channel=index, target=_TARGETS[index]) for index in range(min(info.size_c, 3))
            )
        )
