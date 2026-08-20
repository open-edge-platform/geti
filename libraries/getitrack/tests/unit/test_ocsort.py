# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Unit tests for the OC-SORT algorithm and its observation-centric helpers."""

from __future__ import annotations

import numpy as np
import pytest

from getitrack.algorithms import OCSortTracker
from getitrack.algorithms.configs.ocsort import OCSortConfig
from getitrack.algorithms.ocsort import _direction_cost, _speed_direction, _velocity_direction_batch
from getitrack.config import LifecycleConfig
from getitrack.core.base import BaseTracker
from getitrack.core.detection import Detections


def _dets(
    boxes: list[list[float]], scores: list[float], frame_id: int, class_ids: list[int] | None = None
) -> Detections:
    n = len(boxes)
    return Detections(
        bboxes=np.asarray(boxes, dtype=np.float32).reshape(n, 4),
        scores=np.asarray(scores, dtype=np.float32),
        class_ids=np.asarray(class_ids if class_ids is not None else [0] * n, dtype=np.int64),
        frame_id=frame_id,
    )


@pytest.fixture
def fast_confirm() -> OCSortConfig:
    return OCSortConfig(lifecycle=LifecycleConfig(min_hits=1, tentative_max_age=1, max_age=30))


class TestRegistry:
    def test_from_config_dispatches_to_ocsort(self):
        tracker = BaseTracker.from_config(OCSortConfig())
        assert isinstance(tracker, OCSortTracker)


class TestSingleObject:
    def test_id_persists_across_frames(self, fast_confirm):
        ocs = OCSortTracker(fast_confirm)
        ids = []
        for f in range(5):
            out = ocs.update(_dets([[10 + f * 5, 10, 50 + f * 5, 50]], [0.9], frame_id=f))
            ids.append(out.track_ids.tolist())
        assert ids == [[1], [1], [1], [1], [1]]

    def test_det_indices_point_at_input_rows(self, fast_confirm):
        ocs = OCSortTracker(fast_confirm)
        ocs.update(_dets([[0, 0, 10, 10]], [0.9], frame_id=0))
        # Two detections; the tracked one is the second row.
        out = ocs.update(_dets([[500, 500, 510, 510], [3, 0, 13, 10]], [0.9, 0.9], frame_id=1))
        # track 1 continues from row 1 (the near box); a new track spawns from row 0.
        assert out.det_indices is not None
        idx = {int(t): int(d) for t, d in zip(out.track_ids, out.det_indices, strict=True)}
        assert idx[1] == 1


class TestRecovery:
    def test_first_pass_recovers_track_near_predicted_trajectory(self, fast_confirm):
        # Object seen, gone for 3 frames, reappears on its trajectory: the
        # Kalman prediction still overlaps, so the first pass recovers the id.
        ocs = OCSortTracker(fast_confirm)
        seq: list[tuple[list[list[float]], list[float]]] = [
            ([[10, 10, 50, 50]], [0.9]),
            ([[16, 10, 56, 50]], [0.9]),
            ([], []),
            ([], []),
            ([], []),
        ]
        for f, (b, s) in enumerate(seq):
            ocs.update(_dets(b, s, frame_id=f))
        out = ocs.update(_dets([[34, 10, 74, 50]], [0.9], frame_id=len(seq)))
        assert out.track_ids.tolist() == [1]

    def test_ocr_recovers_track_that_stopped_during_occlusion(self, fast_confirm):
        # Object moving 10 px/frame stops and is occluded for 4 frames. The
        # Kalman prediction coasts ~50 px past the reappearance box (width 40),
        # so the first pass cannot match; OCR matches the last observation.
        ocs = OCSortTracker(fast_confirm)
        for f in range(4):
            ocs.update(_dets([[10 + 10 * f, 10, 50 + 10 * f, 50]], [0.9], frame_id=f))
        for f in range(4, 8):
            ocs.update(_dets([], [], frame_id=f))
        out = ocs.update(_dets([[40, 10, 80, 50]], [0.9], frame_id=8))
        assert out.track_ids.tolist() == [1]

    def test_use_byte_keeps_track_with_low_score_detection(self):
        cfg = OCSortConfig(use_byte=True, lifecycle=LifecycleConfig(min_hits=1, tentative_max_age=1))
        ocs = OCSortTracker(cfg)
        ocs.update(_dets([[10, 10, 50, 50]], [0.9], frame_id=0))
        # Score 0.35 is below det_threshold (0.6) but above score_threshold (0.1).
        out = ocs.update(_dets([[15, 10, 55, 50]], [0.35], frame_id=1))
        assert out.track_ids.tolist() == [1]

    def test_low_score_detection_ignored_without_use_byte(self):
        cfg = OCSortConfig(use_byte=False, lifecycle=LifecycleConfig(min_hits=1, tentative_max_age=1, max_age=30))
        ocs = OCSortTracker(cfg)
        ocs.update(_dets([[10, 10, 50, 50]], [0.9], frame_id=0))
        out = ocs.update(_dets([[15, 10, 55, 50]], [0.35], frame_id=1))
        # No high detection and BYTE off, so the track is not output this frame.
        assert out.track_ids.tolist() == []


