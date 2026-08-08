# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Tests for the GIoU/DIoU/CIoU distance metrics and the config seam."""

from __future__ import annotations

import numpy as np
import pytest

from getitrack.algorithms import ByteTrackTracker
from getitrack.algorithms.configs.bytetrack import ByteTrackConfig
from getitrack.config import DistanceMetric, TrackerConfig
from getitrack.matching import (
    BaseDistanceMetric,
    CIoUDistance,
    DIoUDistance,
    GIoUDistance,
    IoUDistance,
)

# Metric instances under test; each is callable as ``metric(boxes_a, boxes_b)``.
IOU = IoUDistance()
GIOU = GIoUDistance()
DIOU = DIoUDistance()
CIOU = CIoUDistance()

# Reused box sets. All are 10x10 squares unless noted.
_BOX = np.array([[0.0, 0.0, 10.0, 10.0]], dtype=np.float32)
# Disjoint 10x10 square, centre 20px to the right (same aspect ratio).
_DISJOINT_SQUARE = np.array([[20.0, 0.0, 30.0, 10.0]], dtype=np.float32)
# Disjoint 10-wide, 30-tall box (different aspect ratio) to exercise CIoU's v.
_DISJOINT_TALL = np.array([[20.0, 0.0, 30.0, 30.0]], dtype=np.float32)
# Disjoint box with w/h = 1/sqrt(3) so arctan(w/h) = pi/6 exactly; paired with a
# square (arctan = pi/4) it makes CIoU's v == 1/36 analytically, independent of
# the implementation's arctan call.
_DISJOINT_RATIO = np.array([[20.0, 0.0, 30.0, 10.0 * np.sqrt(3.0)]], dtype=np.float32)
# Outer box with a smaller box fully nested inside it (off-centre, taller aspect).
_OUTER = np.array([[0.0, 0.0, 20.0, 20.0]], dtype=np.float32)
_INNER_NESTED = np.array([[2.0, 4.0, 12.0, 10.0]], dtype=np.float32)
# Partial overlap: two 10x10 squares offset by (6, 2).
_PARTIAL_A = np.array([[0.0, 0.0, 10.0, 10.0]], dtype=np.float32)
_PARTIAL_B = np.array([[6.0, 2.0, 16.0, 12.0]], dtype=np.float32)

_ALL_DISTANCES = (GIOU, DIOU, CIOU)


class TestIdenticalBoxes:
    @pytest.mark.parametrize("distance", _ALL_DISTANCES)
    def test_identical_boxes_have_zero_cost(self, distance):
        # IoU == GIoU == DIoU == CIoU == 1 for a box against itself -> cost 0.
        assert distance(_BOX, _BOX)[0, 0] == pytest.approx(0.0, abs=1e-6)


class TestDisjointSameAspect:
    """a=[0,0,10,10] vs b=[20,0,30,10]: no overlap, equal aspect ratios."""

    def test_giou_matches_hand_computation(self):
        assert GIOU(_BOX, _DISJOINT_SQUARE)[0, 0] == pytest.approx(4.0 / 3.0, abs=1e-5)

    def test_diou_matches_hand_computation(self):
        assert DIOU(_BOX, _DISJOINT_SQUARE)[0, 0] == pytest.approx(1.4, abs=1e-5)

    def test_ciou_equals_diou_when_aspect_ratios_match(self):
        ciou = CIOU(_BOX, _DISJOINT_SQUARE)[0, 0]
        diou = DIOU(_BOX, _DISJOINT_SQUARE)[0, 0]
        assert ciou == pytest.approx(diou, abs=1e-6)

    @pytest.mark.parametrize("distance", _ALL_DISTANCES)
    def test_extended_metrics_exceed_plain_iou_cost_when_disjoint(self, distance):
        iou_cost = IOU(_BOX, _DISJOINT_SQUARE)[0, 0]
        assert iou_cost == pytest.approx(1.0, abs=1e-6)
        assert distance(_BOX, _DISJOINT_SQUARE)[0, 0] > iou_cost


