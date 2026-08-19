# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Cubic-spline interpolation strategy."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

import numpy as np
from scipy.interpolate import CubicSpline

from getitrack.config import InterpolationMethod
from getitrack.interpolation.base import BaseInterpolator
from getitrack.interpolation.linear import LinearInterpolator
from getitrack.utils import cxcywh_to_xyxy, xyxy_to_cxcywh

if TYPE_CHECKING:
    from getitrack.interpolation.base import Observation

# Spline sizes are floored to this so an overshoot never yields a degenerate box.
_MIN_BOX_SIZE = 1e-3


class SplineInterpolator(BaseInterpolator):
    """Fit a cubic spline through the track's observed centers and sizes.

    Uses neighbouring observations for a smoother path than the two endpoints
    alone; with exactly two observations it degrades to a straight segment.
    """

    method: ClassVar[InterpolationMethod] = InterpolationMethod.SPLINE

    def fill(
        self,
        observations: list[Observation],
        start: Observation,
        end: Observation,
        frame_ids: list[int],
    ) -> np.ndarray:
        """Evaluate the fitted center/size spline at the gap frames and return ``xyxy`` boxes."""
        spline = self._build_spline(observations)
        if spline is None:  # pragma: no cover - a bracketed gap always has >= 2 observations
            return LinearInterpolator(self._config).fill(observations, start, end, frame_ids)
        values = np.asarray(spline(np.asarray(frame_ids, dtype=np.float64)))
        values[:, 2:] = np.maximum(values[:, 2:], _MIN_BOX_SIZE)
        return cxcywh_to_xyxy(values).astype(np.float32)

    @staticmethod
    def _build_spline(observations: list[Observation]) -> CubicSpline | None:
        """Fit a cubic spline over the track's ``cxcywh`` observations, or ``None`` if fewer than two."""
        if len(observations) < 2:
            return None
        frame_ids = np.array([observation.frame_id for observation in observations], dtype=np.float64)
        boxes = np.stack([observation.bbox for observation in observations], axis=0)
        return CubicSpline(frame_ids, xyxy_to_cxcywh(boxes), axis=0)
