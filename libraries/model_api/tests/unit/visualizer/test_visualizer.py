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
