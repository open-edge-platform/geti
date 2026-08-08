# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""IoU-family pairwise distance metrics for detection-to-track association.

Each metric is a `BaseDistanceMetric` subclass resolved by
`BaseDistanceMetric.from_metric` via `DistanceMetric`. Importing the concrete
metric modules here populates the registry as an import side effect, so callers
only need to import this package. Every metric instance is callable as
``metric(boxes_a, boxes_b) -> cost``.
"""

from getitrack.matching.distance.base import BaseDistanceMetric, iou_matrix
from getitrack.matching.distance.ciou import CIoUDistance
from getitrack.matching.distance.diou import DIoUDistance
from getitrack.matching.distance.giou import GIoUDistance
from getitrack.matching.distance.iou import IoUDistance

__all__ = [
    "BaseDistanceMetric",
    "CIoUDistance",
    "DIoUDistance",
    "GIoUDistance",
    "IoUDistance",
    "iou_matrix",
]
