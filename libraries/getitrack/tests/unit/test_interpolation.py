# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Tests for the track interpolation stage."""

from __future__ import annotations

import numpy as np
import pytest

from getitrack.config import InterpolationConfig, InterpolationMethod, MotionConfig
from getitrack.core.detection import TrackedDetections
from getitrack.core.track import TrackState
from getitrack.interpolation import BaseInterpolator


def _interp(
    frames: list[TrackedDetections],
    config: InterpolationConfig | None = None,
    *,
    motion: MotionConfig | None = None,
) -> list[TrackedDetections]:
    # The library exposes only the interpolator classes; this wraps the build-and-run for brevity.
    return BaseInterpolator.from_config(config, motion=motion).interpolate(frames)


def _frame(
    frame_id: int, boxes: list[list[float]], track_ids: list[int], scores: list[float] | None = None
) -> TrackedDetections:
    n = len(boxes)
    return TrackedDetections(
        bboxes=np.asarray(boxes, dtype=np.float32).reshape(n, 4),
        scores=np.asarray(scores if scores is not None else [0.9] * n, dtype=np.float32),
        class_ids=np.zeros(n, dtype=np.int64),
        track_ids=np.asarray(track_ids, dtype=np.int64),
        track_states=np.full(n, int(TrackState.ACTIVE), dtype=np.int8),
        frame_id=frame_id,
        det_indices=np.arange(n, dtype=np.int64),
    )


def _no_smoothing(*, max_gap: int = 5, method: InterpolationMethod = InterpolationMethod.LINEAR) -> InterpolationConfig:
    # The default smoothing_window is 5, so isolate the raw fill geometry.
    return InterpolationConfig(smoothing_window=1, max_gap=max_gap, method=method)


def _row(frame: TrackedDetections, track_id: int = 1) -> int:
    (rows,) = np.where(frame.track_ids == track_id)
    assert rows.size == 1  # no duplicate rows for a track in one frame
    return int(rows[0])


def _flags(frame: TrackedDetections) -> np.ndarray:
    # ``interpolated`` is optional on TrackedDetections; the interpolation stage always sets it.
    assert frame.interpolated is not None
    return frame.interpolated


class TestGapFill:
    def test_linear_midpoint_with_synth_metadata(self):
        frames = [
            _frame(0, [[0.0, 0.0, 10.0, 10.0]], [1]),
            _frame(1, [], []),
            _frame(2, [[10.0, 10.0, 20.0, 20.0]], [1]),
        ]
        mid = _interp(frames, _no_smoothing())[1]
        row = _row(mid)
        np.testing.assert_allclose(mid.bboxes[row], [5.0, 5.0, 15.0, 15.0])
        assert bool(_flags(mid)[row]) is True  # synth rows are flagged
        det_indices = mid.det_indices
        assert det_indices is not None
        assert int(det_indices[row]) == -1  # ... and carry no source detection

    def test_score_blends_between_endpoints(self):
        frames = [
            _frame(0, [[0.0, 0.0, 10.0, 10.0]], [1], scores=[0.4]),
            _frame(1, [], []),
            _frame(2, [[0.0, 0.0, 10.0, 10.0]], [1], scores=[0.8]),
        ]
        assert _interp(frames, _no_smoothing())[1].scores[0] == pytest.approx(0.6)

    def test_multi_frame_gap_fills_every_frame(self):
        frames = [
            _frame(0, [[0.0, 0.0, 10.0, 10.0]], [1]),
            *[_frame(f, [], []) for f in (1, 2, 3)],
            _frame(4, [[40.0, 0.0, 50.0, 10.0]], [1]),
        ]
        result = _interp(frames, _no_smoothing())
        xs = [float(result[i].bboxes[_row(result[i])][0]) for i in (1, 2, 3)]
        np.testing.assert_allclose(xs, [10.0, 20.0, 30.0])

    @pytest.mark.parametrize(("gap", "filled"), [(5, True), (6, False)])
    def test_max_gap_boundary(self, gap, filled):
        frames = [
            _frame(0, [[0.0, 0.0, 10.0, 10.0]], [1]),
            *[_frame(f, [], []) for f in range(1, gap + 1)],
            _frame(gap + 1, [[10.0, 0.0, 20.0, 10.0]], [1]),
        ]
        result = _interp(frames, InterpolationConfig(max_gap=5))
        assert (len(result[1]) == 1) is filled


