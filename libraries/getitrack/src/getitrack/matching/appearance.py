# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Appearance (ReID) cost computation and IoU-gated fusion.

These helpers are tracker-agnostic: they operate on plain numpy feature
matrices and cost matrices so any appearance-aware tracker (BoT-SORT, Deep
OC-SORT, StrongSORT) can reuse them.

Features are assumed L2-normalised row vectors; `cosine_distance` renormalises
defensively, so an unnormalised input still yields a valid cosine distance.
`fuse_appearance_cost` blends an IoU cost with an appearance cost and gates the
result by an IoU floor, so appearance can never rescue a pair whose boxes do
not overlap enough.
"""

from __future__ import annotations

import numpy as np

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
    a = l2_normalize(features_a)
    b = l2_normalize(features_b)
    similarity = a @ b.T
    return np.clip(1.0 - similarity, 0.0, 2.0).astype(np.float32)


def fuse_appearance_cost(
    iou_cost: np.ndarray,
    appearance_cost: np.ndarray,
    *,
    appearance_weight: float,
    iou_floor: float,
) -> np.ndarray:
    """Blend an IoU cost with an appearance cost, gated by IoU proximity.

    The appearance term is applied only where it is trustworthy: the pair's IoU
    (``1 - iou_cost``) is at or above ``iou_floor`` **and** the appearance cost
    is present (not ``NaN``). There the fused cost is the convex combination
    ``(1 - appearance_weight) * iou_cost + appearance_weight * appearance_cost``,
    which lowers the cost when appearance agrees and raises it when appearance
    disagrees, letting appearance disambiguate competing matches.

    Everywhere else, the cell falls back to the **plain** ``iou_cost``. The gate
    only ever *removes the appearance contribution*; it never writes an
    unmatchable sentinel. This preserves a key invariant for every appearance
    tracker built on this layer (BoT-SORT, Deep OC-SORT, StrongSORT): appearance
    can only help. A pair that IoU alone would match is never made unmatchable by
    appearance, so an appearance tracker is never stricter on geometry than its
    IoU-only baseline (e.g. a same-identity track reappearing at moderate overlap
    below the floor is still recovered on IoU).

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
