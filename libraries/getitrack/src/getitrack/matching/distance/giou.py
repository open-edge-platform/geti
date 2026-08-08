# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Generalised-IoU distance metric (``1 - GIoU``)."""

from __future__ import annotations

from typing import ClassVar

import numpy as np

from getitrack.config import DistanceMetric
from getitrack.matching.distance.base import _EPS, BaseDistanceMetric, _pairwise_terms


class GIoUDistance(BaseDistanceMetric):
    """Pairwise Generalised-IoU cost (``1 - GIoU``) in ``[0, 2]``.

    GIoU subtracts from IoU the enclosing-box fraction left uncovered by the
    union, so it stays informative for disjoint boxes where plain IoU saturates.
    """

    method: ClassVar[DistanceMetric] = DistanceMetric.GIOU

    def _compute(self, boxes_a: np.ndarray, boxes_b: np.ndarray) -> np.ndarray:
        """Return the GIoU cost from the shared pairwise terms."""
        terms = _pairwise_terms(boxes_a, boxes_b)
        penalty = (terms.enclosing_area - terms.union) / np.maximum(terms.enclosing_area, _EPS)
        giou = terms.iou - penalty
        return (1.0 - giou).astype(np.float32)
