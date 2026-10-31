# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Behavioral tests for greedy IOU tracking and its streaming lifecycle."""

from __future__ import annotations

import numpy as np
import pytest

from getitrack.algorithms import IOUTracker
from getitrack.algorithms.configs.iou import IOUConfig
from getitrack.config import LifecycleConfig
from getitrack.core.detection import Detections
from getitrack.core.track import TrackState


def _dets(boxes, scores, frame_id=0, class_ids=None) -> Detections:
    return Detections(
        bboxes=np.asarray(boxes, dtype=np.float32).reshape(-1, 4),
        scores=np.asarray(scores, dtype=np.float32),
        class_ids=np.asarray(class_ids if class_ids is not None else [0] * len(boxes), dtype=np.int64),
        frame_id=frame_id,
    )


@pytest.fixture
def tracker():
    return IOUTracker(IOUConfig(lifecycle=LifecycleConfig(min_hits=1)))


def test_ids_and_observed_boxes_persist(tracker):
    for frame in range(5):
        detections = _dets([[frame, 0, 10 + frame, 10], [50, 50, 60, 60]], [0.9, 0.8], frame)
        out = tracker.update(detections)
        assert out.track_ids.tolist() == [1, 2]
        np.testing.assert_array_equal(out.bboxes, detections.bboxes)
        assert out.det_indices.tolist() == [0, 1]
    assert tracker.tracks[0].hits == 5


def test_requires_length_and_peak_score_without_first_frame_bypass():
    tracker = IOUTracker(IOUConfig(lifecycle=LifecycleConfig(min_hits=3), high_score_threshold=0.8))
    for frame, score in enumerate([0.2, 0.9, 0.2, 0.2]):
        out = tracker.update(_dets([[0, 0, 10, 10]], [score], frame))
        assert out.track_ids.tolist() == ([] if frame < 2 else [1])
        assert len(tracker.tracked_objects) == len(out)
        if frame >= 2:
            assert out.scores[0] == pytest.approx(0.2)


def test_length_alone_does_not_confirm():
    tracker = IOUTracker(IOUConfig(lifecycle=LifecycleConfig(min_hits=2)))
    for frame in range(4):
        assert len(tracker.update(_dets([[0, 0, 10, 10]], [0.2], frame))) == 0
        assert tracker.tracks[0].state == TrackState.TENTATIVE
    assert tracker.update(_dets([[0, 0, 10, 10]], [0.5], 4)).track_ids.tolist() == [1]


@pytest.mark.parametrize("min_hits", [1, 3])
def test_first_miss_removes_active_and_tentative_tracks(min_hits):
    tracker = IOUTracker(IOUConfig(lifecycle=LifecycleConfig(min_hits=min_hits, max_age=30, tentative_max_age=10)))
    tracker.update(_dets([[0, 0, 10, 10]], [0.9]))
    out = tracker.update(_dets([], [], 1))
    assert len(out) == 0
    assert out.frame_id == 1
    assert tracker.tracks == []
    assert tracker._max_scores == {}
    assert len(tracker.tracked_objects) == 0
    tracker.update(_dets([[0, 0, 10, 10]], [0.9], 2))
    assert tracker.tracks[0].track_id == 2


def test_low_score_observation_ends_track(tracker):
    tracker.update(_dets([[0, 0, 10, 10]], [0.9]))
    assert len(tracker.update(_dets([[0, 0, 10, 10]], [0.05], 1))) == 0
    assert tracker.tracks == []


def test_inclusive_score_and_iou_boundaries():
    tracker = IOUTracker(
        IOUConfig(score_threshold=0.5, high_score_threshold=0.5, lifecycle=LifecycleConfig(min_hits=1))
    )
    assert tracker.update(_dets([[0, 0, 10, 10]], [0.5])).track_ids.tolist() == [1]
    # Intersection 50 / union 100 is exactly the 0.5 IoU threshold.
    assert tracker.update(_dets([[0, 0, 5, 10]], [0.5], 1)).track_ids.tolist() == [1]
    assert tracker.update(_dets([[100, 0, 110, 10]], [0.5], 2)).track_ids.tolist() == [2]


