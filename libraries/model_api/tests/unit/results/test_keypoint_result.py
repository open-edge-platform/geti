# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import numpy as np
from model_api.models.result import DetectedKeypoints


def test_init():
    keypoints = np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]])
    scores = np.array([0.9, 0.8, 0.7])
    result = DetectedKeypoints(keypoints=keypoints, scores=scores)
    np.testing.assert_array_equal(result.keypoints, keypoints)
    np.testing.assert_array_equal(result.scores, scores)


def test_str():
    keypoints = np.array([[1.0, 2.0], [3.0, 4.0]])
    scores = np.array([0.9, 0.8])
    result = DetectedKeypoints(keypoints=keypoints, scores=scores)
    s = str(result)
    assert "keypoints: (2, 2)" in s
    assert "scores: (2,)" in s
    assert "keypoints_x_sum" in s
