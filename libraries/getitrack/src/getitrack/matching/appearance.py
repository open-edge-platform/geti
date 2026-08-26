# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Appearance (ReID) cost computation and IoU-gated fusion.

Operate on plain numpy feature and cost matrices. `cosine_distance` returns the
pairwise cosine-distance matrix; `fuse_appearance_cost` blends an IoU cost with an
appearance cost and gates the result by an IoU floor.
"""

from __future__ import annotations

import numpy as np
from scipy.spatial.distance import cdist

_EPS = 1e-12


def l2_normalize(features: np.ndarray) -> np.ndarray:
    """Return ``features`` scaled to unit L2 norm along the last axis.

    Args:
        features: ``(..., D)`` float array. A ``(D,)`` vector or an ``(N, D)``
            batch are both accepted.

    Returns:
        A float32 array of the same shape with each row rescaled to unit norm.
        Zero rows are left at zero (division is floored by a small epsilon).
    """
    arr = np.asarray(features, dtype=np.float32)
    norms = np.linalg.norm(arr, axis=-1, keepdims=True)
    return (arr / np.maximum(norms, _EPS)).astype(np.float32)


def cosine_distance(features_a: np.ndarray, features_b: np.ndarray) -> np.ndarray:
    """Compute pairwise cosine distance between two feature sets.

    Cosine distance is ``1 - cosine_similarity``. For L2-normalised inputs this
    lands in ``[0, 2]``: ``~0`` for identical direction, ``~1`` for orthogonal
    vectors, and ``~2`` for opposite vectors. The result is clipped to
    ``[0, 2]`` to absorb floating-point overshoot.

    Args:
        features_a: ``(M, D)`` float array of query features.
        features_b: ``(N, D)`` float array of gallery features.

    Returns:
        ``(M, N)`` float32 cosine-distance matrix.
    """
    m, n = features_a.shape[0], features_b.shape[0]
    if m == 0 or n == 0:
        return np.zeros((m, n), dtype=np.float32)
    return np.clip(cdist(features_a, features_b, metric="cosine"), 0.0, 2.0).astype(np.float32)


def fuse_appearance_cost(
    iou_cost: np.ndarray,
    appearance_cost: np.ndarray,
    *,
    appearance_weight: float,
    iou_floor: float,
) -> np.ndarray:
    """Blend an IoU cost with an appearance cost, gated by IoU proximity.

    The appearance term is applied only where the pair's IoU (``1 - iou_cost``)
    is at or above ``iou_floor`` and the appearance cost is present (not
    ``NaN``). There the fused cost is the convex combination
    ``(1 - appearance_weight) * iou_cost + appearance_weight * appearance_cost``.
    Every other cell falls back to the plain ``iou_cost``; the gate never writes
    an unmatchable sentinel.

    Args:
        iou_cost: ``(T, N)`` IoU cost matrix (``1 - IoU``).
        appearance_cost: ``(T, N)`` appearance cost matrix, optionally holding
            ``NaN`` for tracks without gallery features.
        appearance_weight: Weight in ``[0, 1]`` given to the appearance term.
        iou_floor: Minimum IoU a pair must reach for appearance to be fused in.

    Returns:
        ``(T, N)`` float32 fused cost matrix.
    """
    if iou_cost.size == 0:
        return iou_cost.astype(np.float32, copy=False)
    weight = float(appearance_weight)
    blended = (1.0 - weight) * iou_cost + weight * appearance_cost
    iou = 1.0 - iou_cost
    use_appearance = (iou >= iou_floor) & ~np.isnan(appearance_cost)
    return np.where(use_appearance, blended, iou_cost).astype(np.float32)
