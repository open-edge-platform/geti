# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Unit + integration tests for the StrongSORT tracker and its config."""

from __future__ import annotations

import numpy as np
import pytest

import getitrack.algorithms  # noqa: F401  -> registers StrongSORT
from getitrack.algorithms import SortTracker, StrongSortTracker
from getitrack.algorithms.configs.sort import SortConfig
from getitrack.algorithms.configs.strongsort import StrongSortConfig
from getitrack.config import AlgorithmType, LifecycleConfig, TrackerConfig
from getitrack.core.base import BaseTracker
from getitrack.core.detection import Detections
from getitrack.core.registry import resolve_tracker_config
from getitrack.motion import KalmanFilter

_E_A = np.array([1.0, 0.0], dtype=np.float32)
_E_B = np.array([0.0, 1.0], dtype=np.float32)


def _rotation_warp(theta: float) -> np.ndarray:
    """Return a 2x3 pure-rotation affine warp (about the origin)."""
    cos, sin = np.cos(theta), np.sin(theta)
    return np.array([[cos, -sin, 0.0], [sin, cos, 0.0]], dtype=np.float32)


def _dets(
    boxes: list[list[float]],
    scores: list[float],
    frame_id: int,
    embeddings: list[np.ndarray] | None = None,
) -> Detections:
    n = len(boxes)
    emb: np.ndarray | None = None
    if embeddings is not None:
        emb = np.asarray(embeddings, dtype=np.float32).reshape(n, -1) if n else np.empty((0, 2), dtype=np.float32)
    return Detections(
        bboxes=np.asarray(boxes, dtype=np.float32).reshape(n, 4),
        scores=np.asarray(scores, dtype=np.float32),
        class_ids=np.zeros(n, dtype=np.int64),
        frame_id=frame_id,
        embeddings=emb,
    )


class TestConfigRegistry:
    def test_from_config_dispatches_to_strongsort(self):
        tracker = BaseTracker.from_config(StrongSortConfig())
        assert isinstance(tracker, StrongSortTracker)

    def test_resolve_dispatches_on_algorithm_key(self):
        resolved = resolve_tracker_config({"algorithm": "strongsort", "appearance_weight": 0.6})
        assert isinstance(resolved, StrongSortConfig)
        assert resolved.appearance_weight == pytest.approx(0.6)

    def test_algorithm_is_pinned(self):
        assert StrongSortConfig().algorithm == AlgorithmType.STRONGSORT

    def test_appearance_is_primary_by_default(self):
        assert StrongSortConfig().appearance_weight == pytest.approx(0.75)

    def test_gmc_enabled_by_default_nsa_off_by_default(self):
        cfg = StrongSortConfig()
        assert cfg.gmc_enabled is True
        assert cfg.nsa_kalman is False

    def test_yaml_round_trip(self, tmp_path):
        cfg = StrongSortConfig(
            appearance_weight=0.5,
            gallery_size=17,
            appearance_threshold=0.3,
            use_ema=False,
            gmc_enabled=False,
            nsa_kalman=True,
            lifecycle=LifecycleConfig(max_age=42),
        )
        path = tmp_path / "strongsort.yaml"
        cfg.to_yaml(path)
        assert TrackerConfig.from_yaml(path) == cfg

    def test_reid_section_defaults(self):
        cfg = StrongSortConfig()
        assert cfg.reid.enabled is False
        assert cfg.reid.model_path is None
        assert cfg.reid.input_size == (256, 128)

    def test_extends_sort_parameters(self):
        # StrongSORT inherits the SORT knobs (e.g. the IoU threshold).
        assert StrongSortConfig().iou_threshold == pytest.approx(0.3)


class TestReidProviderProperty:
    def test_provider_is_none_when_reid_disabled(self):
        assert StrongSortTracker(StrongSortConfig()).reid_provider is None


class TestReidConfigWarning:
    def test_strongsort_config_with_enabled_reid_and_no_path_warns(self):
        from getitrack.config import ReIDConfig

        with pytest.warns(UserWarning, match="neither model_name nor model_path"):
            StrongSortConfig(reid=ReIDConfig(enabled=True))


