# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Configuration model for the StrongSORT tracker."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field

from getitrack.algorithms.configs.sort import SortConfig
from getitrack.config import AlgorithmType, ReIDConfig


class StrongSortConfig(SortConfig):
    """StrongSORT configuration.

    Extends SORT with three components: an appearance (ReID) stage layered on the
    IoU association, ECC-based global motion compensation (GMC), and the optional
    NSA-Kalman confidence-scaled measurement noise. Each is individually
    toggleable. With no detection embeddings, no supplied GMC warp, and
    ``nsa_kalman`` off, the tracker reproduces plain SORT. ``gmc_enabled``
    defaults on but is inert until a per-frame warp is supplied via
    ``StrongSortTracker.set_frame_warp``.
    """

    algorithm: Literal[AlgorithmType.STRONGSORT] = AlgorithmType.STRONGSORT  # pyrefly: ignore[bad-override]
    """Algorithm identifier; fixed to ``strongsort``."""

    appearance_weight: Annotated[float, Field(ge=0.0, le=1.0)] = 0.75
    """Weight of the appearance term when fusing appearance and IoU costs.

    IoU contributes the remaining ``1 - appearance_weight``, and the IoU
    proximity gate still guards every fused pair. 0 disables appearance
    influence; 1 matches on appearance alone within the gate."""

    appearance_iou_floor: Annotated[float, Field(ge=0.0, le=1.0)] = 0.5
    """Minimum IoU a track/detection pair must reach for appearance fusion to
    apply. Pairs below it fall back to the plain IoU cost."""

    gallery_size: Annotated[int, Field(ge=1)] = 50
    """Maximum descriptors retained in each track's FIFO appearance gallery."""

    appearance_threshold: Annotated[float, Field(ge=0.0, le=2.0)] = 0.25
    """Maximum cosine distance for a descriptor to be admitted into a track's
    gallery."""

    use_ema: bool = True
    """Query appearance against a running EMA descriptor in addition to the raw
    FIFO gallery entries."""

    ema_alpha: Annotated[float, Field(gt=0.0, lt=1.0)] = 0.9
    """EMA retention factor. Higher keeps more appearance history. The update is
    ``ema = (1 - w) * ema + w * feature`` with ``w = (1 - ema_alpha) * score``."""

    reid: ReIDConfig = Field(default_factory=ReIDConfig)
    """ReID model enablement and path used to embed detections."""

    gmc_enabled: bool = True
    """Enable ECC global motion compensation. When on, a per-frame affine warp
    supplied via ``StrongSortTracker.set_frame_warp`` is applied to every track's
    Kalman-predicted box before association. Inert until a warp is supplied."""

    nsa_kalman: bool = False
    """Enable the NSA-Kalman rule: scale the Kalman measurement noise by
    ``1 - score``."""