class TestDisjointDifferentAspect:
    """a=[0,0,10,10] (square) vs b=[20,0,30,30] (tall): CIoU's v is non-zero."""

    def test_diou_matches_hand_computation(self):
        # rho^2 = 20^2 + 10^2 = 500; c^2 = 30^2 + 30^2 = 1800.
        # DIoU = 0 - 500/1800 -> cost = 1 + 5/18.
        assert DIOU(_BOX, _DISJOINT_TALL)[0, 0] == pytest.approx(1.0 + 5.0 / 18.0, abs=1e-5)

    def test_ciou_matches_hand_computation(self):
        # v = (4/pi^2)(atan(10/30) - atan(10/10))^2; alpha = v/((1-IoU)+v).
        v = (4.0 / np.pi**2) * (np.arctan(1.0 / 3.0) - np.arctan(1.0)) ** 2
        alpha = v / (1.0 + v)  # IoU == 0 here.
        expected = 1.0 - (0.0 - 500.0 / 1800.0 - alpha * v)
        assert CIOU(_BOX, _DISJOINT_TALL)[0, 0] == pytest.approx(expected, abs=1e-5)

    def test_ciou_strictly_exceeds_diou_when_aspect_differs(self):
        # The aspect term only adds cost, so CIoU > DIoU here.
        assert CIOU(_BOX, _DISJOINT_TALL)[0, 0] > DIOU(_BOX, _DISJOINT_TALL)[0, 0]


class TestCIoUIndependentScalar:
    """Pin CIoU against a value derived without the impl's arctan expression.

    a=[0,0,10,10] (square, arctan(w/h)=pi/4) vs b=[20,0,30,10*sqrt(3)]
    (arctan(w/h)=pi/6). The aspect diff is exactly pi/12, so
    ``v = (4/pi^2)(pi/12)^2 = 1/36`` and ``alpha = v/(1+v) = 1/37`` in closed
    form. IoU=0; rho^2 = 500 - 50*sqrt(3); c^2 = 30^2 + (10*sqrt(3))^2 = 1200.
    CIoU = -(rho^2/c^2) - (1/37)(1/36); cost = 1 - CIoU.
    """

    def test_ciou_matches_closed_form(self):
        rho_sq = 500.0 - 50.0 * np.sqrt(3.0)
        expected = 1.0 + rho_sq / 1200.0 + (1.0 / 37.0) * (1.0 / 36.0)
        # Cross-check the literal so a future geometry edit can't drift silently.
        assert expected == pytest.approx(1.3452486, abs=1e-6)
        assert CIOU(_BOX, _DISJOINT_RATIO)[0, 0] == pytest.approx(expected, abs=1e-4)


class TestNestedBoxes:
    """Inner box fully inside outer: a=[0,0,20,20], b=[2,4,12,10].

    inter = area_b = 60; union = area_a = 400; IoU = 0.15. The enclosing box is
    the outer box, so area_C == union and GIoU == IoU. Centres are (10,10) and
    (7,7): rho^2 = 18, c^2 = 20^2 + 20^2 = 800.
    """

    def test_giou_equals_iou_when_one_box_contains_the_other(self):
        # area_C == union for a fully-nested pair, so the GIoU penalty is 0.
        giou = GIOU(_OUTER, _INNER_NESTED)[0, 0]
        iou = IOU(_OUTER, _INNER_NESTED)[0, 0]
        assert iou == pytest.approx(0.85, abs=1e-5)
        assert giou == pytest.approx(0.85, abs=1e-5)

    def test_diou_matches_hand_computation(self):
        # DIoU = 0.15 - 18/800 = 0.1275 -> cost = 0.8725.
        assert DIOU(_OUTER, _INNER_NESTED)[0, 0] == pytest.approx(0.8725, abs=1e-5)

    def test_ciou_exceeds_diou_when_nested_aspect_differs(self):
        # Outer is square, inner is 10x6, so the aspect term adds a little cost.
        assert CIOU(_OUTER, _INNER_NESTED)[0, 0] > DIOU(_OUTER, _INNER_NESTED)[0, 0]


