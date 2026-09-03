# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Unit + integration tests for the Deep OC-SORT tracker and its config."""

from __future__ import annotations

import numpy as np
import pytest

import getitrack.algorithms  # noqa: F401  -> registers Deep OC-SORT
from getitrack.algorithms import DeepOcSortTracker, OCSortTracker
from getitrack.algorithms.configs.deepocsort import DeepOcSortConfig
from getitrack.algorithms.configs.ocsort import OCSortConfig
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


def _fast() -> LifecycleConfig:
    return LifecycleConfig(min_hits=1, tentative_max_age=1, max_age=5)


class TestConfigRegistry:
    def test_from_config_dispatches_to_deepocsort(self):
        tracker = BaseTracker.from_config(DeepOcSortConfig())
        assert isinstance(tracker, DeepOcSortTracker)

    def test_resolve_dispatches_on_algorithm_key(self):
        resolved = resolve_tracker_config({"algorithm": "deepocsort", "appearance_weight": 0.4})
        assert isinstance(resolved, DeepOcSortConfig)
        assert resolved.appearance_weight == pytest.approx(0.4)

    def test_algorithm_is_pinned(self):
        assert DeepOcSortConfig().algorithm == AlgorithmType.DEEPOCSORT

    def test_algorithm_mismatch_is_rejected(self):
        # The pinned ``Literal`` field rejects any other algorithm value.
        with pytest.raises(ValueError, match="algorithm"):
            DeepOcSortConfig(algorithm=AlgorithmType.OCSORT)

    def test_yaml_round_trip(self, tmp_path):
        cfg = DeepOcSortConfig(
            appearance_weight=0.5,
            gallery_size=17,
            appearance_threshold=0.3,
            use_ema=False,
            delta_t=2,
            lifecycle=LifecycleConfig(max_age=42),
        )
        path = tmp_path / "deepocsort.yaml"
        cfg.to_yaml(path)
        assert TrackerConfig.from_yaml(path) == cfg

    def test_reid_section_defaults(self):
        cfg = DeepOcSortConfig()
        assert cfg.reid.enabled is False
        assert cfg.reid.model_path is None
        assert cfg.reid.input_size == (256, 128)

    def test_extends_ocsort_parameters(self):
        # Deep OC-SORT inherits the OC-SORT knobs (e.g. the momentum lookback).
        cfg = DeepOcSortConfig()
        assert cfg.delta_t == 3
        assert cfg.inertia == pytest.approx(0.2)


class TestReidProviderProperty:
    def test_provider_is_none_when_reid_disabled(self):
        assert DeepOcSortTracker(DeepOcSortConfig()).reid_provider is None


class TestAppearanceRecovery:
    """Appearance recovers an identity that OC-SORT's motion+IoU alone drops.

    After a one-frame gap the track's predicted box overlaps two competing
    detections: a distractor sitting exactly on the prediction (higher IoU,
    wrong appearance) and the true identity nearby (lower IoU, right
    appearance). IoU alone binds the track to the distractor; appearance fusion
    rebinds it to the true identity.
    """

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

    def test_ocsort_iou_only_loses_the_identity(self):
        cfg = OCSortConfig(lifecycle=_fast())
        assert self._run(OCSortTracker(cfg)) != 1

    def test_deepocsort_appearance_recovers_the_identity(self):
        cfg = DeepOcSortConfig(lifecycle=_fast(), appearance_weight=0.5)
        assert cfg.appearance_iou_floor == pytest.approx(0.5)
        assert self._run(DeepOcSortTracker(cfg)) == 1


_REDUCTION_SEQ: list[tuple[list[list[float]], list[float]]] = [
    ([[10, 10, 50, 50], [200, 200, 240, 240]], [0.9, 0.9]),
    ([[16, 10, 56, 50], [206, 200, 246, 240]], [0.9, 0.9]),
    ([[22, 10, 62, 50]], [0.9]),
    ([[28, 10, 68, 50], [212, 200, 252, 240]], [0.9, 0.9]),
    ([], []),
    ([[34, 10, 74, 50], [218, 200, 258, 240]], [0.9, 0.9]),
]


class TestReducesToOcSort:
    """With ReID disabled / no embeddings, Deep OC-SORT == OC-SORT frame by frame."""

    def _drive(self, tracker: BaseTracker) -> list[tuple[list[int], list[int]]]:
        history: list[tuple[list[int], list[int]]] = []
        for f, (boxes, scores) in enumerate(_REDUCTION_SEQ):
            out = tracker.update(_dets(boxes, scores, frame_id=f))
            history.append((out.track_ids.tolist(), out.det_indices.tolist()))
        return history

    def test_no_embeddings_matches_ocsort(self):
        lifecycle = _fast()
        deep = self._drive(DeepOcSortTracker(DeepOcSortConfig(lifecycle=lifecycle)))
        plain = self._drive(OCSortTracker(OCSortConfig(lifecycle=lifecycle)))
        assert deep == plain

    def test_reid_disabled_and_no_gallery_is_populated(self):
        # No embeddings ever reach the galleries, so appearance never engages.
        tracker = DeepOcSortTracker(DeepOcSortConfig(lifecycle=_fast()))
        self._drive(tracker)
        assert tracker._appearance == {}


