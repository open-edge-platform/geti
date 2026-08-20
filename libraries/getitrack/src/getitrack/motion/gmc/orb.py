# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""ORB feature-based camera-motion estimator (FAST corners + ORB descriptors)."""

from __future__ import annotations

from typing import ClassVar

import cv2

from getitrack.config import GMCMethod
from getitrack.motion.gmc.features import FeatureMatchingEstimator


class ORBEstimator(FeatureMatchingEstimator):
    """Detect FAST corners, describe them with ORB, and match with Hamming distance.

    The fastest of the descriptor-based methods; a lightweight alternative to
    sparse optical flow that re-detects features each frame rather than tracking
    them.
    """

    method: ClassVar[GMCMethod] = GMCMethod.ORB

    def _build_cv(self) -> tuple[cv2.Feature2D, cv2.Feature2D, cv2.DescriptorMatcher]:
        return cv2.FastFeatureDetector.create(20), cv2.ORB.create(), cv2.BFMatcher(cv2.NORM_HAMMING)
