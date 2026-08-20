# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Sparse optical-flow camera-motion estimator (BoT-SORT's default GMC)."""

from __future__ import annotations

from typing import ClassVar

import cv2
import numpy as np

from getitrack.config import GMCMethod
from getitrack.motion.gmc.base import BaseMotionEstimator

_IDENTITY = np.eye(2, 3, dtype=np.float32)
_MIN_MATCHES = 4  # estimateAffinePartial2D needs at least this many correspondences.


class SparseOptFlowEstimator(BaseMotionEstimator):
    """Track Shi-Tomasi corners with Lucas-Kanade flow, then fit a partial affine.

    Corners detected in the previous frame are followed into the current one with
    pyramidal optical flow; the surviving matches feed a RANSAC partial-affine
    fit. Falls back to identity when too few corners survive to fit reliably.
    """

    method: ClassVar[GMCMethod] = GMCMethod.SPARSE_OPT_FLOW

    def _estimate(self, prev_gray: np.ndarray, curr_gray: np.ndarray) -> np.ndarray:
        prev_points = cv2.goodFeaturesToTrack(prev_gray, maxCorners=1000, qualityLevel=0.01, minDistance=1, blockSize=3)
        if prev_points is None or len(prev_points) < _MIN_MATCHES:
            return _IDENTITY.copy()
        # nextPts must be passed as None so cv2 allocates it; the stub wrongly types it as required.
        curr_points, status, _ = cv2.calcOpticalFlowPyrLK(  # pyrefly: ignore[no-matching-overload]
            prev_gray, curr_gray, prev_points, None
        )
        if curr_points is None or status is None:
            return _IDENTITY.copy()
        tracked = status.ravel() == 1
        prev_matched = prev_points[tracked]
        curr_matched = curr_points[tracked]
        if len(prev_matched) < _MIN_MATCHES:
            return _IDENTITY.copy()
        warp, _ = cv2.estimateAffinePartial2D(prev_matched, curr_matched, method=cv2.RANSAC)
        if warp is None:
            return _IDENTITY.copy()
        return warp.astype(np.float32)
