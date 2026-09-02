# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""ECC (Enhanced Correlation Coefficient) camera-motion estimator.

Estimates a Euclidean (rotation + translation) warp by maximising the image
correlation. Falls back to identity when the optimisation fails to converge.
"""

from __future__ import annotations

from typing import ClassVar

import cv2
import numpy as np

from getitrack.config import GMCMethod
from getitrack.motion.gmc.base import BaseMotionEstimator

_IDENTITY = np.eye(2, 3, dtype=np.float32)
_MAX_ITERATIONS = 100
_TERMINATION_EPS = 1e-6


class ECCEstimator(BaseMotionEstimator):
    """Fit a Euclidean warp by maximising the enhanced correlation coefficient."""

    method: ClassVar[GMCMethod] = GMCMethod.ECC

    def _estimate(self, prev_gray: np.ndarray, curr_gray: np.ndarray) -> np.ndarray:
        warp = np.eye(2, 3, dtype=np.float32)
        criteria = (
            cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT,
            _MAX_ITERATIONS,
            _TERMINATION_EPS,
        )
        try:
            _, warp = cv2.findTransformECC(prev_gray, curr_gray, warp, cv2.MOTION_EUCLIDEAN, criteria, None)
        except cv2.error:
            return _IDENTITY.copy()
        return warp.astype(np.float32)
