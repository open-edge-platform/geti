# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Shared feature-matching camera-motion pipeline for ORB and SIFT.

`FeatureMatchingEstimator` holds the pipeline both descriptor-based methods
share: detect keypoints inside a border-cropped mask, describe them, match with
a ratio test, drop spatial outliers, and fit a RANSAC partial affine. Concrete
methods (ORB, SIFT) only supply the OpenCV detector, extractor, and matcher via
`_build_cv`. Mirrors Ultralytics' ``apply_features`` (border mask only; detection
regions are not excluded, matching its behaviour when no detections are passed).
"""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING

import cv2
import numpy as np

if TYPE_CHECKING:
    from collections.abc import Sequence

from getitrack.motion.gmc.base import BaseMotionEstimator

_IDENTITY = np.eye(2, 3, dtype=np.float32)


class FeatureMatchingEstimator(BaseMotionEstimator):
    """Estimate camera motion by matching descriptors between consecutive frames."""

    _LOWE_RATIO = 0.9  # a match is kept when its distance is below this fraction of the runner-up's.
    _MAX_SPATIAL_FRACTION = 0.25  # reject matches displaced by more than this fraction of the frame.
    _INLIER_STD = 2.5  # keep displacements within this many standard deviations of the mean.
    _MIN_MATCHES = 4  # estimateAffinePartial2D needs at least this many correspondences.
    _BORDER_FRACTION = 0.02  # ignore keypoints within this fraction of each edge.

    def __init__(self, *, downscale: int = 2) -> None:
        super().__init__(downscale=downscale)
        self._detector, self._extractor, self._matcher = self._build_cv()

    @abstractmethod
    def _build_cv(self) -> tuple[cv2.Feature2D, cv2.Feature2D, cv2.DescriptorMatcher]:
        """Return the ``(detector, extractor, matcher)`` OpenCV objects for this method."""

    def _border_mask(self, gray: np.ndarray) -> np.ndarray:
        """A mask that excludes a small border, where keypoints are least reliable."""
        height, width = gray.shape[:2]
        mask = np.zeros_like(gray)
        y0, y1 = int(self._BORDER_FRACTION * height), int((1 - self._BORDER_FRACTION) * height)
        x0, x1 = int(self._BORDER_FRACTION * width), int((1 - self._BORDER_FRACTION) * width)
        mask[y0:y1, x0:x1] = 255
        return mask

    def _describe(self, gray: np.ndarray, mask: np.ndarray) -> tuple[Sequence[cv2.KeyPoint], np.ndarray | None]:
        """Detect and describe keypoints in ``gray`` within ``mask``."""
        keypoints = self._detector.detect(gray, mask)
        keypoints, descriptors = self._extractor.compute(gray, keypoints)
        return keypoints, descriptors

    def _estimate(self, prev_gray: np.ndarray, curr_gray: np.ndarray) -> np.ndarray:
        mask = self._border_mask(curr_gray)
        prev_kp, prev_desc = self._describe(prev_gray, mask)
        curr_kp, curr_desc = self._describe(curr_gray, mask)
        too_few = len(prev_kp) < self._MIN_MATCHES or len(curr_kp) < self._MIN_MATCHES
        if prev_desc is None or curr_desc is None or too_few:
            return _IDENTITY.copy()

        height, width = curr_gray.shape[:2]
        max_spatial = self._MAX_SPATIAL_FRACTION * np.array([width, height])
        matches: list[cv2.DMatch] = []
        displacements: list[tuple[float, float]] = []
        for pair in self._matcher.knnMatch(prev_desc, curr_desc, 2):
            if len(pair) < 2:
                continue
            match, runner_up = pair
            if match.distance >= self._LOWE_RATIO * runner_up.distance:
                continue
            prev_pt = prev_kp[match.queryIdx].pt
            curr_pt = curr_kp[match.trainIdx].pt
            delta = (prev_pt[0] - curr_pt[0], prev_pt[1] - curr_pt[1])
            if abs(delta[0]) < max_spatial[0] and abs(delta[1]) < max_spatial[1]:
                matches.append(match)
                displacements.append(delta)
        if len(matches) < self._MIN_MATCHES:
            return _IDENTITY.copy()

        # Keep displacements close to the mean (abs distance, unlike the reference
        # which only filters positive deviations); the epsilon admits a pure,
        # noise-free translation, where the standard deviation is zero.
        deltas = np.array(displacements)
        inliers = np.abs(deltas - deltas.mean(axis=0)) < self._INLIER_STD * deltas.std(axis=0) + 1e-6
        prev_pts = np.array(
            [prev_kp[m.queryIdx].pt for i, m in enumerate(matches) if inliers[i, 0] and inliers[i, 1]], dtype=np.float32
        )
        curr_pts = np.array(
            [curr_kp[m.trainIdx].pt for i, m in enumerate(matches) if inliers[i, 0] and inliers[i, 1]], dtype=np.float32
        )
        if len(prev_pts) < self._MIN_MATCHES:
            return _IDENTITY.copy()
        warp, _ = cv2.estimateAffinePartial2D(prev_pts, curr_pts, method=cv2.RANSAC)
        if warp is None:
            return _IDENTITY.copy()
        return warp.astype(np.float32)
