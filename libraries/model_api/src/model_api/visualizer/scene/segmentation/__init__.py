"""Segmentation Scene."""

# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from .instance_segmentation import InstanceSegmentationScene
from .segmentation import SegmentationScene

__all__ = [
    "InstanceSegmentationScene",
    "SegmentationScene",
]
