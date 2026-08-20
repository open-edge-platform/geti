# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Score fusion and Hungarian linear assignment for detection-to-track matching.

Both functions operate on plain numpy cost matrices; assignment uses
`scipy.optimize.linear_sum_assignment`.
"""

from __future__ import annotations

import numpy as np
from scipy.optimize import linear_sum_assignment

_INVALID_COST = 1e6


def fuse_score(cost_matrix: np.ndarray, det_scores: np.ndarray) -> np.ndarray:
    """Discount cost by per-detection confidence where boxes overlap: ``cost + max(sim, 0) * (1 - score)``.

    ``sim = 1 - cost`` is the similarity. In the overlap region (``sim >= 0``)
    this equals the usual ``1 - sim * score``, so a higher-confidence detection is
    cheaper to match. A wider-range metric (GIoU/DIoU/CIoU) makes ``sim`` negative
    for disjoint pairs; there is nothing to discount there, so the raw geometric
    cost is kept. Clamping ``sim`` at 0 keeps the fused cost non-increasing in
    ``score`` everywhere, so a low-confidence detection is never made cheaper than
    a high-confidence one in that region.
    """
    if cost_matrix.size == 0:
        return cost_matrix
    similarity = 1.0 - cost_matrix
    scores = np.asarray(det_scores, dtype=np.float32)[None, :]
    discount = np.maximum(similarity, 0.0) * (1.0 - scores)
    return (cost_matrix + discount).astype(np.float32)


def linear_assignment(
    cost_matrix: np.ndarray,
    thresh: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Solve Hungarian assignment gated by an inclusive maximum-cost threshold.

    Returns ``(matches, unmatched_rows, unmatched_cols)``. Pairs with
    ``cost > thresh`` are masked to a large sentinel before solving, so they
    cannot displace a valid match in the optimal assignment.
    """
    n_rows, n_cols = cost_matrix.shape
    if cost_matrix.size == 0:
        return (
            np.empty((0, 2), dtype=np.int64),
            np.arange(n_rows, dtype=np.int64),
            np.arange(n_cols, dtype=np.int64),
        )

    gated = np.where(cost_matrix > thresh, _INVALID_COST, cost_matrix)
    row_ind, col_ind = linear_sum_assignment(gated)
    keep = cost_matrix[row_ind, col_ind] <= thresh
    matched_rows = row_ind[keep]
    matched_cols = col_ind[keep]

    matches = np.stack([matched_rows, matched_cols], axis=1).astype(np.int64)
    matched_row_set = set(matched_rows.tolist())
    matched_col_set = set(matched_cols.tolist())
    unmatched_rows = np.array([i for i in range(n_rows) if i not in matched_row_set], dtype=np.int64)
    unmatched_cols = np.array([j for j in range(n_cols) if j not in matched_col_set], dtype=np.int64)
    return matches, unmatched_rows, unmatched_cols
