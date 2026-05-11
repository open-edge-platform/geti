"""Tests for scene."""

# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

import numpy as np
import pytest
from model_api.models.result import (
    AnomalyResult,
    ClassificationResult,
    DetectionResult,
    ImageResultWithSoftPrediction,
    InstanceSegmentationResult,
)
from model_api.models.result.classification import Label
from model_api.visualizer import Visualizer
from PIL import Image


def test_anomaly_scene(mock_image: Image, tmpdir: Path):
    """Test if the anomaly scene is created."""
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
    visualizer.save(mock_image, anomaly_result, tmpdir / "anomaly_scene.jpg")
    assert Path(tmpdir / "anomaly_scene.jpg").exists()


def test_classification_scene(mock_image: Image, tmpdir: Path):
    """Test if the classification scene is created."""
    classification_result = ClassificationResult(
        top_labels=[
            Label(name="cat", confidence=0.95),
            Label(name="dog", confidence=0.90),
        ],
        saliency_map=np.ones(mock_image.size, dtype=np.uint8),
    )
    visualizer = Visualizer()
    visualizer.save(
        mock_image,
        classification_result,
        tmpdir / "classification_scene.jpg",
    )
    assert Path(tmpdir / "classification_scene.jpg").exists()


def test_detection_scene(mock_image: Image, tmpdir: Path):
    """Test if the detection scene is created."""
    detection_result = DetectionResult(
        bboxes=np.array([[0, 0, 128, 128], [32, 32, 96, 96]]),
        labels=np.array([0, 1]),
        label_names=["person", "car"],
        scores=np.array([0.85, 0.75]),
        saliency_map=(np.ones((1, 2, 6, 8)) * 255).astype(np.uint8),
    )
    visualizer = Visualizer()
    visualizer.save(mock_image, detection_result, tmpdir / "detection_scene.jpg")
    assert Path(tmpdir / "detection_scene.jpg").exists()


@pytest.mark.parametrize("with_saliency_map", [True, False])
def test_segmentation_scene(mock_image: Image, tmpdir: Path, with_saliency_map: bool):
    """Test if the segmentation scene is created."""
    visualizer = Visualizer()

    instance_segmentation_result = InstanceSegmentationResult(
        bboxes=np.array([[0, 0, 128, 128], [32, 32, 96, 96]]),
        labels=np.array([0, 1]),
        masks=np.array(
            [
                np.ones((128, 128), dtype=np.uint8),
            ],
        ),
        scores=np.array([0.85, 0.75]),
        label_names=["person", "car"],
        saliency_map=[np.ones((128, 128), dtype=np.uint8) * 255] if with_saliency_map else None,
        feature_vector=np.array([1, 2, 3, 4]),
    )

    visualizer.save(
        mock_image,
        instance_segmentation_result,
        tmpdir / "instance_segmentation_scene.jpg",
    )
    assert Path(tmpdir / "instance_segmentation_scene.jpg").exists()

    # Test ImageResultWithSoftPrediction
    soft_prediction_result = ImageResultWithSoftPrediction(
        resultImage=np.array(
            [[0, 1, 2], [1, 2, 0], [2, 0, 1]],
            dtype=np.uint8,
        ),  # 3x3 test image with 3 classes
        soft_prediction=np.ones(
            (3, 3, 3),
            dtype=np.float32,
        ),  # 3 classes, 3x3 prediction
        saliency_map=np.ones((3, 3), dtype=np.uint8) * 255 if with_saliency_map else None,
        feature_vector=np.array([1, 2, 3, 4]),
    )

    visualizer.save(
        mock_image,
        soft_prediction_result,
        tmpdir / "soft_prediction_scene.jpg",
    )
    assert Path(tmpdir / "soft_prediction_scene.jpg").exists()
