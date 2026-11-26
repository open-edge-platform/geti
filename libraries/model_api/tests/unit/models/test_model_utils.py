#
# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#

import numpy as np
from model_api.models import utils


def test_nms_basic():
    boxes = np.array([
        [0, 0, 1, 1],
        [0, 0, 1, 1],
        [1, 1, 2, 2],
    ])
    scores = np.array([0.9, 0.8, 0.7])
    keep = utils.nms(boxes, scores, iou_threshold=0.5)
    assert set(keep) == {0, 2}


def test_nms_no_overlap():
    boxes = np.array([
        [0, 0, 1, 1],
        [2, 2, 3, 3],
        [4, 4, 5, 5],
    ])
    scores = np.array([0.5, 0.6, 0.7])
    keep = utils.nms(boxes, scores, iou_threshold=0.1)
    assert set(keep) == {2, 1, 0}


def test_nms_max_predictions():
    boxes = np.array([
        [0, 0, 1, 1],
        [0, 0, 1, 1],
        [1, 1, 2, 2],
    ])
    scores = np.array([0.9, 0.8, 0.7])
    keep = utils.nms(boxes, scores, iou_threshold=0.5, max_predictions=1)
    assert keep == [0]


def test_nms_include_boundaries():
    boxes = np.array([
        [0, 0, 1, 1],
        [0, 0, 1, 1],
        [1, 1, 2, 2],
    ])
    scores = np.array([0.9, 0.8, 0.7])
    keep = utils.nms(boxes, scores, iou_threshold=0.5, include_boundaries=True)
    assert set(keep) == {0, 2}


def test_multiclass_nms_basic():
    boxes = np.array([
        [0, 0, 1, 1],
        [0, 0, 1, 1],
        [1, 1, 2, 2],
        [2, 2, 3, 3],
    ])
    scores = np.array([0.9, 0.8, 0.7, 0.95])
    labels = np.array([0, 1, 0, 1])
    keep = utils.multiclass_nms(boxes, scores, labels, iou_threshold=0.5)
    # Should keep highest score per class, and non-overlapping
    assert set(keep) == {0, 1, 2, 3}


def test_multiclass_nms_same_class():
    boxes = np.array([
        [0, 0, 1, 1],
        [0, 0, 1, 1],
        [1, 1, 2, 2],
        [2, 2, 3, 3],
    ])
    scores = np.array([0.9, 0.8, 0.7, 0.95])
    labels = np.array([0, 0, 0, 0])
    keep = utils.multiclass_nms(boxes, scores, labels, iou_threshold=0.5)
    # Should keep highest score per class, and non-overlapping
    assert set(keep) == {0, 2, 3}


def test_multiclass_nms_max_predictions():
    boxes = np.array([
        [0, 0, 1, 1],
        [0, 0, 1, 1],
        [1, 1, 2, 2],
        [2, 2, 3, 3],
    ])
    scores = np.array([0.9, 0.8, 0.7, 0.95])
    labels = np.array([0, 1, 0, 1])
    keep = utils.multiclass_nms(boxes, scores, labels, iou_threshold=0.5, max_predictions=2)
    assert len(keep) == 2


def test_multiclass_nms_empty():
    boxes = np.empty((0, 4))
    scores = np.array([])
    labels = np.array([])
    keep = utils.multiclass_nms(boxes, scores, labels)
    assert keep == []


def test_multiclass_nms_include_boundaries():
    boxes = np.array([
        [0, 0, 1, 1],
        [0, 0, 1, 1],
        [1, 1, 2, 2],
        [2, 2, 3, 3],
    ])
    scores = np.array([0.9, 0.8, 0.7, 0.95])
    labels = np.array([0, 1, 0, 1])
    keep = utils.multiclass_nms(boxes, scores, labels, iou_threshold=0.5, include_boundaries=True)
    assert set(keep) == {0, 1, 2, 3}


def test_calculate_nms_no_execute():
    boxes = np.array([
        [0, 0, 1, 1],
        [0, 0, 1, 1],
    ])
    scores = np.array([0.9, 0.8])
    labels = np.array([0, 1])
    keep = utils.calculate_nms(boxes, scores, labels, execute_nms=False)
    assert keep == [0, 1]


def test_calculate_nms_agnostic():
    boxes = np.array([
        [0, 0, 1, 1],
        [0, 0, 1, 1],
        [1, 1, 2, 2],
    ])
    scores = np.array([0.9, 0.8, 0.7])
    labels = np.array([0, 1, 0])
    keep = utils.calculate_nms(boxes, scores, labels, iou_threshold=0.5, agnostic_nms=True, execute_nms=True)
    assert set(keep) == {0, 2}


def test_calculate_nms_multiclass():
    boxes = np.array([
        [0, 0, 1, 1],
        [0, 0, 1, 1],
        [1, 1, 2, 2],
        [2, 2, 3, 3],
    ])
    scores = np.array([0.9, 0.8, 0.7, 0.95])
    labels = np.array([0, 1, 0, 1])
    keep = utils.calculate_nms(boxes, scores, labels, iou_threshold=0.5, execute_nms=True)
    assert set(keep) == {0, 1, 2, 3}


def test_calculate_nms_max_predictions():
    boxes = np.array([
        [0, 0, 1, 1],
        [0, 0, 1, 1],
        [1, 1, 2, 2],
        [2, 2, 3, 3],
    ])
    scores = np.array([0.9, 0.8, 0.7, 0.95])
    labels = np.array([0, 1, 0, 1])
    keep = utils.calculate_nms(boxes, scores, labels, iou_threshold=0.5, max_predictions=2, execute_nms=True)
    assert len(keep) == 2
