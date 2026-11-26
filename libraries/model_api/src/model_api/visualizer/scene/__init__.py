"""Result visualization Scene."""

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from .anomaly import AnomalyScene
from .classification import ClassificationScene
from .detection import DetectionScene
from .keypoint import KeypointScene
from .scene import Scene
from .segmentation import InstanceSegmentationScene, SegmentationScene
from .visual_prompting import VisualPromptingScene

__all__ = [
    "AnomalyScene",
    "ClassificationScene",
    "DetectionScene",
    "InstanceSegmentationScene",
    "KeypointScene",
    "Scene",
    "SegmentationScene",
    "VisualPromptingScene",
]
