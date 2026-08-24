# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Unit + integration tests for the ByteTrack algorithm."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from pydantic import ValidationError

import getitrack.algorithms  # noqa: F401  -> registers ByteTrack
from getitrack.algorithms import ByteTrackTracker
from getitrack.algorithms.bytetrack import _subset
from getitrack.algorithms.configs.bytetrack import ByteTrackConfig
from getitrack.config import LifecycleConfig, TrackerConfig
from getitrack.core.base import BaseTracker
from getitrack.core.detection import Detections, TrackedDetections
from getitrack.core.track import Track, TrackState


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
def fast_confirm_config() -> ByteTrackConfig:
    # Confirm after 1 hit so single-frame tests don't have to spam frames.
    return ByteTrackConfig(lifecycle=LifecycleConfig(min_hits=1, tentative_max_age=1, max_age=5))


class TestRegistry:
    def test_from_config_dispatches_to_bytetrack(self):
        cfg = ByteTrackConfig()
        tracker = BaseTracker.from_config(cfg)
        assert isinstance(tracker, ByteTrackTracker)


class TestSingleObject:
    def test_id_persists_across_frames(self, fast_confirm_config):
        bt = ByteTrackTracker(fast_confirm_config)
        out0 = bt.update(_dets([[10, 10, 50, 50]], [0.9], frame_id=0))
        out = bt.update(_dets([[12, 12, 52, 52]], [0.9], frame_id=1))
        assert out0.track_ids.tolist() == [1]
        assert len(out) == 1
        assert out.track_ids[0] == 1


class TestMultiObject:
    def test_class_only_matching_keeps_classes_separate(self):
        cfg = ByteTrackConfig(lifecycle=LifecycleConfig(min_hits=1, tentative_max_age=1))
        bt = ByteTrackTracker(cfg)
        bt.update(_dets([[0, 0, 20, 20]], [0.9], frame_id=0, class_ids=[0]))
        # Same location, different class -> a new id, not a match.
        out = bt.update(_dets([[0, 0, 20, 20]], [0.9], frame_id=1, class_ids=[1]))
        assert sorted(out.track_ids.tolist()) == [2]


class TestLowScoreRecovery:
    def test_low_score_detection_keeps_track_active(self):
        cfg = ByteTrackConfig(lifecycle=LifecycleConfig(min_hits=1, tentative_max_age=1))
        bt = ByteTrackTracker(cfg)
        bt.update(_dets([[10, 10, 50, 50]], [0.9], frame_id=0))
        # Only a low-score detection on frame 1; first-pass would miss it but second-pass picks it up.
        out = bt.update(_dets([[12, 12, 52, 52]], [0.3], frame_id=1))
        assert len(out) == 1
        assert out.track_ids[0] == 1


class TestConfigValidation:
    def test_low_floor_above_high_split_rejected(self):
        with pytest.raises(ValidationError, match="score_threshold must be below"):
            ByteTrackConfig(score_threshold=0.7, high_score_threshold=0.5)

    def test_high_split_without_room_for_margin_rejected(self):
        with pytest.raises(ValidationError, match="new-track margin"):
            ByteTrackConfig(high_score_threshold=0.95)

    def test_default_yaml_matches_programmatic_defaults(self):
        path = Path(__file__).resolve().parents[2] / "configs" / "default.yaml"
        assert TrackerConfig.from_yaml(path) == ByteTrackConfig()


