# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Linear interpolation strategy."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

import numpy as np

from getitrack.config import InterpolationMethod
from getitrack.interpolation.base import BaseInterpolator

if TYPE_CHECKING:
    from getitrack.interpolation.base import _Observation


class LinearInterpolator(BaseInterpolator):
    """Linearly interpolate the ``xyxy`` corners of the two bracketing observations."""

    method: ClassVar[InterpolationMethod] = InterpolationMethod.LINEAR

    def fill(
        self,
        observations: list[_Observation],
        start: _Observation,
        end: _Observation,
        frame_ids: list[int],
    ) -> np.ndarray:
        """Interpolate ``xyxy`` corners linearly between ``start`` and ``end``."""
        span = float(end.frame_id - start.frame_id)
        weights = (np.asarray(frame_ids, dtype=np.float64) - start.frame_id) / span
        boxes = (1.0 - weights)[:, None] * start.bbox[None, :] + weights[:, None] * end.bbox[None, :]
        return boxes.astype(np.float32)
