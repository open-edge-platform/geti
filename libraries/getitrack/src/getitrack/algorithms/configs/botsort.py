# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Configuration model for the BoT-SORT tracker."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field

from getitrack.algorithms.configs.bytetrack import ByteTrackConfig
from getitrack.config import AlgorithmType, GMCConfig, ReIDConfig


class BotSortConfig(ByteTrackConfig):
    """BoT-SORT configuration.

    Extends the ByteTrack parameter set with an appearance (ReID) stage: a
    bounded per-track gallery, cosine appearance costs fused with IoU under an
    IoU proximity gate, and an optional confidence-scaled EMA feature.
    """

    algorithm: Literal[AlgorithmType.BOTSORT] = AlgorithmType.BOTSORT  # pyrefly: ignore[bad-override]
    """Algorithm identifier; fixed to ``botsort``."""

    appearance_weight: Annotated[float, Field(ge=0.0, le=1.0)] = 0.25
    """Weight of the appearance term when fusing appearance and IoU costs.
    0 disables appearance influence; 1 matches on appearance alone (still
    subject to the IoU proximity gate)."""

    appearance_iou_floor: Annotated[float, Field(ge=0.0, le=1.0)] = 0.5
    """Minimum IoU a track/detection pair must reach for appearance fusion to
    apply. Pairs below it use the IoU cost alone."""

    gallery_size: Annotated[int, Field(ge=1)] = 50
    """Maximum descriptors retained in each track's FIFO appearance gallery."""

    appearance_threshold: Annotated[float, Field(ge=0.0, le=2.0)] = 0.25
    """Maximum cosine distance for a descriptor to be admitted into a track's
    gallery. Larger values admit more descriptors."""

    use_ema: bool = True
    """Also query appearance against a running EMA descriptor, in addition to the
    FIFO gallery entries."""

    ema_alpha: Annotated[float, Field(gt=0.0, lt=1.0)] = 0.9
    """EMA retention factor. Higher keeps more appearance history. The update is
    ``ema = (1 - w) * ema + w * feature`` with ``w = (1 - ema_alpha) * score``."""

    reid: ReIDConfig = Field(default_factory=ReIDConfig)
    """ReID model enablement and path used to embed detections."""

    gmc: GMCConfig = Field(default_factory=GMCConfig)
    """Global motion compensation (camera-motion) parameters."""
