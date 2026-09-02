# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Unit + integration tests for the BoT-SORT tracker and its config."""

from __future__ import annotations

import numpy as np
import pytest

import getitrack.algorithms  # noqa: F401  -> registers BoT-SORT
from getitrack.algorithms import BotSortTracker, ByteTrackTracker
from getitrack.algorithms.configs.botsort import BotSortConfig
from getitrack.algorithms.configs.bytetrack import ByteTrackConfig
from getitrack.config import AlgorithmType, LifecycleConfig, TrackerConfig
from getitrack.core.base import BaseTracker
from getitrack.core.detection import Detections
from getitrack.core.registry import resolve_tracker_config

_E_A = np.array([1.0, 0.0], dtype=np.float32)
_E_B = np.array([0.0, 1.0], dtype=np.float32)


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
    def test_from_config_dispatches_to_botsort(self):
        tracker = BaseTracker.from_config(BotSortConfig())
        assert isinstance(tracker, BotSortTracker)

    def test_resolve_dispatches_on_algorithm_key(self):
        resolved = resolve_tracker_config({"algorithm": "botsort", "appearance_weight": 0.4})
        assert isinstance(resolved, BotSortConfig)
        assert resolved.appearance_weight == pytest.approx(0.4)

    def test_algorithm_is_pinned(self):
        assert BotSortConfig().algorithm == AlgorithmType.BOTSORT

    def test_yaml_round_trip(self, tmp_path):
        cfg = BotSortConfig(
            appearance_weight=0.5,
            gallery_size=17,
            appearance_threshold=0.3,
            use_ema=False,
            lifecycle=LifecycleConfig(max_age=42),
        )
        path = tmp_path / "botsort.yaml"
        cfg.to_yaml(path)
        assert TrackerConfig.from_yaml(path) == cfg

    def test_reid_section_defaults(self):
        cfg = BotSortConfig()
        assert cfg.reid.enabled is False
        assert cfg.reid.model_path is None
        assert cfg.reid.input_size == (256, 128)

    def test_extends_bytetrack_parameters(self):
        # BoT-SORT inherits the ByteTrack knobs (e.g. the high/low split).
        assert BotSortConfig().high_score_threshold == pytest.approx(0.5)


class TestReidProviderProperty:
    def test_provider_is_none_when_reid_disabled(self):
        assert BotSortTracker(BotSortConfig()).reid_provider is None


class TestAppearanceRecovery:
    """Appearance recovers an identity across an occlusion that IoU alone drops."""

    @staticmethod
    def _run(tracker: BaseTracker) -> int:
        # Frame 0: object A at a box, with appearance e_A -> track id 1.
        tracker.update(_dets([[50, 50, 90, 90]], [0.9], frame_id=0, embeddings=[_E_A]))
        # Frame 1: A occluded (no detection) -> track goes LOST.
        tracker.update(_dets([], [], frame_id=1, embeddings=[]))
        # Frame 2: a distractor (e_B) sits exactly on A's coasted box (IoU 1.0),
        # while the true A (e_A) reappears slightly displaced (IoU ~0.68). Both
        # overlap above the DEFAULT appearance_iou_floor (0.5), so appearance
        # applies to both and must disambiguate them.
        out = tracker.update(
            _dets(
                [[50, 50, 90, 90], [46, 46, 86, 86]],
                [0.9, 0.9],
                frame_id=2,
                embeddings=[_E_B, _E_A],
            ),
        )
        # The true-A detection is input row 1; return the id it received.
        assert out.det_indices is not None
        det_indices = out.det_indices.tolist()
        row = det_indices.index(1)
        return int(out.track_ids[row])

    def test_bytetrack_iou_only_loses_the_identity(self):
        # IoU-only association latches id 1 onto the higher-overlap distractor,
        # so the real A gets a fresh id.
        cfg = ByteTrackConfig(lifecycle=LifecycleConfig(min_hits=1, tentative_max_age=1, max_age=5))
        assert self._run(ByteTrackTracker(cfg)) != 1

    def test_botsort_appearance_recovers_the_identity_under_default_floor(self):
        # Default appearance_iou_floor (0.5); only appearance_weight is raised for
        # a robust margin. Appearance discriminates the distractor from true A.
        cfg = BotSortConfig(
            lifecycle=LifecycleConfig(min_hits=1, tentative_max_age=1, max_age=5),
            appearance_weight=0.5,
        )
        assert cfg.appearance_iou_floor == pytest.approx(0.5)
        assert self._run(BotSortTracker(cfg)) == 1


