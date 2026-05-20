"""Tests for visualizer."""

# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

import numpy as np
from model_api.models.result import (
    AnomalyResult,
)
from model_api.visualizer import Visualizer
from PIL import Image


def test_render(mock_image: Image, tmpdir: Path):
    """Test Visualizer.render()."""
    heatmap = np.ones(mock_image.size, dtype=np.uint8)
    heatmap *= 255

    mask = np.zeros(mock_image.size, dtype=np.uint8)
    mask[32:96, 32:96] = 255
    mask[40:80, 0:128] = 255

    anomaly_result = AnomalyResult(
        anomaly_map=heatmap,
        pred_boxes=np.array([[0, 0, 128, 128], [32, 32, 96, 96]]),
        pred_label="Anomaly",
        pred_mask=mask,
        pred_score=0.85,
    )

    visualizer = Visualizer()
    rendered_img = visualizer.render(mock_image, anomaly_result)

    assert isinstance(rendered_img, Image.Image)
    assert np.array(rendered_img).shape == np.array(mock_image).shape

    rendered_img_np = visualizer.render(np.array(mock_image), anomaly_result)

    assert isinstance(rendered_img_np, np.ndarray)
    assert rendered_img_np.shape == np.array(mock_image).shape


def test_show(mock_image: Image, monkeypatch):
    """Test Visualizer.show() with both PIL and numpy input."""
    heatmap = np.ones(mock_image.size, dtype=np.uint8) * 255
    anomaly_result = AnomalyResult(
        anomaly_map=heatmap,
        pred_boxes=None,
        pred_label="Anomaly",
        pred_mask=None,
        pred_score=0.85,
    )

    shown = []
    monkeypatch.setattr(Image.Image, "show", lambda self: shown.append(True))

    visualizer = Visualizer()
    # With PIL Image
    visualizer.show(mock_image, anomaly_result)
    assert len(shown) == 1

    # With numpy array (covers line 70-73)
    visualizer.show(np.array(mock_image), anomaly_result)
    assert len(shown) == 2


def test_save_with_numpy_input(mock_image: Image, tmpdir: Path):
    """Test Visualizer.save() with numpy input (covers line 77)."""
    heatmap = np.ones(mock_image.size, dtype=np.uint8) * 255
    anomaly_result = AnomalyResult(
        anomaly_map=heatmap,
        pred_boxes=None,
        pred_label="Anomaly",
        pred_mask=None,
        pred_score=0.85,
    )

    visualizer = Visualizer()
    visualizer.save(np.array(mock_image), anomaly_result, tmpdir / "numpy_save.jpg")
    assert Path(tmpdir / "numpy_save.jpg").exists()


def test_keypoint_scene_creation(mock_image: Image, tmpdir: Path):
    """Test KeypointScene creation via Visualizer (covers line 112)."""
    from model_api.models.result import DetectedKeypoints

    keypoint_result = DetectedKeypoints(
        keypoints=np.array([[50, 50], [70, 70]]),
        scores=np.array([0.95, 0.80]),
    )

    visualizer = Visualizer()
    rendered = visualizer.render(mock_image, keypoint_result)
    assert isinstance(rendered, Image.Image)

    visualizer.save(mock_image, keypoint_result, tmpdir / "keypoint_scene.jpg")
    assert Path(tmpdir / "keypoint_scene.jpg").exists()
