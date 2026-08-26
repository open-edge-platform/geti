# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Unit tests for the SORT algorithm."""

from __future__ import annotations

import numpy as np
import pytest

from getitrack.algorithms import SortTracker
from getitrack.algorithms.configs.sort import SortConfig
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
def fast_confirm() -> SortConfig:
    return SortConfig(lifecycle=LifecycleConfig(min_hits=1, tentative_max_age=1, max_age=30))


class TestRegistry:
    def test_from_config_dispatches_to_sort(self):
        tracker = BaseTracker.from_config(SortConfig())
        assert isinstance(tracker, SortTracker)


class TestSingleObject:
    def test_id_persists_across_frames(self, fast_confirm):
        sort = SortTracker(fast_confirm)
        ids = []
        for f in range(5):
            out = sort.update(_dets([[10 + f * 5, 10, 50 + f * 5, 50]], [0.9], frame_id=f))
            ids.append(out.track_ids.tolist())
        assert ids == [[1], [1], [1], [1], [1]]

    def test_det_indices_point_at_input_rows(self, fast_confirm):
        sort = SortTracker(fast_confirm)
        sort.update(_dets([[0, 0, 10, 10]], [0.9], frame_id=0))
        # Row 0 falls below the score floor, so the tracked box is input row 1.
        out = sort.update(_dets([[500, 500, 510, 510], [3, 0, 13, 10]], [0.05, 0.9], frame_id=1))
        assert out.det_indices is not None
        idx = {int(t): int(d) for t, d in zip(out.track_ids, out.det_indices, strict=True)}
        assert idx[1] == 1


class TestAccessors:
    def test_tracks_and_tracked_objects_after_update(self, fast_confirm):
        sort = SortTracker(fast_confirm)
        for f in range(3):
            sort.update(_dets([[10, 10, 50, 50]], [0.9], frame_id=f))
        assert [t.track_id for t in sort.tracks] == [1]
        to = sort.tracked_objects
        assert to.track_ids.tolist() == [1]
        assert to.det_indices is not None

    def test_tracked_objects_before_any_frame_is_empty(self):
        sort = SortTracker(SortConfig())
        to = sort.tracked_objects
        assert len(to) == 0
        assert to.det_indices is not None
        assert sort.tracks == []


class TestScoreGate:
    def test_detection_at_or_below_score_threshold_is_dropped(self):
        cfg = SortConfig(score_threshold=0.5, lifecycle=LifecycleConfig(min_hits=1))
        sort = SortTracker(cfg)
        out = sort.update(_dets([[10, 10, 50, 50], [100, 100, 140, 140]], [0.5, 0.4], frame_id=0))
        assert len(out) == 0

    def test_no_low_score_recovery(self):
        # SORT has no second-stage association: a low-score detection cannot
        # keep a track observed, unlike ByteTrack.
        cfg = SortConfig(score_threshold=0.5, lifecycle=LifecycleConfig(min_hits=1, max_age=30))
        sort = SortTracker(cfg)
        sort.update(_dets([[10, 10, 50, 50]], [0.9], frame_id=0))
        out = sort.update(_dets([[12, 10, 52, 50]], [0.3], frame_id=1))
        assert out.track_ids.tolist() == []


