# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import numpy as np
from model_api.models.result import AnomalyResult


def test_init_with_all_params():
    rng = np.random.default_rng(42)
    anomaly_map = rng.random((10, 10)).astype(np.float32)
    pred_boxes = np.array([[0, 0, 10, 10]])
    pred_mask = np.zeros((10, 10), dtype=np.uint8)
    result = AnomalyResult(
        anomaly_map=anomaly_map,
        pred_boxes=pred_boxes,
        pred_label="anomalous",
        pred_mask=pred_mask,
        pred_score=0.85,
    )
    np.testing.assert_array_equal(result.anomaly_map, anomaly_map)
    np.testing.assert_array_equal(result.pred_boxes, pred_boxes)
    assert result.pred_label == "anomalous"
    np.testing.assert_array_equal(result.pred_mask, pred_mask)
    assert result.pred_score == 0.85


def test_init_defaults():
    result = AnomalyResult()
    assert result.anomaly_map is None
    assert result.pred_boxes is None
    assert result.pred_label is None
    assert result.pred_mask is None
    assert result.pred_score is None


def test_compute_min_max():
    tensor = np.array([1.0, 5.0, 3.0, 2.0])
    min_val, max_val = tensor.min(), tensor.max()
    assert min_val == 1.0
    assert max_val == 5.0


def test_str_with_valid_data():
    anomaly_map = np.array([[0.1, 0.9], [0.3, 0.7]])
    pred_mask = np.array([[0, 1], [0, 1]])
    result = AnomalyResult(
        anomaly_map=anomaly_map,
        pred_mask=pred_mask,
        pred_score=0.85,
        pred_label="anomalous",
    )
    s = str(result)
    assert "anomaly_map min:0.1 max:0.9" in s
    assert "pred_score:0.8" in s
    assert "pred_label:anomalous" in s
    assert "pred_mask min:0 max:1" in s


def test_str_with_no_score():
    anomaly_map = np.array([[0.0, 1.0]])
    pred_mask = np.array([[0, 1]])
    result = AnomalyResult(
        anomaly_map=anomaly_map,
        pred_mask=pred_mask,
        pred_score=None,
        pred_label="normal",
    )
    s = str(result)
    assert "pred_score:0.0" in s
