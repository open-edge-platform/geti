# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""BoT-SORT: ByteTrack association augmented with appearance (ReID).

Extends ByteTrack's two-stage detection-to-track association with an appearance
stage. Each confirmed track keeps a bounded appearance gallery
(`getitrack.reid.gallery.AppearanceGallery`), and the first association
(confirmed tracks vs high-score detections, including recovering LOST tracks)
fuses a cosine appearance cost with the IoU cost under an IoU proximity gate.
The low-score second stage stays IoU-only.

When ``gmc`` is enabled the tracker warps its predicted track states by the
estimated frame-to-frame camera motion before association. The caller feeds
frames to the estimator via `BotSortTracker.apply_camera_motion`.

Appearance features come from ``Detections.embeddings``, populated directly or
via the ReID provider exposed as `BotSortTracker.reid_provider` when ``reid`` is
configured.

Reference: Aharon et al., "BoT-SORT: Robust Associations Multi-Pedestrian
Tracking" (2022).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, cast

import numpy as np

from getitrack.algorithms.bytetrack import ByteTrackTracker
from getitrack.algorithms.configs.botsort import BotSortConfig
from getitrack.core.registry import register_algorithm
from getitrack.matching import fuse_appearance_cost, fuse_score, linear_assignment
from getitrack.reid.gallery import AppearanceGallery
from getitrack.utils import xyah_to_xyxy

if TYPE_CHECKING:
    from getitrack.config import LifecycleConfig
    from getitrack.core.detection import Detections, TrackedDetections
    from getitrack.motion.gmc import BaseMotionEstimator
    from getitrack.reid.base import ReIDProvider