class TestReducesToSort:
    """With appearance (no embeddings), GMC, and NSA off, StrongSORT == SORT."""

    @staticmethod
    def _sequence() -> list[Detections]:
        return [
            _dets([[10, 10, 50, 50], [200, 200, 240, 240]], [0.9, 0.8], frame_id=0),
            _dets([[14, 12, 54, 52], [203, 201, 243, 241]], [0.9, 0.8], frame_id=1),
            _dets([[18, 14, 58, 54]], [0.9], frame_id=2),  # second target drops out
            _dets([[22, 16, 62, 56], [260, 260, 300, 300]], [0.9, 0.85], frame_id=3),  # new spawn
        ]

    def test_identical_outputs_frame_by_frame(self):
        lifecycle = LifecycleConfig(min_hits=1, tentative_max_age=1, max_age=5)
        sort = SortTracker(SortConfig(lifecycle=lifecycle))
        strong = StrongSortTracker(StrongSortConfig(lifecycle=lifecycle, gmc_enabled=False))
        for dets in self._sequence():
            out_sort = sort.update(dets)
            out_strong = strong.update(dets)
            np.testing.assert_array_equal(out_strong.track_ids, out_sort.track_ids)
            np.testing.assert_array_equal(out_strong.det_indices, out_sort.det_indices)
            np.testing.assert_allclose(out_strong.bboxes, out_sort.bboxes, rtol=1e-6, atol=1e-6)


class TestAppearanceRecovery:
    """Appearance recovers an identity across an occlusion that IoU alone drops."""

    @staticmethod
    def _run(tracker: BaseTracker) -> int:
        tracker.update(_dets([[50, 50, 90, 90]], [0.9], frame_id=0, embeddings=[_E_A]))
        tracker.update(_dets([], [], frame_id=1, embeddings=[]))
        out = tracker.update(
            _dets(
                [[50, 50, 90, 90], [46, 46, 86, 86]],
                [0.9, 0.9],
                frame_id=2,
                embeddings=[_E_B, _E_A],
            ),
        )
        det_indices = out.det_indices.tolist()
        row = det_indices.index(1)
        return int(out.track_ids[row])

    def test_sort_iou_only_loses_the_identity(self):
        cfg = SortConfig(lifecycle=LifecycleConfig(min_hits=1, tentative_max_age=1, max_age=5))
        assert self._run(SortTracker(cfg)) != 1

    def test_strongsort_appearance_recovers_the_identity(self):
        cfg = StrongSortConfig(
            lifecycle=LifecycleConfig(min_hits=1, tentative_max_age=1, max_age=5),
            gmc_enabled=False,
        )
        assert cfg.appearance_weight == pytest.approx(0.75)
        assert self._run(StrongSortTracker(cfg)) == 1


class TestAppearanceDiscrimination:
    """At a high weight, a disagreeing embedding can drop a perfect-IoU match.

    The convex blend raises a disagreeing pair's cost above ``match_threshold``
    and drops it. SORT (IoU only) keeps the same pair.
    """

    @staticmethod
    def _run(tracker: BaseTracker) -> list[int]:
        # Frame 0 establishes track 1 with appearance E_A. Frame 1 offers a
        # perfect-IoU detection (cost 0 on geometry) but with the opposite
        # embedding E_B, so appearance strongly disagrees.
        tracker.update(_dets([[50, 50, 90, 90]], [0.9], frame_id=0, embeddings=[_E_A]))
        out = tracker.update(_dets([[50, 50, 90, 90]], [0.9], frame_id=1, embeddings=[_E_B]))
        return out.track_ids.tolist()

    def test_high_weight_appearance_drops_a_perfect_iou_match(self):
        # fused = 0.25 * 0.0 + 0.75 * 1.0 = 0.75 > match_threshold (0.7): dropped,
        # so the detection spawns a fresh id rather than continuing track 1.
        cfg = StrongSortConfig(
            lifecycle=LifecycleConfig(min_hits=1, tentative_max_age=1, max_age=5),
            appearance_weight=0.75,
            gmc_enabled=False,
        )
        assert self._run(StrongSortTracker(cfg)) == [2]

    def test_sort_keeps_the_perfect_iou_match(self):
        cfg = SortConfig(lifecycle=LifecycleConfig(min_hits=1, tentative_max_age=1, max_age=5))
        assert self._run(SortTracker(cfg)) == [1]


class TestNoEmbeddings:
    def test_strongsort_falls_back_to_iou_without_embeddings(self):
        cfg = StrongSortConfig(lifecycle=LifecycleConfig(min_hits=1, tentative_max_age=1), gmc_enabled=False)
        tracker = StrongSortTracker(cfg)
        tracker.update(_dets([[10, 10, 50, 50]], [0.9], frame_id=0))
        out = tracker.update(_dets([[12, 12, 52, 52]], [0.9], frame_id=1))
        assert out.track_ids.tolist() == [1]


