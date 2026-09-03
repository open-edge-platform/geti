# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Configuration model for the Deep OC-SORT tracker."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field

from getitrack.algorithms.configs.ocsort import OCSortConfig
from getitrack.config import AlgorithmType, ReIDConfig


class DeepOcSortConfig(OCSortConfig):
    """Deep OC-SORT configuration.

    Extends the OC-SORT parameter set with an appearance (ReID) stage: a bounded
    per-track gallery, a cosine appearance cost fused with IoU under an IoU
    proximity gate in the first (OCM) association, and an optional
    confidence-scaled EMA feature.
    """

    algorithm: Literal[AlgorithmType.DEEPOCSORT] = AlgorithmType.DEEPOCSORT  # pyrefly: ignore[bad-override]
    """Algorithm identifier; fixed to ``deepocsort``."""

    appearance_weight: Annotated[float, Field(ge=0.0, le=1.0)] = 0.25
    """Weight of the appearance term when fusing appearance and IoU costs.
    0 disables appearance influence; 1 matches on appearance alone (still
    subject to the IoU proximity gate)."""

    appearance_iou_floor: Annotated[float, Field(ge=0.0, le=1.0)] = 0.5
    """Minimum IoU a track/detection pair must reach for appearance fusion to
    apply. Pairs below it fall back to the plain IoU (plus OCM) cost."""

    gallery_size: Annotated[int, Field(ge=1)] = 50
    """Maximum descriptors retained in each track's FIFO appearance gallery."""

    appearance_threshold: Annotated[float, Field(ge=0.0, le=2.0)] = 0.25
    """Maximum cosine distance for a descriptor to be admitted into a track's
    gallery. Descriptors above it are rejected."""

    use_ema: bool = True
    """Query appearance against a running EMA descriptor rather than the raw
    FIFO gallery entries."""

    ema_alpha: Annotated[float, Field(gt=0.0, lt=1.0)] = 0.9
    """EMA retention factor. Higher keeps more appearance history. The update is
    confidence-scaled by the detection score."""

    reid: ReIDConfig = Field(default_factory=ReIDConfig)
    """ReID model enablement and path used to embed detections."""
