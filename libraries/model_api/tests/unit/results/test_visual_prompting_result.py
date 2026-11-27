# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import numpy as np
from model_api.models.result.visual_prompting import (
    PredictedMask,
    VisualPromptingResult,
    ZSLVisualPromptingResult,
)


def test_visual_prompting_result_init():
    result = VisualPromptingResult()
    assert result.upscaled_masks is None
    assert result.hard_predictions is None
    assert result.best_iou is None


def test_visual_prompting_result_init_with_values():
    masks = [np.ones((4, 4))]
    hard = [np.zeros((4, 4), dtype=np.uint8)]
    result = VisualPromptingResult(upscaled_masks=masks, hard_predictions=hard)
    assert result.upscaled_masks is masks
    assert result.hard_predictions is hard


def test_visual_prompting_result_str():
    masks = [np.array([[0.1, 0.9], [0.3, 0.7]])]
    hard = [np.zeros((2, 2), dtype=np.uint8)]
    result = VisualPromptingResult(upscaled_masks=masks, hard_predictions=hard)
    s = str(result)
    assert "upscaled_masks min:" in s
    assert "hard_predictions shape:" in s


def test_predicted_mask_init():
    mask = [np.ones((4, 4), dtype=np.uint8)]
    points = [np.array([1.0, 2.0])]
    scores = [0.95]
    pm = PredictedMask(mask=mask, points=points, scores=scores)
    assert pm.mask is mask
    assert pm.points is points
    assert pm.scores is scores


def test_predicted_mask_str_with_list_points():
    mask = [np.ones((2, 2), dtype=np.uint8)]
    points = [np.array([1.5, 2.5]), np.array([3.0, 4.0])]
    scores = [0.9, 0.8]
    pm = PredictedMask(mask=mask, points=points, scores=scores)
    s = str(pm)
    assert "mask sum:" in s
    assert "iou:" in s
    assert "1.5" in s


def test_predicted_mask_str_with_ndarray_points():
    mask = [np.ones((2, 2), dtype=np.uint8)]
    points = np.array([[1.5, 2.5], [3.0, 4.0]])
    scores = np.array([0.9, 0.8])
    pm = PredictedMask(mask=mask, points=points, scores=scores)
    s = str(pm)
    assert "mask sum:" in s
    assert "iou:" in s


def test_zsl_visual_prompting_result_init():
    mask = [np.ones((2, 2), dtype=np.uint8)]
    pm = PredictedMask(mask=mask, points=[np.array([1.0, 2.0])], scores=[0.9])
    data = {0: pm}
    result = ZSLVisualPromptingResult(data=data)
    assert result.data is data


def test_zsl_visual_prompting_result_str():
    mask = [np.ones((2, 2), dtype=np.uint8)]
    pm = PredictedMask(mask=mask, points=[np.array([1.0, 2.0])], scores=[0.9])
    result = ZSLVisualPromptingResult(data={0: pm})
    s = str(result)
    assert "mask sum:" in s


def test_zsl_visual_prompting_result_get_mask():
    mask = [np.ones((2, 2), dtype=np.uint8)]
    pm = PredictedMask(mask=mask, points=[np.array([1.0, 2.0])], scores=[0.9])
    result = ZSLVisualPromptingResult(data={5: pm})
    retrieved = result.get_mask(5)
    assert retrieved is pm
