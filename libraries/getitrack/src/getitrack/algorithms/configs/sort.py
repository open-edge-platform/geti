# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Configuration model for the SORT tracker."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field

from getitrack.config import AlgorithmType, TrackerConfig


class SortConfig(TrackerConfig):
    """SORT-specific configuration."""

    algorithm: Literal[AlgorithmType.SORT] = AlgorithmType.SORT  # pyrefly: ignore[bad-override]
    """Algorithm identifier; fixed to ``sort``."""

    iou_threshold: Annotated[float, Field(ge=0.0, le=1.0)] = 0.3
    """Minimum IoU for a valid detection-track association."""

    match_class_only: bool = True
    """Restrict matching to detection-track pairs that share a class id."""

    @property
    def match_threshold(self) -> float:
        """Maximum assignment cost (``1 - IoU``) accepted for a match."""
        return 1.0 - self.iou_threshold
