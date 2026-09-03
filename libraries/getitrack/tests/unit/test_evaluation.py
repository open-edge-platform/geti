# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Tests for getitrack.evaluation."""

import numpy as np
import pytest

from getitrack.evaluation import MotFrame, evaluate_mot, iou_distance_matrix, load_mot


def _stationary_gt(n_frames: int) -> dict[int, MotFrame]:
    """Two well-separated stationary objects (ids 1 and 2) over n_frames."""
    boxes = np.array([[10.0, 10.0, 20.0, 20.0], [80.0, 80.0, 20.0, 20.0]], dtype=np.float64)
    ids = np.array([1, 2], dtype=np.int64)
    return {frame: MotFrame(ids=ids.copy(), boxes=boxes.copy()) for frame in range(1, n_frames + 1)}


class TestIouDistanceMatrix:
    def test_identical_boxes_zero_distance(self):
        boxes = np.array([[0.0, 0.0, 10.0, 10.0]])
        dist = iou_distance_matrix(boxes, boxes)
        assert dist.shape == (1, 1)
        assert dist[0, 0] == pytest.approx(0.0)

    def test_disjoint_boxes_are_nan(self):
        a = np.array([[0.0, 0.0, 10.0, 10.0]])
        b = np.array([[100.0, 100.0, 10.0, 10.0]])
        dist = iou_distance_matrix(a, b, max_iou_distance=0.5)
        assert np.isnan(dist[0, 0])

    def test_half_overlap_distance(self):
        # Two 10x10 boxes overlapping in a 10x5 region: IoU = 50 / 150 = 1/3.
        a = np.array([[0.0, 0.0, 10.0, 10.0]])
        b = np.array([[0.0, 5.0, 10.0, 10.0]])
        dist = iou_distance_matrix(a, b, max_iou_distance=1.0)
        assert dist[0, 0] == pytest.approx(1.0 - 1.0 / 3.0)

    def test_empty_inputs(self):
        empty = np.empty((0, 4))
        assert iou_distance_matrix(empty, empty).shape == (0, 0)
        assert iou_distance_matrix(np.array([[0.0, 0.0, 1.0, 1.0]]), empty).shape == (1, 0)


class TestEvaluateMot:
    def test_perfect_tracking(self):
        gt = _stationary_gt(6)
        metrics = evaluate_mot(gt, gt)
        assert metrics.mota == pytest.approx(1.0)
        assert metrics.idf1 == pytest.approx(1.0)
        assert metrics.num_switches == 0
        assert metrics.num_false_positives == 0
        assert metrics.num_misses == 0
        assert metrics.mostly_tracked == 2
        assert metrics.mostly_lost == 0

    def test_single_id_switch(self):
        # One ground-truth object across 6 frames; the hypothesis id flips from
        # 1 to 2 at frame 4, producing exactly one identity switch and no
        # misses or false positives. MOTA = 1 - switches / gt = 1 - 1/6.
        box = np.array([[10.0, 10.0, 20.0, 20.0]], dtype=np.float64)
        gt = {frame: MotFrame(ids=np.array([1]), boxes=box.copy()) for frame in range(1, 7)}
        pred = {frame: MotFrame(ids=np.array([1 if frame < 4 else 2]), boxes=box.copy()) for frame in range(1, 7)}
        metrics = evaluate_mot(gt, pred)
        assert metrics.num_switches == 1
        assert metrics.num_false_positives == 0
        assert metrics.num_misses == 0
        assert metrics.mota == pytest.approx(5.0 / 6.0)
        assert metrics.idf1 < 1.0

    def test_missed_detection_lowers_mota(self):
        gt = _stationary_gt(4)
        pred = {frame: gt[frame] for frame in (1, 2, 3)}  # frame 4 fully missed.
        metrics = evaluate_mot(gt, pred)
        # 2 misses out of 8 ground-truth boxes.
        assert metrics.num_misses == 2
        assert metrics.mota == pytest.approx(1.0 - 2.0 / 8.0)

    def test_iou_threshold_changes_matching(self):
        # One GT box and one pred box overlapping with IoU = 1/3 (~0.333).
        gt = {1: MotFrame(ids=np.array([1]), boxes=np.array([[0.0, 0.0, 10.0, 10.0]]))}
        pred = {1: MotFrame(ids=np.array([1]), boxes=np.array([[0.0, 5.0, 10.0, 10.0]]))}

        loose = evaluate_mot(gt, pred, iou_threshold=0.3)
        assert loose.num_matches == 1
        assert loose.num_misses == 0
        assert loose.num_false_positives == 0
        assert loose.motp == pytest.approx(1.0 - 1.0 / 3.0)

        strict = evaluate_mot(gt, pred, iou_threshold=0.7)
        assert strict.num_matches == 0
        assert strict.num_misses == 1
        assert strict.num_false_positives == 1

    def test_zero_matches_report_motp_none(self):
        # Disjoint boxes: nothing can match, so MOTP is undefined -> None.
        gt = {1: MotFrame(ids=np.array([1]), boxes=np.array([[0.0, 0.0, 10.0, 10.0]]))}
        pred = {1: MotFrame(ids=np.array([2]), boxes=np.array([[100.0, 100.0, 10.0, 10.0]]))}
        metrics = evaluate_mot(gt, pred)
        assert metrics.num_matches == 0
        assert metrics.motp is None
        assert metrics.as_dict()["motp"] is None
        # Count fields stay coerced to 0, not None.
        assert metrics.num_switches == 0
        assert metrics.num_misses == 1
        assert metrics.num_false_positives == 1


class TestLoadMot:
    def test_round_trip(self, tmp_path):
        path = tmp_path / "gt.txt"
        path.write_text("1,1,10,10,20,20,1,0,1\n1,2,80,80,20,20,1,0,1\n2,1,12,10,20,20,1,0,1\n")
        frames = load_mot(path)
        assert set(frames) == {1, 2}
        assert frames[1].ids.tolist() == [1, 2]
        assert frames[1].boxes.shape == (2, 4)
        np.testing.assert_allclose(frames[1].boxes[0], [10.0, 10.0, 20.0, 20.0])

    def test_short_columns_raise(self, tmp_path):
        path = tmp_path / "bad.txt"
        path.write_text("1,1,10\n")
        with pytest.raises(ValueError, match="expected at least"):
            load_mot(path)

    def test_loaded_files_evaluate_perfectly(self, tmp_path):
        lines = [f"{frame},{tid},10,10,20,20,1,0,1" for frame in range(1, 5) for tid in (1, 2)]
        path = tmp_path / "seq.txt"
        path.write_text("\n".join(lines) + "\n")
        frames = load_mot(path)
        metrics = evaluate_mot(frames, frames)
        assert metrics.mota == pytest.approx(1.0)
        assert metrics.num_switches == 0
