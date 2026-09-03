# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Deep OC-SORT: OC-SORT association augmented with appearance (ReID).

Extends OC-SORT's observation-centric association with an appearance stage. Each
track keeps a bounded appearance gallery
(`getitrack.reid.gallery.AppearanceGallery`), and the first (OCM) association
fuses a cosine appearance cost with the IoU cost under an IoU proximity gate
before the momentum term is applied.

Each matched high-confidence detection feeds its descriptor into the track's
gallery with the detection score as the confidence; the gallery's EMA descriptor
is confidence-scaled by that score.

The first-pass validity gate uses the pure IoU cost. `fuse_appearance_cost`
falls back to the plain IoU cost below the IoU floor or for tracks without
appearance features, so Deep OC-SORT reduces to OC-SORT when ReID is disabled or
no embeddings are supplied.

Appearance features come from ``Detections.embeddings``, populated by the caller
or by the ReID provider exposed as `DeepOcSortTracker.reid_provider` when
``reid`` is configured.

Reference: Maggiolino et al., "Deep OC-SORT: Multi-Pedestrian Tracking by
Adaptive Re-Identification" (2023).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, cast

import numpy as np

from getitrack.algorithms.configs.deepocsort import DeepOcSortConfig
from getitrack.algorithms.ocsort import OCSortTracker, _direction_cost
from getitrack.core.registry import register_algorithm
from getitrack.matching import fuse_appearance_cost, linear_assignment
from getitrack.reid.gallery import AppearanceGallery

if TYPE_CHECKING:
    from getitrack.config import LifecycleConfig
    from getitrack.core.detection import Detections
    from getitrack.reid.base import ReIDProvider


@register_algorithm("deepocsort", config=DeepOcSortConfig)
class DeepOcSortTracker(OCSortTracker):
    """Deep OC-SORT multi-object tracker (OC-SORT + appearance gallery).

    Maintains OC-SORT's Kalman + observation-centric state and, in parallel, one
    `AppearanceGallery` per track keyed by track id. Matched high-confidence
    detections feed their descriptor into the gallery; the first (OCM)
    association fuses the resulting appearance cost with IoU before the momentum
    term is applied.
    """

    algorithm_name: ClassVar[str] = "deepocsort"

    def __init__(self, config: DeepOcSortConfig) -> None:
        super().__init__(config)
        self._appearance: dict[int, AppearanceGallery] = {}
        self._reid_provider: ReIDProvider | None = None

    @property
    def _cfg(self) -> DeepOcSortConfig:
        """Return ``config`` narrowed to the Deep OC-SORT type."""
        return cast("DeepOcSortConfig", self.config)

    def reset(self) -> None:  # noqa: D102
        super().reset()
        self._appearance.clear()

    @property
    def reid_provider(self) -> ReIDProvider | None:
        """Lazily-built ReID provider from ``config.reid``, or None if disabled.

        Fills ``Detections.embeddings`` before `update`::

            dets = replace(dets, embeddings=tracker.reid_provider.extract(frame, dets.bboxes))

        The backend (torch / OpenVINO / torchreid) is imported on first access.
        """
        if self._reid_provider is None and self._cfg.reid.enabled:
            from getitrack.reid.factory import build_reid_provider

            self._reid_provider = build_reid_provider(self._cfg.reid)
        return self._reid_provider

    def _associate_first(self, track_ids: list[int], dets: Detections) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """First pass: IoU fused with appearance, minus the OCM momentum, gated on IoU.

        Blends a cosine appearance cost into the IoU cost via
        `fuse_appearance_cost` before subtracting the momentum bonus. The
        validity gate uses the pure IoU cost. Appearance applies only when
        detection embeddings and at least one non-empty gallery are present.
        """
        if not track_ids or len(dets) == 0:
            return self._empty_association(len(track_ids), len(dets))
        track_boxes = np.stack([self._tracks[track_id].bbox for track_id in track_ids], axis=0)
        # Association distance selected by config (defaults to IoU).
        iou_cost = self._distance(track_boxes, dets.bboxes)

        fused_cost = iou_cost
        if dets.embeddings is not None:
            appearance_cost = self._appearance_cost(track_ids, dets.embeddings)
            if appearance_cost is not None:
                fused_cost = fuse_appearance_cost(
                    iou_cost,
                    appearance_cost,
                    appearance_weight=self._cfg.appearance_weight,
                    iou_floor=self._cfg.appearance_iou_floor,
                )

        prev_boxes = np.stack([self._previous_observation(track_id) for track_id in track_ids], axis=0)
        velocities = np.stack(
            [v if (v := self._obs[track_id].velocity) is not None else np.zeros(2) for track_id in track_ids],
            axis=0,
        )
        valid = np.array([self._obs[track_id].velocity is not None for track_id in track_ids])
        momentum_bonus = _direction_cost(dets.bboxes, prev_boxes, velocities, valid, dets.scores, self.config.inertia)

        cost = fused_cost - momentum_bonus
        # Gate on the pure IoU cost.
        invalid = iou_cost > self.config.match_threshold
        class_mismatch = self._class_mismatch(track_ids, dets)
        if class_mismatch is not None:
            invalid = invalid | class_mismatch
        cost[invalid] = self._INVALID_COST
        return linear_assignment(cost, self._MATCH_COST_CEILING)

    def _appearance_cost(self, track_ids: list[int], det_embeddings: np.ndarray) -> np.ndarray | None:
        """Build the ``(T, N)`` appearance cost, or None if no gallery is usable.

        Tracks without a usable gallery get an all-``NaN`` row, which
        `fuse_appearance_cost` treats as absent appearance information.
        """
        n = det_embeddings.shape[0]
        rows: list[np.ndarray] = []
        usable = False
        for track_id in track_ids:
            gallery = self._appearance.get(track_id)
            if gallery is None or gallery.is_empty:
                rows.append(np.full((n,), np.nan, dtype=np.float32))
            else:
                rows.append(gallery.distance(det_embeddings))
                usable = True
        if not usable:
            return None
        return np.stack(rows, axis=0).astype(np.float32)

    def _apply_hit(
        self,
        track_id: int,
        dets: Detections,
        det_idx: int,
        lifecycle: LifecycleConfig,
        *,
        src_index: int,
    ) -> None:
        super()._apply_hit(track_id, dets, det_idx, lifecycle, src_index=src_index)
        if dets.embeddings is None:
            return
        score = float(dets.scores[det_idx])
        # Only high-confidence detections (> det_threshold) feed the gallery.
        if score > self.config.det_threshold:
            self._admit(track_id, dets.embeddings[det_idx], score)

    def _spawn_track(self, dets: Detections, det_idx: int, *, src_index: int) -> None:
        # super() assigns the id from _allocate_id(), i.e. the current _next_id;
        # capture it here before the increment.
        new_id = self._next_id
        super()._spawn_track(dets, det_idx, src_index=src_index)
        if dets.embeddings is not None:
            score = float(dets.scores[det_idx])
            if score > self.config.det_threshold:
                self._admit(new_id, dets.embeddings[det_idx], score)

    def _remove_track(self, track_id: int) -> None:
        super()._remove_track(track_id)
        self._appearance.pop(track_id, None)

    def _admit(self, track_id: int, feature: np.ndarray, score: float) -> None:
        """Feed a matched detection's descriptor into the track's gallery.

        The detection score is passed as the gallery's confidence for the EMA
        update.
        """
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