class TestNewTrack:
    def test_detection_above_det_threshold_spawns(self):
        ocs = OCSortTracker(OCSortConfig(det_threshold=0.6, lifecycle=LifecycleConfig(min_hits=1)))
        out = ocs.update(_dets([[10, 10, 50, 50]], [0.7], frame_id=0))
        assert out.track_ids.tolist() == [1]

    def test_detection_below_det_threshold_does_not_spawn(self):
        ocs = OCSortTracker(OCSortConfig(det_threshold=0.6, lifecycle=LifecycleConfig(min_hits=1)))
        out = ocs.update(_dets([[10, 10, 50, 50]], [0.5], frame_id=0))
        assert len(out) == 0


class TestMultiObject:
    def test_class_only_matching_keeps_classes_separate(self):
        cfg = OCSortConfig(lifecycle=LifecycleConfig(min_hits=1, tentative_max_age=1), match_class_only=True)
        ocs = OCSortTracker(cfg)
        ocs.update(_dets([[0, 0, 20, 20]], [0.9], frame_id=0, class_ids=[0]))
        out = ocs.update(_dets([[0, 0, 20, 20]], [0.9], frame_id=1, class_ids=[1]))
        assert sorted(out.track_ids.tolist()) == [2]

    def test_two_objects_keep_distinct_ids(self, fast_confirm):
        ocs = OCSortTracker(fast_confirm)
        for f in range(4):
            out = ocs.update(_dets([[10 + f * 4, 10, 40 + f * 4, 40], [200, 200, 230, 230]], [0.9, 0.9], frame_id=f))
        assert sorted(out.track_ids.tolist()) == [1, 2]


class TestLifecycle:
    def test_track_ages_out_after_max_age(self):
        cfg = OCSortConfig(lifecycle=LifecycleConfig(min_hits=1, tentative_max_age=1, max_age=2))
        ocs = OCSortTracker(cfg)
        ocs.update(_dets([[10, 10, 50, 50]], [0.9], frame_id=0))
        for f in range(1, 5):
            ocs.update(_dets([], [], frame_id=f))
        out = ocs.update(_dets([], [], frame_id=5))
        assert out.track_ids.tolist() == []
        assert ocs._tracks == {}

    def test_reset_clears_state_and_ids_restart(self, fast_confirm):
        ocs = OCSortTracker(fast_confirm)
        ocs.update(_dets([[10, 10, 50, 50]], [0.9], frame_id=0))
        ocs.reset()
        assert ocs._tracks == {}
        assert ocs._obs == {}
        out = ocs.update(_dets([[10, 10, 50, 50]], [0.9], frame_id=0))
        assert out.track_ids.tolist() == [1]


class TestEmptyFrame:
    def test_empty_first_frame_returns_empty(self):
        ocs = OCSortTracker(OCSortConfig(lifecycle=LifecycleConfig(min_hits=1)))
        out = ocs.update(_dets([], [], frame_id=0))
        assert len(out) == 0
        assert out.det_indices is not None


class TestOCMHelpers:
    def test_speed_direction_is_unit_and_correct(self):
        # box1 at origin center, box2 shifted +10 in x -> direction (dy=0, dx=+1).
        box1 = np.array([0.0, 0.0, 10.0, 10.0])
        box2 = np.array([10.0, 0.0, 20.0, 10.0])
        dy, dx = _speed_direction(box1, box2)
        assert dy == pytest.approx(0.0, abs=1e-6)
        assert dx == pytest.approx(1.0, abs=1e-4)

    def test_velocity_direction_batch_shapes_and_values(self):
        dets = np.array([[10.0, 0.0, 20.0, 10.0], [0.0, 10.0, 10.0, 20.0]])  # right, up
        prev = np.array([[0.0, 0.0, 10.0, 10.0]])  # one track at origin
        dy, dx = _velocity_direction_batch(dets, prev)
        assert dy.shape == (1, 2)
        # det0 is to the right: dx=+1, dy=0. det1 is below-ish: dy=+1, dx=0.
        assert dx[0, 0] == pytest.approx(1.0, abs=1e-4)
        assert dy[0, 1] == pytest.approx(1.0, abs=1e-4)

    def test_direction_cost_rewards_aligned_penalises_opposed(self):
        # Track velocity points right (dy=0, dx=+1), prior obs at origin.
        prev = np.array([[0.0, 0.0, 10.0, 10.0]])
        velocities = np.array([[0.0, 1.0]])  # (dy, dx)
        valid = np.array([True])
        # det A to the right (aligned), det B to the left (opposed).
        dets = np.array([[100.0, 0.0, 110.0, 10.0], [-100.0, 0.0, -90.0, 10.0]])
        scores = np.array([1.0, 1.0])
        cost = _direction_cost(dets, prev, velocities, valid, scores, inertia=1.0)
        assert cost[0, 0] == pytest.approx(0.5, abs=1e-3)  # aligned -> reward
        assert cost[0, 1] == pytest.approx(-0.5, abs=1e-3)  # opposed -> penalty

    def test_direction_cost_masked_when_velocity_invalid(self):
        prev = np.array([[0.0, 0.0, 10.0, 10.0]])
        velocities = np.array([[0.0, 1.0]])
        valid = np.array([False])  # no established velocity yet
        dets = np.array([[100.0, 0.0, 110.0, 10.0]])
        scores = np.array([1.0])
        cost = _direction_cost(dets, prev, velocities, valid, scores, inertia=1.0)
        assert cost[0, 0] == 0.0


