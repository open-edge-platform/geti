# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Bounding-box interpolation: fills short per-track gaps in a clip.

Consumes a clip's per-frame `TrackedDetections` and synthesises missing boxes
for gaps up to ``max_gap``, so downstream consumers see continuous trajectories.
Synthesised rows carry ``interpolated=True`` and ``det_index=-1``; observed rows
are untouched, which makes the stage idempotent.

Strategies (`InterpolationConfig.method`, resolved by `BaseInterpolator.from_config`):

- `LinearInterpolator`: straight line between the two bracketing observations.
- `KalmanInterpolator`: constant velocity; ``velocity_decay`` shapes the path.
- `SplineInterpolator`: cubic spline through all of the track's observations.

Regimes (`InterpolationConfig.online`):

- Offline (default): bridge every gap up to ``max_gap`` using the observations
  on both sides.
- Online (causal): fill a gap frame only once its closing observation is within
  ``online_buffer`` frames of lookahead (``0`` is strictly causal, fills nothing).
"""

from __future__ import annotations

from getitrack.interpolation.base import BaseInterpolator
from getitrack.interpolation.kalman import KalmanInterpolator
from getitrack.interpolation.linear import LinearInterpolator
from getitrack.interpolation.spline import SplineInterpolator

__all__ = [
    "BaseInterpolator",
    "KalmanInterpolator",
    "LinearInterpolator",
    "SplineInterpolator",
]
