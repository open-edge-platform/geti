# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import numpy as np
import pytest
from model_api.models.result import DetectionResult


def _make_det():
    bboxes = np.array([[10, 20, 30, 40], [50, 60, 70, 80]], dtype=np.float32)
    labels = np.array([0, 1], dtype=np.int32)
    scores = np.array([0.9, 0.7], dtype=np.float32)
    label_names = ["cat", "dog"]
    saliency_map = np.ones((2, 10, 10), dtype=np.float32)
    feature_vector = np.array([1.0, 2.0, 3.0])
    return DetectionResult(
        bboxes=bboxes,
        labels=labels,
        scores=scores,
        label_names=label_names,
        saliency_map=saliency_map,
        feature_vector=feature_vector,
    )


def test_init_all_params():
    result = _make_det()
    assert len(result) == 2
    assert result.label_names == ["cat", "dog"]
    assert result.labels.dtype == np.int32


def test_init_default_scores():
    bboxes = np.array([[0, 0, 1, 1]])
    labels = np.array([0])
    result = DetectionResult(bboxes=bboxes, labels=labels)
    np.testing.assert_array_equal(result.scores, np.zeros(1))
    assert result.label_names == ["#"]
    assert result.saliency_map is None
    assert result.feature_vector is None


def test_str():
    result = _make_det()
    s = str(result)
    assert "cat" in s
    assert "dog" in s
    assert "0.900" in s


def test_get_obj_sizes():
    bboxes = np.array([[0, 0, 10, 20], [5, 5, 15, 25]], dtype=np.float32)
    labels = np.array([0, 1])
    result = DetectionResult(bboxes=bboxes, labels=labels)
    sizes = result.get_obj_sizes()
    np.testing.assert_array_equal(sizes, [200, 200])


def test_bboxes_setter_valid():
    result = _make_det()
    new_bboxes = np.array([[0, 0, 5, 5]], dtype=np.float32)
    result.bboxes = new_bboxes
    np.testing.assert_array_equal(result.bboxes, new_bboxes)


def test_bboxes_setter_invalid():
    result = _make_det()
    with pytest.raises(ValueError, match="Bounding boxes must be numpy array"):
        result.bboxes = [[0, 0, 5, 5]]


def test_labels_setter_invalid():
    result = _make_det()
    with pytest.raises(ValueError, match="Labels must be numpy array"):
        result.labels = [0, 1]


def test_scores_setter_invalid():
    result = _make_det()
    with pytest.raises(ValueError, match="Scores must be numpy array"):
        result.scores = [0.9]


def test_label_names_setter_invalid():
    result = _make_det()
    with pytest.raises(ValueError, match="Label names must be list"):
        result.label_names = np.array(["cat"])


def test_saliency_map_setter_invalid():
    result = _make_det()
    with pytest.raises(ValueError, match="Saliency map must be numpy array"):
        result.saliency_map = [1, 2, 3]


def test_feature_vector_setter_invalid():
    result = _make_det()
    with pytest.raises(ValueError, match="Feature vector must be numpy array"):
        result.feature_vector = [1.0, 2.0]


def test_labels_setter_valid():
    result = _make_det()
    new_labels = np.array([5, 6])
    result.labels = new_labels
    np.testing.assert_array_equal(result.labels, new_labels)


def test_scores_setter_valid():
    result = _make_det()
    new_scores = np.array([0.1, 0.2])
    result.scores = new_scores
    np.testing.assert_array_equal(result.scores, new_scores)


# --- DetectionResult setter success paths (lines 110, 126, 137) ---


def test_label_names_setter_valid():
    result = _make_det()
    result.label_names = ["a", "b"]
    assert result.label_names == ["a", "b"]


def test_saliency_map_setter_valid():
    result = _make_det()
    new_map = np.zeros((2, 5, 5), dtype=np.float32)
    result.saliency_map = new_map
    np.testing.assert_array_equal(result.saliency_map, new_map)


def test_feature_vector_setter_valid():
    result = _make_det()
    new_vec = np.array([4.0, 5.0])
    result.feature_vector = new_vec
    np.testing.assert_array_equal(result.feature_vector, new_vec)


def test_label_names_setter_invalid_str():
    result = _make_det()
    with pytest.raises(ValueError, match="Label names must be list"):
        result.label_names = "not_a_list"


def test_saliency_map_setter_invalid_str():
    result = _make_det()
    with pytest.raises(ValueError, match="Saliency map must be numpy"):
        result.saliency_map = "not_array"


def test_feature_vector_setter_invalid_str():
    result = _make_det()
    with pytest.raises(ValueError, match="Feature vector must be numpy"):
        result.feature_vector = "not_array"