class TestGalleryLifecycle:
    def test_gallery_created_on_spawn_and_dropped_on_removal(self):
        cfg = StrongSortConfig(lifecycle=LifecycleConfig(min_hits=1, tentative_max_age=1, max_age=1), gmc_enabled=False)
        tracker = StrongSortTracker(cfg)
        tracker.update(_dets([[10, 10, 50, 50]], [0.9], frame_id=0, embeddings=[_E_A]))
        assert set(tracker._appearance) == {1}
        for f in range(1, 4):
            tracker.update(_dets([], [], frame_id=f, embeddings=[]))
        assert tracker._appearance == {}

    def test_reset_clears_galleries_and_warps(self):
        cfg = StrongSortConfig(lifecycle=LifecycleConfig(min_hits=1))
        tracker = StrongSortTracker(cfg)
        tracker.update(_dets([[10, 10, 50, 50]], [0.9], frame_id=0, embeddings=[_E_A]))
        tracker.set_frame_warp(np.eye(2, 3, dtype=np.float32))
        tracker.reset()
        assert tracker._appearance == {}
        assert tracker._pending_warp is None

    def test_each_gallery_is_keyed_to_the_right_detection(self):
        cfg = StrongSortConfig(lifecycle=LifecycleConfig(min_hits=1), gmc_enabled=False)
        tracker = StrongSortTracker(cfg)
        out = tracker.update(
            _dets([[0, 0, 20, 20], [200, 200, 240, 240]], [0.9, 0.9], frame_id=0, embeddings=[_E_A, _E_B]),
        )
        assert out.track_ids.tolist() == [1, 2]
        assert float(tracker._appearance[1].distance(_E_A[None, :])[0]) == pytest.approx(0.0, abs=1e-5)
        assert float(tracker._appearance[1].distance(_E_B[None, :])[0]) == pytest.approx(1.0, abs=1e-5)
        assert float(tracker._appearance[2].distance(_E_B[None, :])[0]) == pytest.approx(0.0, abs=1e-5)


class TestWarpBoxes:
    """The GMC warp application is a pure box transform, tested without video."""

    def test_pure_translation(self):
        warp = np.array([[1.0, 0.0, 10.0], [0.0, 1.0, -5.0]], dtype=np.float32)
        boxes = np.array([[0.0, 0.0, 10.0, 10.0]], dtype=np.float32)
        out = StrongSortTracker._warp_boxes(boxes, warp)
        np.testing.assert_allclose(out, [[10.0, -5.0, 20.0, 5.0]], atol=1e-5)

    def test_pure_scale_about_origin(self):
        warp = np.array([[2.0, 0.0, 0.0], [0.0, 2.0, 0.0]], dtype=np.float32)
        boxes = np.array([[1.0, 1.0, 3.0, 3.0]], dtype=np.float32)
        out = StrongSortTracker._warp_boxes(boxes, warp)
        np.testing.assert_allclose(out, [[2.0, 2.0, 6.0, 6.0]], atol=1e-5)

    def test_pure_rotation_moves_center_but_preserves_size(self):
        # 90-degree rotation about origin: center (1, 2) -> (-2, 1); w=2, h=4 unchanged.
        warp = np.array([[0.0, -1.0, 0.0], [1.0, 0.0, 0.0]], dtype=np.float32)
        boxes = np.array([[0.0, 0.0, 2.0, 4.0]], dtype=np.float32)
        out = StrongSortTracker._warp_boxes(boxes, warp)
        np.testing.assert_allclose(out, [[-3.0, -1.0, -1.0, 3.0]], atol=1e-5)
        # Width and height are exactly preserved under pure rotation.
        assert out[0, 2] - out[0, 0] == pytest.approx(2.0)
        assert out[0, 3] - out[0, 1] == pytest.approx(4.0)

    def test_repeated_rotation_does_not_grow_the_box(self):
        # Regression: feeding the warped box back under sustained rotation must
        # not inflate it.
        warp = _rotation_warp(np.deg2rad(0.5))
        boxes = np.array([[100.0, 100.0, 140.0, 220.0]], dtype=np.float32)  # 40 x 120
        area0 = 40.0 * 120.0
        for _ in range(120):
            boxes = StrongSortTracker._warp_boxes(boxes, warp)
        area = float((boxes[0, 2] - boxes[0, 0]) * (boxes[0, 3] - boxes[0, 1]))
        assert area == pytest.approx(area0, rel=1e-4)

    def test_empty_input(self):
        out = StrongSortTracker._warp_boxes(np.empty((0, 4), dtype=np.float32), np.eye(2, 3, dtype=np.float32))
        assert out.shape == (0, 4)

    def test_apply_gmc_under_sustained_rotation_keeps_area_bounded(self):
        # The reported failure path: _apply_gmc writes the warped box back onto
        # track.bbox, so the next frame warps an already-warped box. Loop it.
        cfg = StrongSortConfig(lifecycle=LifecycleConfig(min_hits=1), gmc_enabled=True)
        tracker = StrongSortTracker(cfg)
        tracker.update(_dets([[100.0, 100.0, 140.0, 220.0]], [0.9], frame_id=0))
        box0 = tracker._tracks[1].bbox.copy()
        area0 = float((box0[2] - box0[0]) * (box0[3] - box0[1]))
        warp = _rotation_warp(np.deg2rad(0.5))
        for _ in range(120):
            tracker._apply_gmc(warp)
        box = tracker._tracks[1].bbox
        area = float((box[2] - box[0]) * (box[3] - box[1]))
        assert area == pytest.approx(area0, rel=1e-4)