def test_greedy_track_order_differs_from_global_assignment(tracker):
    tracker.update(_dets([[0, 0, 10, 10], [2, 0, 12, 10]], [0.9, 0.9]))
    # Track 1 takes its best match, even though reserving it for track 2
    # would allow both old tracks to survive a global assignment.
    out = tracker.update(_dets([[1, 0, 11, 10], [-3, 0, 7, 10]], [0.9, 0.9], 1))
    assert out.track_ids.tolist() == [1, 3]
    assert out.det_indices.tolist() == [0, 1]


def test_ties_choose_first_detection_and_never_reuse_it(tracker):
    tracker.update(_dets([[0, 0, 10, 10], [0, 0, 10, 10]], [0.9, 0.9]))
    out = tracker.update(_dets([[0, 0, 10, 10], [0, 0, 10, 10]], [0.8, 0.7], 1))
    assert out.track_ids.tolist() == [1, 2]
    assert out.det_indices.tolist() == [0, 1]
    out = tracker.update(_dets([[0, 0, 10, 10]], [0.9], 2))
    assert out.track_ids.tolist() == [1]


@pytest.mark.parametrize(("match_class_only", "expected_id"), [(True, 2), (False, 1)])
def test_class_matching_even_at_zero_iou_threshold(match_class_only, expected_id):
    tracker = IOUTracker(
        IOUConfig(iou_threshold=0, match_class_only=match_class_only, lifecycle=LifecycleConfig(min_hits=1))
    )
    tracker.update(_dets([[0, 0, 10, 10]], [0.9], class_ids=[0]))
    out = tracker.update(_dets([[0, 0, 10, 10]], [0.9], 1, class_ids=[1]))
    assert out.track_ids.tolist() == [expected_id]


def test_class_and_score_filter_indices_and_accessors():
    tracker = IOUTracker(IOUConfig(class_filter=[2], lifecycle=LifecycleConfig(min_hits=1)))
    for frame in range(2):
        out = tracker.update(_dets([[0, 0, 10, 10]] * 3, [0.9, 0.01, 0.9], frame, [0, 2, 2]))
        assert out.det_indices is not None
        assert out.det_indices.tolist() == [2]
        snapshot = tracker.tracked_objects
        assert snapshot.det_indices is not None
        assert snapshot.det_indices.tolist() == [2]
    snapshot = tracker.tracks
    snapshot[0].bbox[:] = 0
    assert tracker.tracks[0].bbox.tolist() == [0, 0, 10, 10]


def test_inputs_and_outputs_do_not_mutate_tracker(tracker):
    for frame in range(2):
        detections = _dets([[0, 0, 10, 10]], [0.9], frame)
        out = tracker.update(detections)
        detections.bboxes[:] = 100
        out.bboxes[:] = 200
        assert tracker.tracks[0].bbox.tolist() == [0, 0, 10, 10]


def test_reset_clears_peak_score_ids_and_accessors(tracker):
    assert tracker.tracks == []
    assert len(tracker.tracked_objects) == 0
    tracker.update(_dets([[0, 0, 10, 10]], [0.9]))
    tracker.reset()
    assert tracker.tracks == []
    assert tracker._max_scores == {}
    assert len(tracker.tracked_objects) == 0
    assert len(tracker.update(_dets([[0, 0, 10, 10]], [0.2]))) == 0
    assert tracker.tracks[0].track_id == 1


def test_empty_output_contract(tracker):
    out = tracker.update(_dets([], [], 7))
    assert out.frame_id == 7
    assert out.bboxes.shape == (0, 4)
    assert out.bboxes.dtype == np.float32
    assert out.track_ids.dtype == np.int64
    assert out.track_states.dtype == np.int8
    assert out.det_indices.shape == (0,)
    assert out.det_indices.dtype == np.int64
