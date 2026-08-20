# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Configuration model for the OC-SORT tracker."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field, model_validator

from getitrack.config import AlgorithmType, TrackerConfig


class OCSortConfig(TrackerConfig):
    """OC-SORT-specific configuration."""

    algorithm: Literal[AlgorithmType.OCSORT] = AlgorithmType.OCSORT  # pyrefly: ignore[bad-override]
    """Algorithm identifier; fixed to ``ocsort``."""

    det_threshold: Annotated[float, Field(ge=0.0, le=1.0)] = 0.6
    """High-score gate. Detections above this drive the first association pass and
    can spawn new tracks; those between ``score_threshold`` and this feed the
    optional BYTE stage."""

    iou_threshold: Annotated[float, Field(ge=0.0, le=1.0)] = 0.3
    """Minimum IoU for a valid association. A pair overlapping less than this is
    left unmatched regardless of the momentum term."""

    delta_t: Annotated[int, Field(ge=1)] = 3
    """Frame gap used to estimate a track's motion direction for the
    observation-centric momentum (OCM) term."""

    inertia: Annotated[float, Field(ge=0.0, le=1.0)] = 0.2
    """Weight of the OCM velocity-direction term added to the association cost."""

    use_byte: bool = False
    """Associate low-score detections to still-unmatched tracks before the
    recovery pass."""

    match_class_only: bool = True
    """Restrict matching to detection-track pairs that share a class id."""

    @property
    def match_threshold(self) -> float:
        """Maximum assignment cost (``1 - IoU``) accepted for a match."""
        return 1.0 - self.iou_threshold

    @model_validator(mode="after")
    def _check_thresholds(self) -> OCSortConfig:
        """Reject a low-score floor at or above the high-score gate."""
        if self.score_threshold >= self.det_threshold:
            msg = "score_threshold must be below det_threshold"
            raise ValueError(msg)
        return self
