# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Detection-to-track association: distance metrics, appearance, and assignment."""

from getitrack.matching.appearance import (
    cosine_distance,
    fuse_appearance_cost,
    l2_normalize,
)
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
    "cosine_distance",
    "fuse_appearance_cost",
    "fuse_score",
    "iou_matrix",
    "l2_normalize",
    "linear_assignment",
]