class TestThresholdSemantics:
    def test_mid_score_detection_reactivates_lost_track(self):
        # A 0.55 detection is above the 0.5 high/low split, so it reaches the
        # first-pass association and recovers a LOST track, even though it is
        # below the 0.6 new-track threshold.
        bt = ByteTrackTracker(ByteTrackConfig(lifecycle=LifecycleConfig(min_hits=1, max_age=5)))
        bt.update(_dets([[10, 10, 50, 50]], [0.9], frame_id=0))
        bt.update(_dets([], [], frame_id=1))  # miss -> LOST
        out = bt.update(_dets([[12, 12, 52, 52]], [0.55], frame_id=2))
        assert out.track_ids.tolist() == [1]

    def test_high_detection_below_margin_does_not_spawn(self):
        # 0.55 clears the split but not the split + 0.1 new-track margin, so with
        # no track to match it spawns nothing.
        bt = ByteTrackTracker(ByteTrackConfig(lifecycle=LifecycleConfig(min_hits=1)))
        out = bt.update(_dets([[10, 10, 50, 50]], [0.55], frame_id=0))
        assert len(out) == 0


class TestDuplicateSuppression:
    def test_active_duplicated_against_multiple_lost_does_not_crash(self):
        bt = ByteTrackTracker(ByteTrackConfig())
        box = np.array([0, 0, 40, 40], dtype=np.float32)
        bt._tracks = {
            1: Track(track_id=1, class_id=0, bbox=box, score=0.9, state=TrackState.LOST, age=10),
            2: Track(track_id=2, class_id=0, bbox=box.copy(), score=0.9, state=TrackState.LOST, age=10),
            3: Track(track_id=3, class_id=0, bbox=box.copy(), score=0.9, state=TrackState.ACTIVE, age=1),
        }
        bt._remove_duplicate_tracks()
        # Track 3 duplicates both LOST tracks; it is dropped once, no KeyError.
        assert set(bt._tracks) == {1, 2}

    def test_equal_age_tie_drops_active_track(self):
        bt = ByteTrackTracker(ByteTrackConfig())
        box = np.array([0, 0, 40, 40], dtype=np.float32)
        bt._tracks = {
            1: Track(track_id=1, class_id=0, bbox=box, score=0.9, state=TrackState.LOST, age=5),
            2: Track(track_id=2, class_id=0, bbox=box.copy(), score=0.9, state=TrackState.ACTIVE, age=5),
        }
        bt._remove_duplicate_tracks()
        # On an age tie the reference drops the active-side track.
        assert set(bt._tracks) == {1}

    def test_overlapping_pair_of_different_classes_is_kept(self):
        bt = ByteTrackTracker(ByteTrackConfig())
        box = np.array([0, 0, 40, 40], dtype=np.float32)
        bt._tracks = {
            1: Track(track_id=1, class_id=0, bbox=box, score=0.9, state=TrackState.LOST, age=10),
            2: Track(track_id=2, class_id=1, bbox=box.copy(), score=0.9, state=TrackState.ACTIVE, age=1),
        }
        bt._remove_duplicate_tracks()
        assert set(bt._tracks) == {1, 2}


class TestEmpty:
    def test_reset_clears_state(self, fast_confirm_config):
        bt = ByteTrackTracker(fast_confirm_config)
        bt.update(_dets([[10, 10, 50, 50]], [0.9], frame_id=0))
        bt.reset()
        out = bt.update(_dets([[10, 10, 50, 50]], [0.9], frame_id=0))
        # Id allocator is back to 1 after reset.
        assert out.track_ids[0] == 1


class TestLifecycle:
    def test_aging_out_removes_track(self):
        cfg = ByteTrackConfig(lifecycle=LifecycleConfig(min_hits=1, tentative_max_age=1, max_age=2))
        bt = ByteTrackTracker(cfg)
        bt.update(_dets([[10, 10, 50, 50]], [0.9], frame_id=0))
        # Three empty frames: state goes ACTIVE -> LOST (frame 1) -> still LOST (2) -> REMOVED (3).
        for f in range(1, 4):
            bt.update(_dets([], [], frame_id=f))
        # A fresh detection now should spawn track id 2, not reuse 1.
        out = bt.update(_dets([[10, 10, 50, 50]], [0.9], frame_id=4))
        assert out.track_ids[0] != 1


