# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import numpy as np
import pytest
from model_api.models.result import InstanceSegmentationResult, RotatedSegmentationResult
from model_api.models.result.segmentation import Contour, ImageResultWithSoftPrediction


def _make_inst_seg():
    bboxes = np.array([[0, 0, 10, 10]], dtype=np.float32)
    labels = np.array([1], dtype=np.int32)
    masks = np.zeros((1, 20, 20), dtype=np.uint8)
    masks[0, 2:8, 2:8] = 1
    scores = np.array([0.9], dtype=np.float32)
    label_names = ["cat"]
    saliency_map = [np.ones((5, 5), dtype=np.float32)]
    feature_vector = np.array([1.0, 2.0, 3.0])
    return InstanceSegmentationResult(
        bboxes=bboxes,
        labels=labels,
        masks=masks,
        scores=scores,
        label_names=label_names,
        saliency_map=saliency_map,
        feature_vector=feature_vector,
    )


def test_instance_seg_init():
    result = _make_inst_seg()
    assert result.masks.shape == (1, 20, 20)
    assert len(result) == 1
    assert result.label_names == ["cat"]


def test_instance_seg_str():
    result = _make_inst_seg()
    s = str(result)
    assert "cat" in s
    assert "0.900" in s


def test_instance_seg_masks_setter_valid():
    result = _make_inst_seg()
    new_masks = np.ones((1, 10, 10), dtype=np.uint8)
    result.masks = new_masks
    np.testing.assert_array_equal(result.masks, new_masks)


def test_instance_seg_masks_setter_invalid():
    result = _make_inst_seg()
    with pytest.raises(ValueError, match="Masks must be numpy array"):
        result.masks = [[1, 2, 3]]


def test_instance_seg_saliency_map_setter_valid():
    result = _make_inst_seg()
    new_map = [np.zeros((3, 3))]
    result.saliency_map = new_map
    assert result.saliency_map is new_map


def test_instance_seg_saliency_map_setter_invalid():
    result = _make_inst_seg()
    with pytest.raises(ValueError, match="Saliency maps must be list"):
        result.saliency_map = np.zeros((3, 3))


def test_rotated_seg_init():
    bboxes = np.array([[0, 0, 10, 10]], dtype=np.float32)
    labels = np.array([0], dtype=np.int32)
    masks = np.zeros((1, 20, 20), dtype=np.uint8)
    masks[0, 2:8, 2:8] = 1
    rotated_rects = [((5.0, 5.0), (6.0, 6.0), 45.0)]
    result = RotatedSegmentationResult(
        bboxes=bboxes,
        labels=labels,
        masks=masks,
        rotated_rects=rotated_rects,
        scores=np.array([0.8]),
        label_names=["dog"],
        saliency_map=[np.ones((3, 3))],
        feature_vector=np.array([1.0]),
    )
    assert len(result.rotated_rects) == 1


def test_rotated_seg_str():
    bboxes = np.array([[0, 0, 10, 10]], dtype=np.float32)
    labels = np.array([0], dtype=np.int32)
    masks = np.zeros((1, 20, 20), dtype=np.uint8)
    masks[0, 2:8, 2:8] = 1
    rotated_rects = [((5.0, 5.0), (6.0, 6.0), 45.0)]
    result = RotatedSegmentationResult(
        bboxes=bboxes,
        labels=labels,
        masks=masks,
        rotated_rects=rotated_rects,
        scores=np.array([0.8]),
        label_names=["dog"],
        saliency_map=[np.ones((3, 3))],
        feature_vector=np.array([1.0]),
    )
    s = str(result)
    assert "RotatedRect" in s
    assert "dog" in s


def test_rotated_rects_setter_invalid():
    bboxes = np.array([[0, 0, 10, 10]], dtype=np.float32)
    labels = np.array([0], dtype=np.int32)
    masks = np.zeros((1, 20, 20), dtype=np.uint8)
    rotated_rects = [((5.0, 5.0), (6.0, 6.0), 45.0)]
    result = RotatedSegmentationResult(
        bboxes=bboxes,
        labels=labels,
        masks=masks,
        rotated_rects=rotated_rects,
        saliency_map=[np.array([])],
    )
    with pytest.raises(ValueError, match="RotatedRects must be list"):
        result.rotated_rects = "not a list"


def test_contour_str_repr():
    contour = Contour(label="car", probability=0.95, shape=[(0, 0), (1, 0), (1, 1)])
    s = str(contour)
    assert "car" in s
    assert "0.950" in s
    assert repr(contour) == s


def test_contour_with_excluded_shapes():
    contour = Contour(
        label="building",
        probability=0.8,
        shape=[(0, 0), (10, 0), (10, 10), (0, 10)],
        excluded_shapes=[[(2, 2), (4, 2), (4, 4)]],
    )
    s = str(contour)
    assert "building" in s
    assert "1" in s  # 1 excluded shape


def test_image_result_with_soft_prediction():
    rng = np.random.default_rng(42)
    result_img = np.zeros((10, 10), dtype=np.uint8)
    soft = rng.random((10, 10)).astype(np.float32)
    sal = rng.random((3, 10, 10)).astype(np.float32)
    fv = np.array([1.0, 2.0])
    result = ImageResultWithSoftPrediction(
        resultImage=result_img,
        soft_prediction=soft,
        saliency_map=sal,
        feature_vector=fv,
    )
    assert result.resultImage is result_img
    s = str(result)
    assert "[10,10]" in s  # soft prediction shape
    assert "[2]" in s  # feature vector shape