class TestNoOp:
    def test_empty_input(self):
        assert _interp([], InterpolationConfig()) == []

    def test_disabled_returns_same_objects(self):
        frames = [
            _frame(0, [[0.0, 0.0, 10.0, 10.0]], [1]),
            _frame(1, [], []),
            _frame(2, [[10.0, 10.0, 20.0, 20.0]], [1]),
        ]
        result = _interp(frames, InterpolationConfig(enabled=False))
        assert [id(f) for f in result] == [id(f) for f in frames]

    def test_single_observation_not_filled(self):
        frames = [_frame(0, [[0.0, 0.0, 10.0, 10.0]], [1]), _frame(1, [], []), _frame(2, [], [])]
        result = _interp(frames, InterpolationConfig(max_gap=5))
        assert [id(f) for f in result] == [id(f) for f in frames]


class TestMultiTrack:
    def test_tracks_filled_independently(self):
        frames = [
            _frame(0, [[0.0, 0.0, 10.0, 10.0], [100.0, 0.0, 110.0, 10.0]], [1, 2]),
            _frame(1, [[100.0, 0.0, 110.0, 10.0]], [2]),  # track 1 missing
            _frame(2, [[20.0, 0.0, 30.0, 10.0], [100.0, 0.0, 110.0, 10.0]], [1, 2]),
        ]
        mid = _interp(frames, _no_smoothing())[1]
        assert len(mid) == 2
        np.testing.assert_allclose(mid.bboxes[_row(mid, 1)], [10.0, 0.0, 20.0, 10.0])
        assert bool(_flags(mid)[_row(mid, 1)]) is True  # synth
        assert bool(_flags(mid)[_row(mid, 2)]) is False  # observed, untouched

    def test_unsorted_input_is_ordered(self):
        frames = [
            _frame(2, [[10.0, 10.0, 20.0, 20.0]], [1]),
            _frame(0, [[0.0, 0.0, 10.0, 10.0]], [1]),
            _frame(1, [], []),
        ]
        result = _interp(frames, InterpolationConfig(max_gap=5))
        assert [f.frame_id for f in result] == [0, 1, 2]
        assert len(result[1]) == 1


class TestMethods:
    @pytest.mark.parametrize("method", list(InterpolationMethod))
    def test_all_methods_recover_translation_midpoint(self, method):
        # Pure translation: linear, kalman (undamped) and spline (2 points) all agree.
        frames = [
            _frame(0, [[0.0, 0.0, 20.0, 10.0]], [1]),
            _frame(1, [], []),
            _frame(2, [[20.0, 0.0, 40.0, 10.0]], [1]),
        ]
        mid = _interp(frames, _no_smoothing(method=method))[1]
        np.testing.assert_allclose(mid.bboxes[_row(mid)], [10.0, 0.0, 30.0, 10.0], atol=1e-3)

    def test_spline_bends_toward_neighbours(self):
        # Quadratic trajectory through frames 0,1,3 (cy = 5,15,95): the spline
        # curves to cy=45 (y1=40) at frame 2, below the straight-line 50.
        frames = [
            _frame(0, [[0.0, 0.0, 10.0, 10.0]], [1]),
            _frame(1, [[0.0, 10.0, 10.0, 20.0]], [1]),
            _frame(2, [], []),
            _frame(3, [[0.0, 90.0, 10.0, 100.0]], [1]),
        ]
        spline = _interp(frames, _no_smoothing(method=InterpolationMethod.SPLINE))
        linear = _interp(frames, _no_smoothing(method=InterpolationMethod.LINEAR))
        assert float(spline[2].bboxes[_row(spline[2])][1]) == pytest.approx(40.0, abs=1e-3)
        assert float(linear[2].bboxes[_row(linear[2])][1]) == pytest.approx(50.0, abs=1e-3)

    def test_spline_two_observations_falls_back_to_line(self):
        frames = [
            _frame(0, [[0.0, 0.0, 10.0, 10.0]], [1]),
            _frame(1, [], []),
            _frame(2, [], []),
            _frame(3, [[30.0, 0.0, 40.0, 10.0]], [1]),
        ]
        result = _interp(frames, _no_smoothing(method=InterpolationMethod.SPLINE))
        np.testing.assert_allclose(result[1].bboxes[_row(result[1])], [10.0, 0.0, 20.0, 10.0], atol=1e-3)

    def test_kalman_velocity_decay_undershoots(self):
        frames = [
            _frame(0, [[0.0, 0.0, 10.0, 10.0]], [1]),
            *[_frame(f, [], []) for f in range(1, 5)],
            _frame(5, [[50.0, 0.0, 60.0, 10.0]], [1]),
        ]
        cfg = _no_smoothing(method=InterpolationMethod.KALMAN)
        damped = _interp(frames, cfg, motion=MotionConfig(velocity_decay=0.5))
        undamped = _interp(frames, cfg)
        assert float(undamped[4].bboxes[_row(undamped[4])][0]) == pytest.approx(40.0, abs=1e-3)
        assert float(damped[4].bboxes[_row(damped[4])][0]) < float(undamped[4].bboxes[_row(undamped[4])][0])

    def test_degenerate_anchor_does_not_crash(self):
        # A zero-area anchor is floored, not raised on, in the xyah conversion.
        frames = [
            _frame(0, [[5.0, 5.0, 5.0, 5.0]], [1]),
            _frame(1, [], []),
            _frame(2, [[15.0, 15.0, 25.0, 25.0]], [1]),
        ]
        result = _interp(frames, _no_smoothing(method=InterpolationMethod.KALMAN))
        assert np.all(np.isfinite(result[1].bboxes))