class TestStandardLifecycleDefaults:
    """Default config reproduces reference ByteTrack confirmation behavior."""

    def test_mid_sequence_track_confirms_on_second_match(self):
        bt = ByteTrackTracker(ByteTrackConfig())
        # min_hits=2 default, but tracks born on the first frame bypass TENTATIVE.
        out0 = bt.update(_dets([[10, 10, 50, 50]], [0.9], frame_id=0))
        assert len(out0) == 1
        # New object on frame 1 starts TENTATIVE: not output yet.
        out1 = bt.update(_dets([[10, 10, 50, 50], [200, 200, 240, 240]], [0.9, 0.9], frame_id=1))
        assert len(out1) == 1
        # Its second match confirms it.
        out2 = bt.update(_dets([[10, 10, 50, 50], [202, 202, 242, 242]], [0.9, 0.9], frame_id=2))
        assert len(out2) == 2

    def test_tentative_removed_on_first_miss(self):
        # tentative_max_age=0 default: one missed frame kills an unconfirmed track.
        bt = ByteTrackTracker(ByteTrackConfig())
        bt.update(_dets([[10, 10, 50, 50]], [0.9], frame_id=0))
        bt.update(_dets([[10, 10, 50, 50], [200, 200, 240, 240]], [0.9, 0.9], frame_id=1))
        bt.update(_dets([[10, 10, 50, 50]], [0.9], frame_id=2))
        # The object reappears and confirms; it must carry a fresh id, not 2.
        bt.update(_dets([[10, 10, 50, 50], [200, 200, 240, 240]], [0.9, 0.9], frame_id=3))
        out = bt.update(_dets([[10, 10, 50, 50], [200, 200, 240, 240]], [0.9, 0.9], frame_id=4))
        assert sorted(out.track_ids.tolist()) == [1, 3]


class TestDetIndices:
    def test_det_indices_point_to_original_rows_for_low_score_matches(self):
        cfg = ByteTrackConfig(lifecycle=LifecycleConfig(min_hits=1, tentative_max_age=1))
        bt = ByteTrackTracker(cfg)
        bt.update(_dets([[10, 10, 50, 50]], [0.9], frame_id=0))
        # Row 0 is a low-score continuation; row 1 is an unrelated high-score det.
        dets1 = _dets([[12, 12, 52, 52], [300, 300, 340, 340]], [0.3, 0.9], frame_id=1)
        out1 = bt.update(dets1)
        assert out1.det_indices is not None
        idx_of_track_1 = int(out1.det_indices[out1.track_ids.tolist().index(1)])
        assert idx_of_track_1 == 0

    def test_empty_frame_has_empty_det_indices(self, fast_confirm_config):
        bt = ByteTrackTracker(fast_confirm_config)
        out = bt.update(_dets([], [], frame_id=0))
        assert out.det_indices is not None
        assert len(out.det_indices) == 0


def _mixed_state_tracker() -> tuple[ByteTrackTracker, TrackedDetections]:
    """Drive a tracker to a frame holding one ACTIVE, one LOST, one TENTATIVE track.

    Returns the tracker and the frame-2 ``update`` output (ACTIVE only). After
    frame 2: track 1 (A) coasts as LOST, track 2 (B) stays ACTIVE, and track 3
    (C) is freshly spawned TENTATIVE.
    """
    cfg = ByteTrackConfig(lifecycle=LifecycleConfig(min_hits=2, tentative_max_age=3, max_age=3))
    bt = ByteTrackTracker(cfg)
    # Frame 0: both born ACTIVE (first frame bypasses TENTATIVE). A=id1, B=id2.
    bt.update(_dets([[10, 10, 50, 50], [200, 200, 240, 240]], [0.9, 0.9], frame_id=0))
    # Frame 1: A drifts +10 (still matches), B is stationary.
    bt.update(_dets([[20, 20, 60, 60], [200, 200, 240, 240]], [0.9, 0.9], frame_id=1))
    # Frame 2: A absent -> LOST; B (row 0) matched; C (row 1) new -> TENTATIVE id3.
    out2 = bt.update(_dets([[200, 200, 240, 240], [400, 400, 440, 440]], [0.9, 0.9], frame_id=2))
    return bt, out2