class TestMultiObject:
    def test_two_objects_keep_distinct_ids(self, fast_confirm):
        sort = SortTracker(fast_confirm)
        for f in range(4):
            out = sort.update(_dets([[10 + f * 4, 10, 40 + f * 4, 40], [200, 200, 230, 230]], [0.9, 0.9], frame_id=f))
        assert sorted(out.track_ids.tolist()) == [1, 2]

    def test_class_only_matching_keeps_classes_separate(self):
        cfg = SortConfig(lifecycle=LifecycleConfig(min_hits=1, tentative_max_age=1), match_class_only=True)
        sort = SortTracker(cfg)
        sort.update(_dets([[0, 0, 20, 20]], [0.9], frame_id=0, class_ids=[0]))
        out = sort.update(_dets([[0, 0, 20, 20]], [0.9], frame_id=1, class_ids=[1]))
        assert out.track_ids.tolist() == [2]

    def test_iou_threshold_gates_association(self, fast_confirm):
        sort = SortTracker(fast_confirm)
        sort.update(_dets([[0, 0, 10, 10]], [0.9], frame_id=0))
        # A far-away detection overlaps the prediction with IoU 0, so it spawns
        # a new track instead of continuing track 1.
        out = sort.update(_dets([[100, 100, 110, 110]], [0.9], frame_id=1))
        assert out.track_ids.tolist() == [2]

    def test_cross_class_match_allowed_without_match_class_only(self):
        cfg = SortConfig(lifecycle=LifecycleConfig(min_hits=1, tentative_max_age=1), match_class_only=False)
        sort = SortTracker(cfg)
        sort.update(_dets([[0, 0, 20, 20]], [0.9], frame_id=0, class_ids=[0]))
        out = sort.update(_dets([[0, 0, 20, 20]], [0.9], frame_id=1, class_ids=[1]))
        assert out.track_ids.tolist() == [1]

    def test_class_mask_holds_at_zero_iou_threshold(self):
        # iou_threshold=0 accepts any assignment cost, so only the class mask
        # can reject this same-position, different-class pair.
        cfg = SortConfig(
            iou_threshold=0.0, lifecycle=LifecycleConfig(min_hits=1, tentative_max_age=1), match_class_only=True
        )
        sort = SortTracker(cfg)
        sort.update(_dets([[0, 0, 20, 20]], [0.9], frame_id=0, class_ids=[0]))
        out = sort.update(_dets([[0, 0, 20, 20]], [0.9], frame_id=1, class_ids=[1]))
        assert out.track_ids.tolist() == [2]


class TestCoasting:
    def test_lost_track_reacquired_from_prediction(self, fast_confirm):
        # Constant motion, a 2-frame gap, then a detection on the trajectory:
        # the Kalman prediction carries the box forward and the id survives.
        sort = SortTracker(fast_confirm)
        for f in range(3):
            sort.update(_dets([[10 + f * 10, 10, 50 + f * 10, 50]], [0.9], frame_id=f))
        for f in range(3, 5):
            out = sort.update(_dets([], [], frame_id=f))
            assert out.track_ids.tolist() == []  # LOST tracks are not emitted
        out = sort.update(_dets([[60, 10, 100, 50]], [0.9], frame_id=5))
        assert out.track_ids.tolist() == [1]


class TestLifecycle:
    def test_mid_sequence_spawn_confirms_after_min_hits(self):
        cfg = SortConfig(lifecycle=LifecycleConfig(min_hits=2, tentative_max_age=1, max_age=30))
        sort = SortTracker(cfg)
        sort.update(_dets([[0, 0, 20, 20]], [0.9], frame_id=0))
        # New object appears mid-sequence: TENTATIVE on its first frame.
        out = sort.update(_dets([[0, 0, 20, 20], [200, 200, 240, 240]], [0.9, 0.9], frame_id=1))
        assert sorted(out.track_ids.tolist()) == [1]
        out = sort.update(_dets([[0, 0, 20, 20], [202, 200, 242, 240]], [0.9, 0.9], frame_id=2))
        assert sorted(out.track_ids.tolist()) == [1, 2]

    def test_track_ages_out_after_max_age(self):
        cfg = SortConfig(lifecycle=LifecycleConfig(min_hits=1, tentative_max_age=1, max_age=2))
        sort = SortTracker(cfg)
        sort.update(_dets([[10, 10, 50, 50]], [0.9], frame_id=0))
        for f in range(1, 5):
            sort.update(_dets([], [], frame_id=f))
        out = sort.update(_dets([], [], frame_id=5))
        assert out.track_ids.tolist() == []
        assert sort._tracks == {}
        assert sort._kalman_states == {}

    def test_reset_clears_state_and_ids_restart(self, fast_confirm):
        sort = SortTracker(fast_confirm)
        sort.update(_dets([[10, 10, 50, 50]], [0.9], frame_id=0))
        sort.reset()
        assert sort._tracks == {}
        assert sort._kalman_states == {}
        out = sort.update(_dets([[10, 10, 50, 50]], [0.9], frame_id=0))
        assert out.track_ids.tolist() == [1]


class TestEmptyFrame:
    def test_empty_first_frame_returns_empty(self):
        sort = SortTracker(SortConfig(lifecycle=LifecycleConfig(min_hits=1)))
        out = sort.update(_dets([], [], frame_id=0))
        assert len(out) == 0
        assert out.det_indices is not None