class TestModerateOverlapRecovery:
    """A below-floor same-identity reappearance is still recovered on IoU.

    Pairs below the appearance floor fall back to the IoU cost, so the id is
    preserved under the default config.
    """

    @staticmethod
    def _run(tracker: BaseTracker) -> list[int]:
        tracker.update(_dets([[50, 50, 90, 90]], [0.9], frame_id=0, embeddings=[_E_A]))
        tracker.update(_dets([], [], frame_id=1, embeddings=[]))
        # Reappears at IoU ~0.32 (below the default 0.5 floor) with the SAME e_A.
        out = tracker.update(_dets([[62, 62, 102, 102]], [0.9], frame_id=2, embeddings=[_E_A]))
        return out.track_ids.tolist()

    def test_botsort_recovers_below_floor_reappearance_under_default_config(self):
        cfg = BotSortConfig(lifecycle=LifecycleConfig(min_hits=1, tentative_max_age=1, max_age=5))
        # Default floor; no appearance sidestep. The id is preserved, not re-spawned.
        assert self._run(BotSortTracker(cfg)) == [1]

    def test_matches_the_bytetrack_baseline(self):
        cfg = ByteTrackConfig(lifecycle=LifecycleConfig(min_hits=1, tentative_max_age=1, max_age=5))
        assert self._run(ByteTrackTracker(cfg)) == [1]


class TestGalleryLifecycle:
    def test_gallery_created_on_spawn_and_dropped_on_removal(self):
        cfg = BotSortConfig(lifecycle=LifecycleConfig(min_hits=1, tentative_max_age=1, max_age=1))
        tracker = BotSortTracker(cfg)
        tracker.update(_dets([[10, 10, 50, 50]], [0.9], frame_id=0, embeddings=[_E_A]))
        assert set(tracker._appearance) == {1}
        # Three empty frames age the track out: ACTIVE -> LOST -> LOST -> REMOVED.
        for f in range(1, 4):
            tracker.update(_dets([], [], frame_id=f, embeddings=[]))
        assert tracker._appearance == {}

    def test_reset_clears_galleries(self):
        cfg = BotSortConfig(lifecycle=LifecycleConfig(min_hits=1))
        tracker = BotSortTracker(cfg)
        tracker.update(_dets([[10, 10, 50, 50]], [0.9], frame_id=0, embeddings=[_E_A]))
        tracker.reset()
        assert tracker._appearance == {}

    def test_low_score_hits_do_not_pollute_gallery(self):
        # A low-score detection recovers the track but must not enter the gallery.
        cfg = BotSortConfig(lifecycle=LifecycleConfig(min_hits=1, tentative_max_age=1), high_score_threshold=0.5)
        tracker = BotSortTracker(cfg)
        tracker.update(_dets([[10, 10, 50, 50]], [0.9], frame_id=0, embeddings=[_E_A]))
        tracker.update(_dets([[12, 12, 52, 52]], [0.3], frame_id=1, embeddings=[_E_B]))
        # Only the initial high-score e_A descriptor was admitted.
        assert len(tracker._appearance[1]) == 1


class TestMultiSpawn:
    def test_each_gallery_is_keyed_to_the_right_detection(self):
        # Two objects spawn in the same (first) frame; each track's gallery must
        # hold its own detection's descriptor, verifying the _next_id peek in
        # _spawn keys galleries correctly.
        cfg = BotSortConfig(lifecycle=LifecycleConfig(min_hits=1))
        tracker = BotSortTracker(cfg)
        out = tracker.update(
            _dets(
                [[0, 0, 20, 20], [200, 200, 240, 240]],
                [0.9, 0.9],
                frame_id=0,
                embeddings=[_E_A, _E_B],
            ),
        )
        # Row 0 (e_A) -> id 1, row 1 (e_B) -> id 2.
        assert out.track_ids.tolist() == [1, 2]
        # Track 1's gallery matches e_A and rejects e_B, and vice-versa.
        assert float(tracker._appearance[1].distance(_E_A[None, :])[0]) == pytest.approx(0.0, abs=1e-5)
        assert float(tracker._appearance[1].distance(_E_B[None, :])[0]) == pytest.approx(1.0, abs=1e-5)
        assert float(tracker._appearance[2].distance(_E_B[None, :])[0]) == pytest.approx(0.0, abs=1e-5)
        assert float(tracker._appearance[2].distance(_E_A[None, :])[0]) == pytest.approx(1.0, abs=1e-5)


class TestReidConfigWarning:
    def test_enabled_without_model_source_warns(self):
        from getitrack.config import ReIDConfig

        with pytest.warns(UserWarning, match="neither model_name nor model_path"):
            ReIDConfig(enabled=True)

    def test_botsort_config_with_enabled_reid_and_no_source_warns(self):
        from getitrack.config import ReIDConfig

        with pytest.warns(UserWarning, match="neither model_name nor model_path"):
            BotSortConfig(reid=ReIDConfig(enabled=True))

    def test_no_warning_when_model_name_set(self):
        import warnings

        from getitrack.config import ReIDConfig

        with warnings.catch_warnings():
            warnings.simplefilter("error")
            ReIDConfig(enabled=True, model_name="osnet_x1_0")

    def test_no_warning_when_disabled(self):
        import warnings

        from getitrack.config import ReIDConfig

        with warnings.catch_warnings():
            warnings.simplefilter("error")
            ReIDConfig(enabled=False)


