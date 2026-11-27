# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import numpy as np
from model_api.models.utils import calculate_nms, multiclass_nms, nms


def test_nms_basic():
    boxes = np.array(
        [
            [0, 0, 10, 10],
            [1, 1, 11, 11],
            [50, 50, 60, 60],
        ],
        dtype=np.float32,
    )
    scores = np.array([0.9, 0.8, 0.7])
    keep = nms(boxes, scores, iou_threshold=0.5)
    assert 0 in keep
    assert 2 in keep


def test_nms_no_overlap():
    boxes = np.array(
        [
            [0, 0, 10, 10],
            [20, 20, 30, 30],
        ],
        dtype=np.float32,
    )
    scores = np.array([0.9, 0.8])
    keep = nms(boxes, scores, iou_threshold=0.5)
    assert len(keep) == 2


def test_nms_full_overlap():
    boxes = np.array(
        [
            [0, 0, 10, 10],
            [0, 0, 10, 10],
        ],
        dtype=np.float32,
    )
    scores = np.array([0.9, 0.8])
    keep = nms(boxes, scores, iou_threshold=0.5)
    assert len(keep) == 1


def test_nms_with_max_predictions():
    boxes = np.array(
        [
            [0, 0, 10, 10],
            [20, 20, 30, 30],
            [40, 40, 50, 50],
        ],
        dtype=np.float32,
    )
    scores = np.array([0.9, 0.8, 0.7])
    keep = nms(boxes, scores, iou_threshold=0.5, max_predictions=2)
    assert len(keep) <= 2


def test_nms_include_boundaries():
    boxes = np.array([[0, 0, 10, 10]], dtype=np.float32)
    scores = np.array([0.9])
    keep = nms(boxes, scores, iou_threshold=0.5, include_boundaries=True)
    assert len(keep) == 1


def test_multiclass_nms_basic():
    boxes = np.array(
        [
            [0, 0, 10, 10],
            [1, 1, 11, 11],
            [50, 50, 60, 60],
        ],
        dtype=np.float32,
    )
    scores = np.array([0.9, 0.8, 0.7])
    labels = np.array([0, 0, 1])
    keep = multiclass_nms(boxes, scores, labels, iou_threshold=0.5)
    assert 0 in keep
    assert 2 in keep


def test_multiclass_nms_empty():
    boxes = np.array([], dtype=np.float32).reshape(0, 4)
    scores = np.array([], dtype=np.float32)
    labels = np.array([], dtype=np.int32)
    keep = multiclass_nms(boxes, scores, labels)
    assert keep == []


def test_calculate_nms_no_execute():
    boxes = np.array([[0, 0, 10, 10]], dtype=np.float32)
    scores = np.array([0.9])
    labels = np.array([0])
    keep = calculate_nms(boxes, scores, labels, execute_nms=False)
    assert keep == [0]


def test_calculate_nms_agnostic():
    boxes = np.array(
        [
            [0, 0, 10, 10],
            [1, 1, 11, 11],
        ],
        dtype=np.float32,
    )
    scores = np.array([0.9, 0.8])
    labels = np.array([0, 1])
    keep = calculate_nms(boxes, scores, labels, execute_nms=True, agnostic_nms=True, iou_threshold=0.5)
    assert len(keep) >= 1