class TestPartialOverlap:
    """Two 10x10 squares offset by (6, 2): a=[0,0,10,10], b=[6,2,16,12].

    inter = 4*8 = 32; union = 168; IoU = 32/168. Enclosing box = [0,0,16,12]:
    area_C = 192, c^2 = 16^2 + 12^2 = 400. Centres (5,5) and (11,7): rho^2 = 40.
    Both boxes share aspect ratio 1, so v = 0 and CIoU == DIoU.
    """

    def test_iou_matches_hand_computation(self):
        assert IOU(_PARTIAL_A, _PARTIAL_B)[0, 0] == pytest.approx(1.0 - 32.0 / 168.0, abs=1e-5)

    def test_giou_matches_hand_computation(self):
        # penalty = (192 - 168)/192 = 0.125; GIoU = 32/168 - 0.125.
        expected = 1.0 - (32.0 / 168.0 - 0.125)
        assert GIOU(_PARTIAL_A, _PARTIAL_B)[0, 0] == pytest.approx(expected, abs=1e-5)

    def test_diou_matches_hand_computation(self):
        # DIoU = 32/168 - 40/400 = 32/168 - 0.1.
        expected = 1.0 - (32.0 / 168.0 - 0.1)
        assert DIOU(_PARTIAL_A, _PARTIAL_B)[0, 0] == pytest.approx(expected, abs=1e-5)


class TestShapeAndValidation:
    @pytest.mark.parametrize("distance", _ALL_DISTANCES)
    def test_matrix_shape_and_alignment(self, distance):
        # Distinct boxes so (M, N) alignment is checked against known cells: an
        # identical pair (cost 0) sits at an off-diagonal position, and each far
        # disjoint pair has cost > 1 for every extended metric.
        boxes_a = np.array([[0, 0, 10, 10], [20, 20, 30, 30]], dtype=np.float32)
        boxes_b = np.array([[100, 0, 110, 10], [0, 0, 10, 10], [20, 20, 30, 30]], dtype=np.float32)
        out = distance(boxes_a, boxes_b)
        assert out.shape == (2, 3)
        assert out.dtype == np.float32
        # Identical pairs land off the diagonal at (0, 1) and (1, 2).
        assert out[0, 1] == pytest.approx(0.0, abs=1e-6)
        assert out[1, 2] == pytest.approx(0.0, abs=1e-6)
        # Disjoint pairs exceed the IoU saturation cost of 1.0.
        assert out[0, 0] > 1.0
        assert out[1, 0] > 1.0

    @pytest.mark.parametrize("distance", _ALL_DISTANCES)
    def test_empty_inputs_return_empty_matrix(self, distance):
        empty = np.empty((0, 4), dtype=np.float32)
        assert distance(empty, _BOX).shape == (0, 1)
        assert distance(_BOX, empty).shape == (1, 0)

    @pytest.mark.parametrize("distance", _ALL_DISTANCES)
    def test_bad_shape_raises(self, distance):
        bad = np.zeros((3, 5), dtype=np.float32)
        with pytest.raises(ValueError, match="boxes_a must have shape"):
            distance(bad, _BOX)

    @pytest.mark.parametrize("distance", _ALL_DISTANCES)
    def test_non_finite_raises(self, distance):
        nan_box = np.array([[0.0, 0.0, np.nan, 10.0]], dtype=np.float32)
        with pytest.raises(ValueError, match="boxes_a contains non-finite"):
            distance(nan_box, _BOX)
        with pytest.raises(ValueError, match="boxes_b contains non-finite"):
            distance(_BOX, nan_box)


class TestDispatch:
    def test_config_default_metric_is_iou(self):
        assert TrackerConfig.model_fields["distance_metric"].default == DistanceMetric.IOU
        assert ByteTrackConfig().distance_metric == DistanceMetric.IOU

    @pytest.mark.parametrize(
        ("metric", "expected"),
        [
            (DistanceMetric.IOU, IoUDistance),
            (DistanceMetric.GIOU, GIoUDistance),
            (DistanceMetric.DIOU, DIoUDistance),
            (DistanceMetric.CIOU, CIoUDistance),
        ],
    )
    def test_each_metric_dispatches_to_its_function(self, metric, expected):
        assert type(BaseDistanceMetric.from_metric(metric)) is expected


class TestByteTrackWiring:
    def test_default_tracker_uses_iou_distance(self):
        tracker = ByteTrackTracker(ByteTrackConfig())
        assert isinstance(tracker._distance, IoUDistance)

    @pytest.mark.parametrize(
        ("metric", "expected"),
        [
            (DistanceMetric.GIOU, GIoUDistance),
            (DistanceMetric.DIOU, DIoUDistance),
            (DistanceMetric.CIOU, CIoUDistance),
        ],
    )
    def test_selected_metric_is_wired_into_association(self, metric, expected):
        tracker = ByteTrackTracker(ByteTrackConfig(distance_metric=metric))
        assert isinstance(tracker._distance, expected)
