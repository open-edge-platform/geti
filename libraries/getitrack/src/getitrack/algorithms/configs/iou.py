# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Configuration for the High-Speed IOU Tracker."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field

from getitrack.config import AlgorithmType, DistanceMetric, TrackerConfig


class IOUConfig(TrackerConfig):
    """IOU thresholds and online confirmation settings.

    ``lifecycle.min_hits`` is the paper's minimum track length (t_min).
    Tracks end on the first miss regardless of the lifecycle age limits.
    Motion settings are unused: association uses the last observed box.
    """

    algorithm: Literal[AlgorithmType.IOU] = AlgorithmType.IOU  # pyrefly: ignore[bad-override]
    """Algorithm identifier; fixed to ``iou``."""

    distance_metric: Literal[DistanceMetric.IOU] = DistanceMetric.IOU  # pyrefly: ignore[bad-override]
    """The reference algorithm requires plain IoU."""

    score_threshold: Annotated[float, Field(ge=0.0, le=1.0)] = 0.1
    """Inclusive low detection threshold (sigma_l)."""

    high_score_threshold: Annotated[float, Field(ge=0.0, le=1.0)] = 0.5
    """At least one observation must reach this score to confirm a track (sigma_h)."""

    iou_threshold: Annotated[float, Field(ge=0.0, le=1.0)] = 0.5
    """Minimum overlap for a greedy match (sigma_iou), inclusive."""

    match_class_only: bool = True
    """Restrict matching to detections sharing the track's class id."""