class TestNoEmbeddings:
    def test_botsort_falls_back_to_iou_without_embeddings(self):
        # With no embeddings supplied, BoT-SORT behaves like ByteTrack.
        cfg = BotSortConfig(lifecycle=LifecycleConfig(min_hits=1, tentative_max_age=1))
        tracker = BotSortTracker(cfg)
        tracker.update(_dets([[10, 10, 50, 50]], [0.9], frame_id=0))
        out = tracker.update(_dets([[12, 12, 52, 52]], [0.9], frame_id=1))
        assert out.track_ids.tolist() == [1]


class TestCameraMotion:
    @staticmethod
    def _seeded_tracker(box: list[float] | None = None) -> BotSortTracker:
        from getitrack.config import GMCConfig

        cfg = BotSortConfig(gmc=GMCConfig(enabled=True), lifecycle=LifecycleConfig(min_hits=1, tentative_max_age=1))
        tracker = BotSortTracker(cfg)
        tracker.update(_dets([box or [50, 50, 90, 90]], [0.9], frame_id=0))
        return tracker

    def test_cmc_is_none_when_gmc_disabled(self):
        tracker = BotSortTracker(BotSortConfig())
        assert tracker.cmc is None
        assert tracker.apply_camera_motion(np.zeros((20, 20, 3), dtype=np.uint8)) is None

    def test_cmc_built_when_enabled(self):
        from getitrack.config import GMCConfig
        from getitrack.motion.gmc import SparseOptFlowEstimator

        tracker = BotSortTracker(BotSortConfig(gmc=GMCConfig(enabled=True)))
        assert isinstance(tracker.cmc, SparseOptFlowEstimator)

    def test_apply_cmc_translates_predicted_boxes(self):
        tracker = self._seeded_tracker()
        before = tracker._tracks[1].bbox.copy()
        tracker._apply_cmc(np.array([[1, 0, 10], [0, 1, 5]], dtype=np.float32))
        after = tracker._tracks[1].bbox
        assert after == pytest.approx(before + np.array([10, 5, 10, 5]), abs=1e-3)

    def test_apply_cmc_scale_preserves_aspect_ratio(self):
        # A uniform zoom must scale width and height equally, leaving the aspect
        # ratio unchanged; the old kron(I4, R) transform scaled width by s**2.
        tracker = self._seeded_tracker([50, 50, 90, 130])  # w=40, h=80, aspect 0.5
        before = tracker._tracks[1].bbox.copy()
        w0, h0 = before[2] - before[0], before[3] - before[1]
        tracker._apply_cmc(np.array([[2, 0, 0], [0, 2, 0]], dtype=np.float32))
        after = tracker._tracks[1].bbox
        w1, h1 = after[2] - after[0], after[3] - after[1]
        assert h1 == pytest.approx(2 * h0, rel=1e-2)
        assert w1 == pytest.approx(2 * w0, rel=1e-2)
        assert (w1 / h1) == pytest.approx(w0 / h0, rel=1e-2)

    def test_apply_cmc_rotation_keeps_height_and_aspect(self):
        # A pure rotation (det == 1) must leave height and aspect ratio intact
        # and never drive them negative; only position rotates.
        tracker = self._seeded_tracker([50, 50, 90, 130])
        before = tracker._tracks[1].bbox.copy()
        w0, h0 = before[2] - before[0], before[3] - before[1]
        theta = np.deg2rad(10)
        cos, sin = np.cos(theta), np.sin(theta)
        tracker._apply_cmc(np.array([[cos, -sin, 0], [sin, cos, 0]], dtype=np.float32))
        after = tracker._tracks[1].bbox
        w1, h1 = after[2] - after[0], after[3] - after[1]
        assert w1 > 0
        assert h1 == pytest.approx(h0, rel=1e-3)
        assert (w1 / h1) == pytest.approx(w0 / h0, rel=1e-3)

    def test_predict_all_consumes_pending_warp(self):
        tracker = self._seeded_tracker()
        left_before = float(tracker._tracks[1].bbox[0])
        tracker._pending_warp = np.array([[1, 0, 12], [0, 1, 0]], dtype=np.float32)
        tracker._predict_all()
        assert tracker._pending_warp is None
        # The staged +12 x shift moved the predicted box to the right.
        assert float(tracker._tracks[1].bbox[0]) > left_before + 8
