"""Result types."""

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from .anomaly import AnomalyResult
from .classification import ClassificationResult, Label
from .detection import DetectionResult
from .keypoint import DetectedKeypoints
from .segmentation import (
    Contour,
    ImageResultWithSoftPrediction,
    InstanceSegmentationResult,
    RotatedSegmentationResult,
)
from .visual_prompting import PredictedMask, VisualPromptingResult, ZSLVisualPromptingResult

__all__ = [
    "AnomalyResult",
    "ClassificationResult",
    "Contour",
    "DetectionResult",
    "DetectedKeypoints",
    "Label",
    "ImageResultWithSoftPrediction",
    "InstanceSegmentationResult",
    "PredictedMask",
    "VisualPromptingResult",
    "ZSLVisualPromptingResult",
    "RotatedSegmentationResult",
]
