"""Keypoint result type."""

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import numpy as np

from .base import Result


class DetectedKeypoints(Result):
    def __init__(self, keypoints: np.ndarray, scores: np.ndarray) -> None:
        self.keypoints = keypoints
        self.scores = scores

    def __str__(self):
        return (
            f"keypoints: {self.keypoints.shape}, "
            f"keypoints_x_sum: {np.sum(self.keypoints[:, :1]):.3f}, "
            f"scores: {self.scores.shape} {np.sum(self.scores):.3f}"
        )
