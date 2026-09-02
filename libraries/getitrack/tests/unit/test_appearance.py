# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Tests for the appearance cost helpers (cosine distance + IoU-gated fusion)."""

import numpy as np
import pytest

from getitrack.matching.appearance import (
    cosine_distance,
    fuse_appearance_cost,
    l2_normalize,
)


class TestCosineDistance:
    def test_identical_features_are_near_zero(self):
        a = np.array([[1.0, 2.0, 3.0]], dtype=np.float32)
        dist = cosine_distance(a, a.copy())
        assert dist[0, 0] == pytest.approx(0.0, abs=1e-5)

    def test_orthogonal_features_are_near_one(self):
        a = np.array([[1.0, 0.0]], dtype=np.float32)
        b = np.array([[0.0, 1.0]], dtype=np.float32)
        assert cosine_distance(a, b)[0, 0] == pytest.approx(1.0, abs=1e-5)

    def test_opposite_features_are_near_two(self):
        a = np.array([[1.0, 0.0]], dtype=np.float32)
        b = np.array([[-1.0, 0.0]], dtype=np.float32)
        assert cosine_distance(a, b)[0, 0] == pytest.approx(2.0, abs=1e-5)

    def test_unnormalised_input_still_yields_cosine(self):
        # Scaling a vector must not change its cosine distance.
        a = np.array([[3.0, 4.0]], dtype=np.float32)
        b = np.array([[6.0, 8.0]], dtype=np.float32)
        assert cosine_distance(a, b)[0, 0] == pytest.approx(0.0, abs=1e-5)

    def test_shape_and_dtype(self):
        a = np.random.default_rng(0).random((4, 8)).astype(np.float32)
        b = np.random.default_rng(1).random((3, 8)).astype(np.float32)
        dist = cosine_distance(a, b)
        assert dist.shape == (4, 3)
        assert dist.dtype == np.float32

    def test_empty_inputs(self):
        empty = np.empty((0, 8), dtype=np.float32)
        boxes = np.zeros((2, 8), dtype=np.float32)
        assert cosine_distance(empty, boxes).shape == (0, 2)
        assert cosine_distance(boxes, empty).shape == (2, 0)


class TestL2Normalize:
    def test_rows_become_unit_norm(self):
        x = np.array([[3.0, 4.0], [0.0, 2.0]], dtype=np.float32)
        norms = np.linalg.norm(l2_normalize(x), axis=1)
        assert np.allclose(norms, 1.0, atol=1e-5)

    def test_zero_row_stays_zero(self):
        x = np.zeros((1, 4), dtype=np.float32)
        assert np.allclose(l2_normalize(x), 0.0)


class TestFuseAppearanceCost:
    def test_convex_blend(self):
        iou_cost = np.array([[0.2]], dtype=np.float32)
        app_cost = np.array([[0.8]], dtype=np.float32)
        fused = fuse_appearance_cost(iou_cost, app_cost, appearance_weight=0.25, iou_floor=0.0)
        # 0.75 * 0.2 + 0.25 * 0.8 = 0.35
        assert fused[0, 0] == pytest.approx(0.35, abs=1e-6)

    def test_below_floor_pairs_fall_back_to_plain_iou(self):
        # IoU = 1 - iou_cost. Row 0 overlaps (IoU 0.8 >= floor), row 1 barely
        # (IoU 0.1 < floor). Appearance must never make a below-floor pair
        # unmatchable: it falls back to the plain iou_cost, not a sentinel.
        iou_cost = np.array([[0.2], [0.9]], dtype=np.float32)
        app_cost = np.array([[0.0], [0.0]], dtype=np.float32)
        fused = fuse_appearance_cost(iou_cost, app_cost, appearance_weight=0.9, iou_floor=0.5)
        # Above the floor, appearance lowers the cost.
        assert fused[0, 0] < iou_cost[0, 0]
        # Below the floor, appearance is dropped: the pair keeps its IoU cost and
        # stays exactly as matchable as it is under IoU alone (not gated out).
        assert fused[1, 0] == pytest.approx(iou_cost[1, 0])

    def test_never_stricter_than_iou_for_below_floor_reappearance(self):
        # A same-identity reappearance at moderate overlap (IoU 0.36, below a 0.5
        # floor) with a perfect appearance match keeps its plain IoU cost, so it
        # remains matchable exactly where the IoU-only baseline would match it.
        iou_cost = np.array([[0.64]], dtype=np.float32)
        app_cost = np.array([[0.0]], dtype=np.float32)
        fused = fuse_appearance_cost(iou_cost, app_cost, appearance_weight=0.9, iou_floor=0.5)
        assert fused[0, 0] == pytest.approx(0.64)

    def test_disagreeing_appearance_raises_cost_above_floor(self):
        # A high-overlap pair whose appearance disagrees is penalised, letting
        # appearance discriminate competing matches.
        iou_cost = np.array([[0.1]], dtype=np.float32)
        app_cost = np.array([[1.0]], dtype=np.float32)
        fused = fuse_appearance_cost(iou_cost, app_cost, appearance_weight=0.5, iou_floor=0.5)
        assert fused[0, 0] > iou_cost[0, 0]

    def test_nan_appearance_falls_back_to_iou(self):
        iou_cost = np.array([[0.3]], dtype=np.float32)
        app_cost = np.array([[np.nan]], dtype=np.float32)
        fused = fuse_appearance_cost(iou_cost, app_cost, appearance_weight=0.5, iou_floor=0.0)
        assert fused[0, 0] == pytest.approx(0.3, abs=1e-6)

    def test_empty_matrix_passthrough(self):
        empty = np.empty((0, 0), dtype=np.float32)
        fused = fuse_appearance_cost(empty, empty, appearance_weight=0.5, iou_floor=0.5)
        assert fused.shape == (0, 0)
