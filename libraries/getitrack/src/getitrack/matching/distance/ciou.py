# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Complete-IoU distance metric (``1 - CIoU``)."""

from __future__ import annotations

from typing import ClassVar

import numpy as np

from getitrack.config import DistanceMetric
from getitrack.matching.distance.base import _EPS, BaseDistanceMetric, _pairwise_terms


class CIoUDistance(BaseDistanceMetric):
    """Pairwise Complete-IoU cost (``1 - CIoU``) in ``[0, ~2.31]``.

    CIoU extends DIoU with an aspect-ratio consistency term
    (``CIoU = IoU - rho^2 / c^2 - alpha * v``); the weight
    ``alpha = v / ((1 - IoU) + v)`` scales the term up only once overlap is
    reasonable. For disjoint boxes with divergent aspect ratios the cost can
    slightly exceed 2.
    """

    method: ClassVar[DistanceMetric] = DistanceMetric.CIOU

    def _compute(self, boxes_a: np.ndarray, boxes_b: np.ndarray) -> np.ndarray:
        """Return the CIoU cost from the shared pairwise terms."""
        terms = _pairwise_terms(boxes_a, boxes_b)
        distance_term = terms.center_dist_sq / np.maximum(terms.enclosing_diag_sq, _EPS)
        alpha = terms.aspect_v / np.maximum(1.0 - terms.iou + terms.aspect_v, _EPS)
        ciou = terms.iou - distance_term - alpha * terms.aspect_v
        return (1.0 - ciou).astype(np.float32)