class TestMomentum:
    def test_ocm_prefers_direction_consistent_detection(self):
        # Track moving right; two candidates at equal IoU to the prediction,
        # one ahead (direction-consistent) and one behind (opposed). The OCM
        # term must select the aligned candidate.
        cfg = OCSortConfig(inertia=0.3, lifecycle=LifecycleConfig(min_hits=1, tentative_max_age=1, max_age=30))
        ocs = OCSortTracker(cfg)
        w, h = 100, 40
        for f in range(4):
            cx = 100 + f * 10
            ocs.update(_dets([[cx - w / 2, 0, cx + w / 2, h]], [0.9], frame_id=f))
        mean, _ = ocs._kalman_states[1]
        pred_cx = float(mean[0] + mean[4])  # next-frame predicted center x
        opposed = [pred_cx - 40 - w / 2, 0, pred_cx - 40 + w / 2, h]
        aligned = [pred_cx + 40 - w / 2, 0, pred_cx + 40 + w / 2, h]
        out = ocs.update(_dets([opposed, aligned], [0.9, 0.9], frame_id=4))
        assert out.det_indices is not None
        pairs = {int(t): int(d) for t, d in zip(out.track_ids, out.det_indices, strict=True)}
        assert pairs[1] == 1

    def test_momentum_penalty_does_not_veto_iou_valid_match(self):
        # A reversal detection overlaps the prediction (IoU ~0.49, valid) but
        # opposes the track direction. The momentum penalty may only reorder
        # candidates; the pair must still match on its valid IoU.
        cfg = OCSortConfig(inertia=0.8, lifecycle=LifecycleConfig(min_hits=1, tentative_max_age=1, max_age=30))
        ocs = OCSortTracker(cfg)
        w, h = 100, 40
        for f in range(4):
            cx = f * 4
            ocs.update(_dets([[cx - w / 2, 0, cx + w / 2, h]], [0.9], frame_id=f))
        out = ocs.update(_dets([[-20 - w / 2, 0, -20 + w / 2, h]], [0.9], frame_id=4))
        assert out.track_ids.tolist() == [1]


class TestObservationHistory:
    def test_previous_observation_returns_delta_t_frames_back(self, fast_confirm):
        ocs = OCSortTracker(fast_confirm)
        for f in range(5):
            ocs.update(_dets([[10 * f, 0, 10 * f + 40, 40]], [0.9], frame_id=f))
        age = ocs._tracks[1].age
        expected = ocs._obs[1].observations[age - ocs.config.delta_t]
        np.testing.assert_array_equal(ocs._previous_observation(1), expected)

    def test_observation_history_is_bounded(self, fast_confirm):
        ocs = OCSortTracker(fast_confirm)
        for f in range(20):
            ocs.update(_dets([[10 + f, 10, 50 + f, 50]], [0.9], frame_id=f))
        assert len(ocs._obs[1].observations) == ocs.config.delta_t + 1


class TestORU:
    def test_reupdate_recovers_forward_velocity_after_gap(self):
        # Constant rightward motion, a 3-frame gap, then re-acquisition on the
        # same line. After ORU the filter's x-velocity should still point forward
        # at roughly the true speed, not collapse toward zero.
        cfg = OCSortConfig(lifecycle=LifecycleConfig(min_hits=1, max_age=30))
        ocs = OCSortTracker(cfg)
        for f in range(4):
            ocs.update(_dets([[10 + f * 10, 10, 50 + f * 10, 50]], [0.9], frame_id=f))
        for f in range(4, 7):
            ocs.update(_dets([], [], frame_id=f))
        out = ocs.update(_dets([[80, 10, 120, 50]], [0.9], frame_id=7))
        assert out.track_ids.tolist() == [1]
        mean, _ = ocs._kalman_states[1]
        assert mean[4] > 3.0  # x-velocity recovered as clearly forward (true speed ~10 px/frame)
