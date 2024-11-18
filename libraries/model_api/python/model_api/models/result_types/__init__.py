"""Result types."""

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from .anomaly import AnomalyResult
from .classification import ClassificationResult
from .detection import Detection, DetectionResult
from .keypoint import DetectedKeypoints
from .segmentation import (
    Contour,
    ImageResultWithSoftPrediction,
    InstanceSegmentationResult,
    SegmentedObject,
    SegmentedObjectWithRects,
)
from .visual_prompting import PredictedMask, VisualPromptingResult, ZSLVisualPromptingResult

__all__ = [
    "AnomalyResult",
    "ClassificationResult",
    "Contour",
    "Detection",
    "DetectionResult",
    "DetectedKeypoints",
    "SegmentedObject",
    "SegmentedObjectWithRects",
    "ImageResultWithSoftPrediction",
    "InstanceSegmentationResult",
    "PredictedMask",
    "VisualPromptingResult",
    "ZSLVisualPromptingResult",
]