@register_algorithm("botsort", config=BotSortConfig)
class BotSortTracker(ByteTrackTracker):
    """BoT-SORT multi-object tracker (ByteTrack + appearance gallery).

    Maintains ByteTrack's Kalman and lifecycle state alongside one
    `AppearanceGallery` per track, keyed by track id. High-confidence matched
    detections feed their descriptor into the gallery; the first association
    fuses the resulting appearance cost with IoU.
    """

    algorithm_name: ClassVar[str] = "botsort"

    def __init__(self, config: BotSortConfig) -> None:
        super().__init__(config)
        self._appearance: dict[int, AppearanceGallery] = {}
        self._reid_provider: ReIDProvider | None = None
        self._cmc: BaseMotionEstimator | None = None
        self._pending_warp: np.ndarray | None = None

    @property
    def _cfg(self) -> BotSortConfig:
        """Return ``config`` narrowed to the ``BotSortConfig`` type."""
        return cast("BotSortConfig", self.config)

    def reset(self) -> None:
        """Reset the base tracker, galleries, and camera-motion estimator state."""
        super().reset()
        self._appearance.clear()
        self._pending_warp = None
        if self._cmc is not None:
            self._cmc.reset()

    @property
    def reid_provider(self) -> ReIDProvider | None:
        """Lazily-built ReID provider from ``config.reid``, or None if disabled.

        Fill ``Detections.embeddings`` before `update`::

            dets = replace(dets, embeddings=tracker.reid_provider.extract(frame, dets.bboxes))

        The backend (torch / OpenVINO / torchreid) is imported on first access.
        """
        if self._reid_provider is None and self._cfg.reid.enabled:
            from getitrack.reid.factory import build_reid_provider

            self._reid_provider = build_reid_provider(self._cfg.reid)
        return self._reid_provider

    @property
    def cmc(self) -> BaseMotionEstimator | None:
        """Lazily-built camera-motion estimator from ``config.gmc``, or None if disabled."""
        if self._cmc is None and self._cfg.gmc.enabled:
            from getitrack.motion.gmc import BaseMotionEstimator

            self._cmc = BaseMotionEstimator.from_config(self._cfg.gmc)
        return self._cmc

    def apply_camera_motion(self, frame_bgr: np.ndarray) -> np.ndarray | None:
        """Estimate camera motion from ``frame_bgr`` and stage it for the next `update`.

        Call once per frame before `update` when GMC is enabled::

            tracker.apply_camera_motion(frame)
            out = tracker.update(dets)

        The staged warp is consumed and cleared during the next `update`'s
        prediction step. Returns the ``2x3`` affine, or None when GMC is disabled.
        """
        estimator = self.cmc
        if estimator is None:
            return None
        self._pending_warp = estimator.estimate(frame_bgr)
        return self._pending_warp

    def _predict_all(self) -> None:
        # Warp the just-predicted track states by the staged camera motion.
        # The warp is consumed once; a frame without a staged warp gets no
        # compensation.
        super()._predict_all()
        if self._pending_warp is not None:
            self._apply_cmc(self._pending_warp)
            self._pending_warp = None

    def _apply_cmc(self, warp: np.ndarray) -> None:
        """Transform every Kalman state (mean and covariance) by the affine ``warp``.

        The ``2x2`` linear part is applied blockwise to the 8-D state via
        ``kron(I4, R)`` and to the covariance; the translation is added to the
        position. The aspect component is scaled along with the position.
        """
        if not self._kalman_states:
            return
        linear = warp[:2, :2]
        translation = warp[:2, 2]
        block = np.kron(np.eye(4, dtype=np.float32), linear)
        tids = list(self._kalman_states)
        for tid in tids:
            mean, cov = self._kalman_states[tid]
            mean = block @ mean
            mean[:2] += translation
            cov = block @ cov @ block.T
            self._kalman_states[tid] = (mean, cov)
        boxes = xyah_to_xyxy(np.stack([self._kalman_states[tid][0][:4] for tid in tids], axis=0)).astype(np.float32)
        for i, tid in enumerate(tids):
            self._tracks[tid].bbox = boxes[i]

    def _update_impl(self, detections: Detections) -> TrackedDetections:
        tracked = super()._update_impl(detections)
        # Drop galleries of tracks the base tracker removed this frame.
        for tid in set(self._appearance) - set(self._tracks):
            del self._appearance[tid]
        return tracked

    def _associate(
        self,
        track_ids: list[int],
        dets: Detections,
        cost_limit: float,
        *,
        apply_fuse_score: bool,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Associate with IoU, appearance fusion (high stages), and class gating.

        Mirrors `ByteTrackTracker._associate` but blends an appearance cost into
        the IoU cost before score fusion. Appearance is applied only on the
        high-score stages (``apply_fuse_score`` is set) and only when detection
        embeddings and at least one non-empty gallery are available; the
        low-score second stage stays IoU-only.
        """
        if not track_ids or len(dets) == 0:
            return (
                np.empty((0, 2), dtype=np.int64),
                np.arange(len(track_ids), dtype=np.int64),
                np.arange(len(dets), dtype=np.int64),
            )
        track_boxes = np.stack([self._tracks[tid].bbox for tid in track_ids], axis=0)
        cost = self._distance(track_boxes, dets.bboxes)
        if apply_fuse_score and dets.embeddings is not None:
            appearance_cost = self._appearance_cost(track_ids, dets.embeddings)
            if appearance_cost is not None:
                cost = fuse_appearance_cost(
                    cost,
                    appearance_cost,
                    appearance_weight=self._cfg.appearance_weight,
                    iou_floor=self._cfg.appearance_iou_floor,
                )
        cls_mismatch: np.ndarray | None = None
        if self._cfg.match_class_only:
            track_classes = np.array([self._tracks[tid].class_id for tid in track_ids])
            cls_mismatch = track_classes[:, None] != dets.class_ids[None, :]
        if apply_fuse_score:
            cost = fuse_score(cost, dets.scores)
        if cls_mismatch is not None:
            cost[cls_mismatch] = self._UNMATCHABLE_COST
        return linear_assignment(cost, cost_limit)

    def _appearance_cost(self, track_ids: list[int], det_embeddings: np.ndarray) -> np.ndarray | None:
        """Build the ``(T, N)`` appearance cost, or None if no gallery is usable.

        Tracks without a usable gallery get an all-``NaN`` row, which
        `fuse_appearance_cost` treats as "no appearance information" and falls
        back to IoU for that track.
        """
        n = det_embeddings.shape[0]
        rows: list[np.ndarray] = []
        usable = False
        for tid in track_ids:
            gallery = self._appearance.get(tid)
            if gallery is None or gallery.is_empty:
                rows.append(np.full((n,), np.nan, dtype=np.float32))
            else:
                rows.append(gallery.distance(det_embeddings))
                usable = True
        if not usable:
            return None
        return np.stack(rows, axis=0).astype(np.float32)

    def _apply_hits(
        self,
        hits: list[tuple[int, int, int]],
        dets: Detections,
        lifecycle: LifecycleConfig,
    ) -> None:
        super()._apply_hits(hits, dets, lifecycle)
        if dets.embeddings is None or not hits:
            return
        for tid, di, _ in hits:
            score = float(dets.scores[di])
            if score >= self._cfg.high_score_threshold:
                self._admit(tid, dets.embeddings[di], score)

    def _spawn(self, dets: Detections, det_idx: int, *, src_index: int) -> None:
        # BaseTracker._allocate_id returns the current ``_next_id`` then
        # increments it, so the id this spawn assigns equals ``_next_id`` read
        # before super() runs.
        new_id = self._next_id
        super()._spawn(dets, det_idx, src_index=src_index)
        if dets.embeddings is not None:
            score = float(dets.scores[det_idx])
            if score >= self._cfg.high_score_threshold:
                self._admit(new_id, dets.embeddings[det_idx], score)

    def _admit(self, track_id: int, feature: np.ndarray, score: float) -> None:
        """Feed a matched detection's descriptor into the track's gallery."""
        gallery = self._appearance.get(track_id)
        if gallery is None:
            gallery = AppearanceGallery(
                gallery_size=self._cfg.gallery_size,
                use_ema=self._cfg.use_ema,
                ema_alpha=self._cfg.ema_alpha,
                admission_threshold=self._cfg.appearance_threshold,
            )
            self._appearance[track_id] = gallery
        gallery.update(feature, confidence=score)
