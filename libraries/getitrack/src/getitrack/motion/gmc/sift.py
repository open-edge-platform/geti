# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""SIFT feature-based camera-motion estimator (scale-invariant descriptors)."""

from __future__ import annotations

from typing import ClassVar

import cv2

from getitrack.config import GMCMethod
from getitrack.motion.gmc.features import FeatureMatchingEstimator


class SIFTEstimator(FeatureMatchingEstimator):
    """Detect and describe keypoints with SIFT, matched by L2 distance.

    The most robust of the descriptor-based methods on textured, low-motion
    footage, at the cost of being the slowest. SIFT is patent-free since 2020 and
    ships in the main OpenCV module.
    """

    method: ClassVar[GMCMethod] = GMCMethod.SIFT

    def _build_cv(self) -> tuple[cv2.Feature2D, cv2.Feature2D, cv2.DescriptorMatcher]:
        sift = cv2.SIFT.create(nOctaveLayers=3, contrastThreshold=0.02, edgeThreshold=20)
        return sift, sift, cv2.BFMatcher(cv2.NORM_L2)
