# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Kalman constant-velocity interpolation strategy."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

import numpy as np

from getitrack.config import InterpolationMethod
from getitrack.interpolation.base import BaseInterpolator
from getitrack.motion import KalmanFilter
from getitrack.utils import cxcywh_to_xyxy, xyah_to_xyxy, xyxy_to_cxcywh, xyxy_to_xyah

if TYPE_CHECKING:
    from getitrack.config import InterpolationConfig, MotionConfig
    from getitrack.interpolation.base import _Observation

# Degenerate anchor sizes are floored to this before the xyah conversion, which
# otherwise rejects zero-area boxes.
_MIN_BOX_SIZE = 1e-3


class KalmanInterpolator(BaseInterpolator):
    """Propagate a constant-velocity Kalman state across the gap in ``xyah`` space.

    Seeds the filter at the opening observation with the endpoint-derived
    velocity. ``velocity_decay`` of 1.0 traces the straight line to the closing
    box; below 1.0 the fill decelerates and undershoots it, leaving a step at
    the gap boundary.
    """

    method: ClassVar[InterpolationMethod] = InterpolationMethod.KALMAN

    def __init__(self, config: InterpolationConfig | None = None, *, motion: MotionConfig | None = None) -> None:
        """Build the underlying filter from ``motion`` (``None`` is undamped constant velocity)."""
        super().__init__(config, motion=motion)
        self._kalman = KalmanFilter() if self._motion is None else KalmanFilter.from_config(self._motion)

    def fill(
        self,
        observations: list[_Observation],
        start: _Observation,
        end: _Observation,
        frame_ids: list[int],
    ) -> np.ndarray:
        """Fill the gap by advancing a seeded constant-velocity state one frame at a time."""
        # Floor degenerate anchors (xyxy_to_xyah rejects zero-area boxes), then convert.
        anchors = xyxy_to_cxcywh(np.stack([start.bbox, end.bbox], axis=0))
        anchors[:, 2:] = np.maximum(anchors[:, 2:], _MIN_BOX_SIZE)
        start_xyah, end_xyah = xyxy_to_xyah(cxcywh_to_xyxy(anchors))

        steps = end.frame_id - start.frame_id
        velocity = (end_xyah - start_xyah) / steps
        mean, covariance = self._kalman.initiate(start_xyah)
        mean = mean.copy()
        mean[4:] = velocity

        boxes_by_frame: dict[int, np.ndarray] = {}
        for step in range(1, steps):
            mean, covariance = self._kalman.predict(mean, covariance)
            boxes_by_frame[start.frame_id + step] = xyah_to_xyxy(mean[None, :4])[0]
        return np.stack([boxes_by_frame[frame_id] for frame_id in frame_ids], axis=0).astype(np.float32)