class TestGmcRecovery:
    """A camera pan that breaks IoU is recovered once the predicted box is warped."""

    @staticmethod
    def _run(*, gmc_enabled: bool) -> list[int]:
        cfg = StrongSortConfig(
            lifecycle=LifecycleConfig(min_hits=1, tentative_max_age=1, max_age=5), gmc_enabled=gmc_enabled
        )
        tracker = StrongSortTracker(cfg)
        tracker.update(_dets([[50, 50, 90, 90]], [0.9], frame_id=0))
        # Camera pans right by 40px: the same object is detected 40px to the right,
        # so its predicted box no longer overlaps the detection on IoU alone.
        tracker.set_frame_warp(np.array([[1.0, 0.0, 40.0], [0.0, 1.0, 0.0]], dtype=np.float32))
        out = tracker.update(_dets([[90, 50, 130, 90]], [0.9], frame_id=1))
        return out.track_ids.tolist()

    def test_without_gmc_the_pan_breaks_the_track(self):
        assert self._run(gmc_enabled=False) == [2]

    def test_with_gmc_the_warped_prediction_keeps_the_id(self):
        assert self._run(gmc_enabled=True) == [1]

    def test_warp_is_consumed_once_per_frame(self):
        cfg = StrongSortConfig(lifecycle=LifecycleConfig(min_hits=1), gmc_enabled=True)
        tracker = StrongSortTracker(cfg)
        tracker.set_frame_warp(np.eye(2, 3, dtype=np.float32))
        tracker.update(_dets([[50, 50, 90, 90]], [0.9], frame_id=0))
        assert tracker._pending_warp is None


class TestNsaKalman:
    def test_scale_is_one_when_disabled(self):
        tracker = StrongSortTracker(StrongSortConfig(nsa_kalman=False))
        assert tracker._measurement_noise_scale(0.9) == pytest.approx(1.0)

    def test_scale_is_one_minus_score_when_enabled(self):
        tracker = StrongSortTracker(StrongSortConfig(nsa_kalman=True))
        assert tracker._measurement_noise_scale(0.7) == pytest.approx(0.3)

    def test_scale_is_floored_for_near_certain_detections(self):
        tracker = StrongSortTracker(StrongSortConfig(nsa_kalman=True))
        assert tracker._measurement_noise_scale(1.0) == pytest.approx(StrongSortTracker._NSA_NOISE_FLOOR)

    def test_smaller_noise_scale_trusts_the_measurement_more(self):
        # NSA-Kalman relies on this filter property: a smaller measurement-noise
        # scale pulls the posterior mean closer to the observation.
        kf = KalmanFilter()
        mean, cov = kf.initiate(np.array([10.0, 10.0, 1.0, 40.0]))
        mean, cov = kf.predict(mean, cov)
        measurement = np.array([20.0, 20.0, 1.0, 40.0])
        loose, _ = kf.update(mean, cov, measurement, measurement_noise_scale=1.0)
        tight, _ = kf.update(mean, cov, measurement, measurement_noise_scale=0.1)
        assert abs(tight[0] - measurement[0]) < abs(loose[0] - measurement[0])

    @staticmethod
    def _posterior_mean(*, nsa_kalman: bool) -> np.ndarray:
        cfg = StrongSortConfig(lifecycle=LifecycleConfig(min_hits=1), gmc_enabled=False, nsa_kalman=nsa_kalman)
        tracker = StrongSortTracker(cfg)
        tracker.update(_dets([[50, 50, 90, 90]], [0.95], frame_id=0))
        # A moderate-confidence, displaced detection that still overlaps enough to
        # match track 1 (center 78); NSA scales its R by 1 - 0.5.
        tracker.update(_dets([[58, 58, 98, 98]], [0.5], frame_id=1))
        return tracker._kalman_states[1][0].copy()

    def test_nsa_changes_the_update_outcome_end_to_end(self):
        baseline = self._posterior_mean(nsa_kalman=False)
        nsa = self._posterior_mean(nsa_kalman=True)
        # NSA (score 0.5 -> R * 0.5) trusts the observation more, so the posterior
        # center lands nearer the measured center (78) than the default filter.
        assert not np.allclose(baseline, nsa)
        assert abs(nsa[0] - 78.0) < abs(baseline[0] - 78.0)
