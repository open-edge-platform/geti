# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from app.models import OmeImageInfo
from app.models.ome import GrayscaleProjection
from app.services.base import InvalidImageError


class SingleChannelGrayscaleProjectionStrategy:
    """Select a configured source channel without expanding it to RGB."""

    def __init__(self, channel: int = 0) -> None:
        self._projection = GrayscaleProjection(channel=channel)

    def compute(self, info: OmeImageInfo) -> GrayscaleProjection:
        """Return a single-channel projection if the selected source channel exists."""
        if self._projection.channel >= info.size_c:
            raise InvalidImageError(f"Grayscale source channel {self._projection.channel} is outside SizeC.")
        return self._projection