class TestSmoothing:
    def test_moving_average_pulls_synth_toward_neighbours(self):
        frames = [
            _frame(0, [[0.0, 0.0, 10.0, 10.0]], [1]),
            _frame(1, [[0.0, 0.0, 10.0, 10.0]], [1]),
            _frame(2, [], []),
            _frame(3, [[30.0, 0.0, 40.0, 10.0]], [1]),
            _frame(4, [[90.0, 0.0, 100.0, 10.0]], [1]),
        ]
        raw = _interp(frames, _no_smoothing())[2]
        smoothed = _interp(frames, InterpolationConfig(max_gap=5, smoothing_window=5))[2]
        assert float(raw.bboxes[_row(raw)][0]) == pytest.approx(15.0)  # linear midpoint of 0, 30
        assert float(smoothed.bboxes[_row(smoothed)][0]) == pytest.approx(27.0)  # mean of [0, 0, 15, 30, 90]


class TestIdempotency:
    def test_interpolating_twice_matches_once(self):
        frames = [
            _frame(0, [[0.0, 0.0, 10.0, 10.0]], [1]),
            _frame(1, [], []),
            _frame(2, [], []),
            _frame(3, [[30.0, 0.0, 40.0, 10.0]], [1]),
        ]
        once = _interp(frames, InterpolationConfig(max_gap=5))
        twice = _interp(once, InterpolationConfig(max_gap=5))
        for a, b in zip(once, twice, strict=True):
            np.testing.assert_array_equal(np.sort(a.track_ids), np.sort(b.track_ids))  # no duplicate rows
            np.testing.assert_allclose(a.bboxes, b.bboxes)


