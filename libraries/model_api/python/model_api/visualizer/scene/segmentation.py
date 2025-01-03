"""Segmentation Scene."""

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from model_api.models.result import InstanceSegmentationResult

from .scene import Scene


class SegmentationScene(Scene):
    """Segmentation Scene."""

    def __init__(self, result: InstanceSegmentationResult) -> None:
        self.result = result
