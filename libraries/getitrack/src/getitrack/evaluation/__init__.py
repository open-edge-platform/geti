# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Multi-object-tracking evaluation utilities.

Computes standard CLEAR-MOT and identity metrics (MOTA, IDF1, id switches,
fragmentations, MT/ML) from predicted tracks against ground truth, both in
MOT-challenge text format.
"""

from getitrack.evaluation.mot import (
    MotFrame,
    MotMetrics,
    evaluate_mot,
    iou_distance_matrix,
    load_mot,
)

__all__ = [
    "MotFrame",
    "MotMetrics",
    "evaluate_mot",
    "iou_distance_matrix",
    "load_mot",
]
