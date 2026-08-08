# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Detection-to-track association: IoU-family distance metrics and assignment."""

from getitrack.matching.assignment import fuse_score, linear_assignment
from getitrack.matching.distance import (
    BaseDistanceMetric,
    CIoUDistance,
    DIoUDistance,
    GIoUDistance,
    IoUDistance,
    iou_matrix,
)

__all__ = [
    "BaseDistanceMetric",
    "CIoUDistance",
    "DIoUDistance",
    "GIoUDistance",
    "IoUDistance",
    "fuse_score",
    "iou_matrix",
    "linear_assignment",
]
