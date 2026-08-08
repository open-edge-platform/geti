# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Distance-IoU distance metric (``1 - DIoU``)."""

from __future__ import annotations

from typing import ClassVar

import numpy as np

from getitrack.config import DistanceMetric
from getitrack.matching.distance.base import _EPS, BaseDistanceMetric, _pairwise_terms


class DIoUDistance(BaseDistanceMetric):
    """Pairwise Distance-IoU cost (``1 - DIoU``) in ``[0, 2]``.

    DIoU adds to IoU the centre displacement normalised by the squared
    enclosing-box diagonal, favouring boxes whose centres are close even at
    identical overlap.
    """

    method: ClassVar[DistanceMetric] = DistanceMetric.DIOU

    def _compute(self, boxes_a: np.ndarray, boxes_b: np.ndarray) -> np.ndarray:
        """Return the DIoU cost from the shared pairwise terms."""
        terms = _pairwise_terms(boxes_a, boxes_b)
        diou = terms.iou - terms.center_dist_sq / np.maximum(terms.enclosing_diag_sq, _EPS)
        return (1.0 - diou).astype(np.float32)