class TestBelowFloorInvariant:
    """Below the IoU floor, appearance is not fused and cannot reorder matches.

    After a gap the track's prediction overlaps two competitors, both below the
    appearance floor (IoU ~0.47 and ~0.32) but still IoU-matchable: a geometry
    winner (row 0, higher IoU) carrying the wrong embedding and a geometry loser
    (row 1, lower IoU) carrying the right one. Even at a high appearance weight,
    the track binds to the geometry winner exactly as OC-SORT would.
    """

    @staticmethod
    def _run(tracker: BaseTracker) -> dict[int, int]:
        tracker.update(_dets([[50, 50, 90, 90]], [0.9], frame_id=0, embeddings=[_E_A]))
        tracker.update(_dets([], [], frame_id=1, embeddings=[]))
        out = tracker.update(
            _dets(
                [[58, 58, 98, 98], [62, 62, 102, 102]],
                [0.9, 0.9],
                frame_id=2,
                embeddings=[_E_B, _E_A],
            ),
        )
        return {int(t): int(d) for t, d in zip(out.track_ids, out.det_indices, strict=True)}

    def test_deepocsort_does_not_reorder_below_floor(self):
        # appearance_weight=0.9 would flip the match to the _E_A box (row 1) if
        # appearance were (wrongly) fused below the floor; the track must stay on
        # the geometry winner (row 0).
        cfg = DeepOcSortConfig(lifecycle=_fast(), appearance_weight=0.9)
        assert cfg.appearance_iou_floor == pytest.approx(0.5)
        assert self._run(DeepOcSortTracker(cfg))[1] == 0

    def test_matches_the_ocsort_baseline(self):
        assert self._run(OCSortTracker(OCSortConfig(lifecycle=_fast())))[1] == 0


class TestGalleryLifecycle:
    def test_gallery_created_on_spawn_and_dropped_on_removal(self):
        cfg = DeepOcSortConfig(lifecycle=LifecycleConfig(min_hits=1, tentative_max_age=1, max_age=1))
        tracker = DeepOcSortTracker(cfg)
        tracker.update(_dets([[10, 10, 50, 50]], [0.9], frame_id=0, embeddings=[_E_A]))
        assert set(tracker._appearance) == {1}
        for f in range(1, 4):
            tracker.update(_dets([], [], frame_id=f, embeddings=[]))
        assert tracker._appearance == {}

    def test_reset_clears_galleries(self):
        cfg = DeepOcSortConfig(lifecycle=LifecycleConfig(min_hits=1))
        tracker = DeepOcSortTracker(cfg)
        tracker.update(_dets([[10, 10, 50, 50]], [0.9], frame_id=0, embeddings=[_E_A]))
        tracker.reset()
        assert tracker._appearance == {}

    def test_low_score_hits_do_not_pollute_gallery(self):
        # A BYTE-stage match below det_threshold must not feed the gallery.
        cfg = DeepOcSortConfig(lifecycle=LifecycleConfig(min_hits=1, tentative_max_age=2), use_byte=True)
        tracker = DeepOcSortTracker(cfg)
        tracker.update(_dets([[10, 10, 50, 50]], [0.9], frame_id=0, embeddings=[_E_A]))
        tracker.update(_dets([[12, 12, 52, 52]], [0.3], frame_id=1, embeddings=[_E_B]))
        assert len(tracker._appearance[1]) == 1


class TestMultiSpawn:
    def test_each_gallery_is_keyed_to_the_right_detection(self):
        cfg = DeepOcSortConfig(lifecycle=LifecycleConfig(min_hits=1))
        tracker = DeepOcSortTracker(cfg)
        out = tracker.update(
            _dets(
                [[0, 0, 20, 20], [200, 200, 240, 240]],
                [0.9, 0.9],
                frame_id=0,
                embeddings=[_E_A, _E_B],
            ),
        )
        assert out.track_ids.tolist() == [1, 2]
        assert float(tracker._appearance[1].distance(_E_A[None, :])[0]) == pytest.approx(0.0, abs=1e-5)
        assert float(tracker._appearance[1].distance(_E_B[None, :])[0]) == pytest.approx(1.0, abs=1e-5)
        assert float(tracker._appearance[2].distance(_E_B[None, :])[0]) == pytest.approx(0.0, abs=1e-5)
        assert float(tracker._appearance[2].distance(_E_A[None, :])[0]) == pytest.approx(1.0, abs=1e-5)


class TestReidConfigWarning:
    def test_deepocsort_config_with_enabled_reid_and_no_path_warns(self):
        from getitrack.config import ReIDConfig

        with pytest.warns(UserWarning, match="neither model_name nor model_path"):
            DeepOcSortConfig(reid=ReIDConfig(enabled=True))


class TestNoEmbeddings:
    def test_deepocsort_falls_back_to_iou_without_embeddings(self):
        cfg = DeepOcSortConfig(lifecycle=LifecycleConfig(min_hits=1, tentative_max_age=1))
        tracker = DeepOcSortTracker(cfg)
        tracker.update(_dets([[10, 10, 50, 50]], [0.9], frame_id=0))
        out = tracker.update(_dets([[12, 12, 52, 52]], [0.9], frame_id=1))
        assert out.track_ids.tolist() == [1]