class TestStateAccessors:
    def test_tracks_exposes_all_lifecycle_states(self):
        bt, _ = _mixed_state_tracker()
        tracks = bt.tracks
        assert all(isinstance(t, Track) for t in tracks)
        by_id = {t.track_id: t.state for t in tracks}
        assert by_id == {1: TrackState.LOST, 2: TrackState.ACTIVE, 3: TrackState.TENTATIVE}

    def test_tracks_returns_a_fresh_list(self):
        bt, _ = _mixed_state_tracker()
        tracks = bt.tracks
        tracks.clear()
        # Mutating the returned list must not disturb tracker state.
        assert len(bt.tracks) == 3

    def test_tracked_objects_includes_coasted_lost_track(self):
        bt, out2 = _mixed_state_tracker()
        to = bt.tracked_objects()
        assert to.det_indices is not None
        rows = {int(tid): i for i, tid in enumerate(to.track_ids)}
        # ACTIVE and LOST are both emitted; TENTATIVE (id 3) is not.
        assert set(rows) == {1, 2}
        # The LOST track coasts: no source detection this frame -> det_index -1.
        lost_row = rows[1]
        assert to.track_states[lost_row] == TrackState.LOST
        assert int(to.det_indices[lost_row]) == -1
        # A drifted in +x/+y, so the coasted Kalman prediction advances past the
        # last observed box [20, 20, 60, 60] rather than reusing it.
        lost_box = to.bboxes[lost_row]
        assert lost_box[0] > 20.0
        assert lost_box[1] > 20.0
        # The ACTIVE track keeps its real detection index (B is input row 0).
        active_row = rows[2]
        assert to.track_states[active_row] == TrackState.ACTIVE
        assert int(to.det_indices[active_row]) == 0
        # update() stays ACTIVE-only, so tracked_objects() is strictly larger here.
        assert out2.track_ids.tolist() == [2]
        assert len(to) == 2

    def test_tracked_objects_excludes_removed_track(self):
        bt, _ = _mixed_state_tracker()
        # Keep feeding only B; A (id1) coasts until it ages past max_age -> REMOVED.
        for f in range(3, 8):
            bt.update(_dets([[200, 200, 240, 240]], [0.9], frame_id=f))
        live_ids = {t.track_id for t in bt.tracks}
        assert 1 not in live_ids
        assert 1 not in bt.tracked_objects().track_ids.tolist()

    def test_tracked_objects_dtypes_and_shape_match_update(self):
        bt, out2 = _mixed_state_tracker()
        to = bt.tracked_objects()
        assert to.det_indices is not None
        assert to.bboxes.dtype == out2.bboxes.dtype == np.float32
        assert to.scores.dtype == out2.scores.dtype == np.float32
        assert to.class_ids.dtype == out2.class_ids.dtype == np.int64
        assert to.track_ids.dtype == out2.track_ids.dtype == np.int64
        assert to.track_states.dtype == out2.track_states.dtype == np.int8
        assert to.det_indices.dtype == np.int64
        assert to.bboxes.shape[1] == 4

    def test_tracked_objects_before_any_frame_is_empty(self):
        bt = ByteTrackTracker(ByteTrackConfig())
        to = bt.tracked_objects()
        assert len(to) == 0
        assert to.det_indices is not None
        assert to.det_indices.dtype == np.int64
        assert len(to.det_indices) == 0
        assert bt.tracks == []

    def test_tracked_objects_only_tentative_hits_empty_branch(self):
        # A non-empty _tracks whose tracks are all TENTATIVE yields no alive rows,
        # so the empty-output branch runs even though the tracker holds a track.
        bt = ByteTrackTracker(ByteTrackConfig())
        box = np.array([0, 0, 40, 40], dtype=np.float32)
        bt._tracks = {1: Track(track_id=1, class_id=0, bbox=box, score=0.9, state=TrackState.TENTATIVE)}
        to = bt.tracked_objects()
        assert len(to) == 0
        assert to.det_indices is not None
        assert len(to.det_indices) == 0
        assert len(bt.tracks) == 1

    def test_tracked_objects_det_indices_index_unfiltered_rows_under_class_filter(self):
        # Row 0 (class 0) is filtered out; row 1 (class 5) is tracked. det_indices
        # must point at input row 1, matching update(), not the filtered-space 0.
        cfg = ByteTrackConfig(class_filter=[5], lifecycle=LifecycleConfig(min_hits=1, tentative_max_age=1))
        bt = ByteTrackTracker(cfg)
        dets = _dets([[10, 10, 50, 50], [100, 100, 140, 140]], [0.9, 0.9], frame_id=0, class_ids=[0, 5])
        out = bt.update(dets)
        to = bt.tracked_objects()
        assert out.det_indices is not None
        assert to.det_indices is not None
        # The single tracked object came from input row 1 in both views.
        assert out.track_ids.tolist() == [1]
        assert out.det_indices.tolist() == [1]
        assert to.track_ids.tolist() == [1]
        assert to.det_indices.tolist() == [1]

    def test_tracked_objects_det_index_becomes_valid_after_lost_recovery(self):
        bt, _ = _mixed_state_tracker()
        # Track 1 is LOST after frame 2 (det_index -1); its predicted box sits
        # near [21, 21, 61, 61]. A detection there re-matches and reactivates it.
        assert bt._tracks[1].state == TrackState.LOST
        bt.update(_dets([[22, 22, 62, 62]], [0.9], frame_id=3))
        assert bt._tracks[1].state == TrackState.ACTIVE
        to = bt.tracked_objects()
        assert to.det_indices is not None
        rows = {int(tid): i for i, tid in enumerate(to.track_ids)}
        recovered_row = rows[1]
        assert to.track_states[recovered_row] == TrackState.ACTIVE
        # The recovered track now carries a real detection index again (input row 0).
        assert int(to.det_indices[recovered_row]) == 0

    def test_tracked_objects_lost_box_advances_over_multiple_coasted_frames(self):
        bt, _ = _mixed_state_tracker()

        def lost_x1() -> float:
            to = bt.tracked_objects()
            rows = {int(tid): i for i, tid in enumerate(to.track_ids)}
            return float(to.bboxes[rows[1]][0])

        # Frame 2: track 1 just went LOST. Keep feeding only B so track 1 keeps
        # coasting; its predicted x should advance each frame while still LOST.
        x2 = lost_x1()
        bt.update(_dets([[200, 200, 240, 240]], [0.9], frame_id=3))
        x3 = lost_x1()
        bt.update(_dets([[200, 200, 240, 240]], [0.9], frame_id=4))
        x4 = lost_x1()
        assert bt._tracks[1].state == TrackState.LOST
        assert x3 > x2
        assert x4 > x3


class TestSubset:
    def _dets_with_embeddings(self, dim: int = 128) -> Detections:
        return Detections(
            bboxes=np.zeros((3, 4), dtype=np.float32),
            scores=np.ones(3, dtype=np.float32),
            class_ids=np.zeros(3, dtype=np.int64),
            frame_id=0,
            embeddings=np.zeros((3, dim), dtype=np.float32),
        )

    def test_empty_subset_preserves_embedding_dim(self):
        empty = _subset(self._dets_with_embeddings(dim=128), [])
        assert len(empty) == 0
        assert empty.embeddings is not None
        assert empty.embeddings.shape == (0, 128)

    def test_subset_keeps_selected_rows(self):
        subset = _subset(self._dets_with_embeddings(), [0, 2])
        assert len(subset) == 2
        assert subset.embeddings is not None
        assert subset.embeddings.shape == (2, 128)