class TestCausalMode:
    def test_online_buffer_limits_lookahead(self):
        frames = [
            _frame(0, [[0.0, 0.0, 10.0, 10.0]], [1]),
            _frame(1, [], []),
            _frame(2, [], []),
            _frame(3, [[30.0, 0.0, 40.0, 10.0]], [1]),
        ]
        result = _interp(frames, InterpolationConfig(max_gap=5, online=True, online_buffer=1))
        assert len(result[1]) == 0  # closing obs 2 frames ahead, beyond buffer
        assert len(result[2]) == 1  # closing obs 1 frame ahead

    def test_online_field_selects_causal_fill(self):
        # InterpolationConfig.online is the single switch: causal vs offline.
        frames = [
            _frame(0, [[0.0, 0.0, 10.0, 10.0]], [1]),
            _frame(1, [], []),
            _frame(2, [[10.0, 10.0, 20.0, 20.0]], [1]),
        ]
        causal = InterpolationConfig(max_gap=5, online=True, online_buffer=0)
        offline = InterpolationConfig(max_gap=5, online=False)
        assert len(_interp(frames, causal)[1]) == 0  # strictly causal (buffer 0) fills nothing
        assert len(_interp(frames, offline)[1]) == 1  # offline bridges the gap

    def test_smoothing_respects_causal_horizon(self):
        # Online mode must not smooth a synth frame against an observation beyond
        # its lookahead horizon (frame + online_buffer).
        def clip(far_box: list[float]) -> list[TrackedDetections]:
            return [
                _frame(0, [[0.0, 0.0, 10.0, 10.0]], [1]),
                _frame(1, [[10.0, 0.0, 20.0, 10.0]], [1]),
                _frame(2, [], []),
                _frame(3, [], []),
                _frame(4, [[40.0, 0.0, 50.0, 10.0]], [1]),
                _frame(5, [far_box], [1]),
            ]

        online = InterpolationConfig(max_gap=5, online=True, online_buffer=1, smoothing_window=5)
        near = _interp(clip([50.0, 0.0, 60.0, 10.0]), online)
        far = _interp(clip([500.0, 0.0, 510.0, 10.0]), online)
        np.testing.assert_array_equal(near[3].bboxes[_row(near[3])], far[3].bboxes[_row(far[3])])
        # Offline uses the full centred window, so the far box does move it.
        offline = InterpolationConfig(max_gap=5, smoothing_window=5)
        off_near = _interp(clip([50.0, 0.0, 60.0, 10.0]), offline)
        off_far = _interp(clip([500.0, 0.0, 510.0, 10.0]), offline)
        assert not np.array_equal(off_near[3].bboxes[_row(off_near[3])], off_far[3].bboxes[_row(off_far[3])])

    def test_spline_fill_respects_causal_horizon(self):
        # A spline fits the whole trajectory, so online mode must hide observations
        # past a gap's closing anchor: an already-filled gap frame must not move
        # when a later observation is added. Smoothing is off to isolate the fill.
        def clip(far_box: list[float]) -> list[TrackedDetections]:
            return [
                _frame(0, [[0.0, 0.0, 10.0, 10.0]], [1]),
                _frame(1, [[10.0, 0.0, 20.0, 10.0]], [1]),
                _frame(2, [], []),  # gap
                _frame(3, [], []),  # gap
                _frame(4, [[40.0, 0.0, 50.0, 10.0]], [1]),  # closing anchor
                _frame(5, [far_box], [1]),  # future observation, beyond the anchor
            ]

        online = InterpolationConfig(
            max_gap=5, online=True, online_buffer=3, smoothing_window=1, method=InterpolationMethod.SPLINE
        )
        near = _interp(clip([50.0, 0.0, 60.0, 10.0]), online)
        far = _interp(clip([500.0, 0.0, 510.0, 10.0]), online)
        np.testing.assert_array_equal(near[2].bboxes[_row(near[2])], far[2].bboxes[_row(far[2])])
        # Offline sees the whole trajectory, so the future box does bend the fill.
        offline = InterpolationConfig(max_gap=5, smoothing_window=1, method=InterpolationMethod.SPLINE)
        off_near = _interp(clip([50.0, 0.0, 60.0, 10.0]), offline)
        off_far = _interp(clip([500.0, 0.0, 510.0, 10.0]), offline)
        assert not np.array_equal(off_near[2].bboxes[_row(off_near[2])], off_far[2].bboxes[_row(off_far[2])])


class TestSparseClip:
    def test_absent_gap_frame_is_skipped(self):
        # Frame 1 is present and filled; frame 2 is absent from the clip and skipped.
        frames = [
            _frame(0, [[0.0, 0.0, 10.0, 10.0]], [1]),
            _frame(1, [], []),
            _frame(3, [[30.0, 0.0, 40.0, 10.0]], [1]),
        ]
        result = _interp(frames, InterpolationConfig(max_gap=5))
        assert [f.frame_id for f in result] == [0, 1, 3]
        assert len(result[1]) == 1


class TestConstruction:
    def test_default_config_is_offline_linear(self):
        cfg = BaseInterpolator.from_config().config
        assert cfg.method is InterpolationMethod.LINEAR
        assert cfg.online is False

    def test_prior_interpolated_rows_are_not_anchors(self):
        # A pre-existing interpolated row must not seed a fill nor gain a duplicate.
        synthetic = TrackedDetections(
            bboxes=np.asarray([[5.0, 5.0, 15.0, 15.0]], dtype=np.float32),
            scores=np.asarray([0.5], dtype=np.float32),
            class_ids=np.zeros(1, dtype=np.int64),
            track_ids=np.asarray([1], dtype=np.int64),
            track_states=np.asarray([int(TrackState.ACTIVE)], dtype=np.int8),
            frame_id=1,
            det_indices=np.asarray([-1], dtype=np.int64),
            interpolated=np.asarray([True], dtype=np.bool_),
        )
        frames = [
            _frame(0, [[0.0, 0.0, 10.0, 10.0]], [1]),
            synthetic,
            TrackedDetections.create_empty(frame_id=2),
            _frame(3, [[30.0, 30.0, 40.0, 40.0]], [1]),
        ]
        result = _interp(frames, InterpolationConfig(max_gap=5))
        assert len(result[1]) == 1  # no duplicate on the pre-existing row
        assert bool(_flags(result[2])[_row(result[2])]) is True  # anchors are frames 0 and 3
