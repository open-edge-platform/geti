# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Plain IoU distance metric (``1 - IoU``)."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from getitrack.config import DistanceMetric
from getitrack.matching.distance.base import BaseDistanceMetric, iou_matrix

if TYPE_CHECKING:
    import numpy as np


class IoUDistance(BaseDistanceMetric):
    """Pairwise IoU cost (``1 - IoU``) in ``[0, 1]``."""

    method: ClassVar[DistanceMetric] = DistanceMetric.IOU

    def _compute(self, boxes_a: np.ndarray, boxes_b: np.ndarray) -> np.ndarray:
        """Return the IoU cost (``1 - IoU``)."""
        return 1.0 - iou_matrix(boxes_a, boxes_b)
