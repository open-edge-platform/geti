# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""StrongSORT: SORT with appearance (ReID), ECC GMC, and NSA-Kalman.

Extends SORT's single-stage IoU association and Kalman motion model with three
individually toggleable components:

- Appearance (ReID): each track keeps a bounded appearance gallery
  (`getitrack.reid.gallery.AppearanceGallery`); during association a cosine
  appearance cost is fused with the IoU cost under an IoU proximity gate. Outside
  the gate, or where a track has no appearance, the cell uses the plain IoU cost.

- ECC global motion compensation (GMC): when ``gmc_enabled`` is set, a per-frame
  2x3 affine warp supplied via `set_frame_warp` is applied to each track's
  Kalman-predicted box before association.

- NSA-Kalman: when ``nsa_kalman`` is set, the Kalman measurement noise is scaled
  by ``1 - score``.

Appearance features come from ``Detections.embeddings``, populated directly or via
`StrongSortTracker.reid_provider`. With no embeddings, no supplied GMC warp, and
``nsa_kalman`` off, StrongSORT reproduces plain SORT.

Reference: Du et al., "StrongSORT: Make DeepSORT Great Again" (IEEE TMM 2023).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, cast

import numpy as np

from getitrack.algorithms.configs.strongsort import StrongSortConfig
from getitrack.algorithms.sort import SortTracker
from getitrack.core.registry import register_algorithm
from getitrack.matching import fuse_appearance_cost, linear_assignment
from getitrack.reid.gallery import AppearanceGallery
from getitrack.utils import xyxy_to_xyah

if TYPE_CHECKING:
    from getitrack.config import LifecycleConfig
    from getitrack.core.detection import Detections, TrackedDetections
    from getitrack.reid.base import ReIDProvider


@register_algorithm("strongsort", config=StrongSortConfig)
class StrongSortTracker(SortTracker):
    """StrongSORT multi-object tracker (SORT + appearance + GMC + NSA-Kalman).

    Maintains SORT's Kalman + lifecycle state and, in parallel, one
    `AppearanceGallery` per track keyed by track id. Matched and newly spawned
    detections feed their descriptor into the gallery; the IoU association fuses
    the resulting appearance cost with IoU, an optional ECC warp compensates for
    camera motion before association, and an optional NSA-Kalman rule scales the
    measurement noise by detection confidence.
    """

    algorithm_name: ClassVar[str] = "strongsort"

    _NSA_NOISE_FLOOR: ClassVar[float] = 0.05
    """Lower bound on the NSA measurement-noise scale."""

    def __init__(self, config: StrongSortConfig) -> None:
        super().__init__(config)
        self._appearance: dict[int, AppearanceGallery] = {}
        self._reid_provider: ReIDProvider | None = None
        self._pending_warp: np.ndarray | None = None
        self._current_warp: np.ndarray | None = None

    @property
    def _cfg(self) -> StrongSortConfig:
        """Return the config narrowed to its StrongSORT type."""
        return cast("StrongSortConfig", self.config)

    def reset(self) -> None:  # noqa: D102
        super().reset()
        self._appearance.clear()
        self._pending_warp = None
        self._current_warp = None

    @property
    def reid_provider(self) -> ReIDProvider | None:
        """Lazily-built ReID provider from ``config.reid``, or None if disabled.

        Fill ``Detections.embeddings`` before `update`::

            dets = replace(dets, embeddings=tracker.reid_provider.extract(frame, dets.bboxes))
        """
        if self._reid_provider is None and self._cfg.reid.enabled:
            from getitrack.reid.factory import build_reid_provider

            self._reid_provider = build_reid_provider(self._cfg.reid)
        return self._reid_provider

    def set_frame_warp(self, warp: np.ndarray | None) -> None:
        """Register the ``(2, 3)`` GMC affine warp to apply on the next `update`.

        The warp maps previous-frame to current-frame pixel coordinates. It is
        consumed by the next `update` and then cleared. Passing ``None`` skips
        compensation for that frame, and the warp is ignored unless
        ``gmc_enabled`` is set.

        Args:
            warp: ``(2, 3)`` previous-to-current affine warp, or ``None``.
        """
        self._pending_warp = warp

    def _update_impl(self, detections: Detections) -> TrackedDetections:
        # Consume the pending warp before association.
        self._current_warp = self._pending_warp if self._cfg.gmc_enabled else None
        self._pending_warp = None
        tracked = super()._update_impl(detections)
        for track_id in set(self._appearance) - set(self._tracks):
            del self._appearance[track_id]
        return tracked

    def _predict_all(self) -> None:
        """Advance the Kalman states, then warp predicted boxes for camera motion."""
        super()._predict_all()
        if self._current_warp is not None:
            self._apply_gmc(self._current_warp)

    def _apply_gmc(self, warp: np.ndarray) -> None:
        """Warp every track's predicted box and Kalman mean position by ``warp``.

        Applies the affine ``warp`` to each track's predicted ``xyxy`` box and
        writes the result back onto both ``track.bbox`` and the Kalman mean's
        position/scale. Velocity and covariance are left unchanged.

        Args:
            warp: ``(2, 3)`` affine warp mapping previous-frame to current-frame
                coordinates.
        """
        for track_id, track in self._tracks.items():
            warped = self._warp_boxes(track.bbox[None, :], warp)[0]
            track.bbox = warped
            mean, covariance = self._kalman_states[track_id]
            mean = mean.copy()
            mean[:4] = xyxy_to_xyah(warped[None, :])[0]
            self._kalman_states[track_id] = (mean, covariance)

    @staticmethod
    def _warp_boxes(boxes: np.ndarray, warp: np.ndarray) -> np.ndarray:
        """Apply a ``(2, 3)`` affine warp to ``xyxy`` boxes.

        The box center is transformed by ``warp = [R | t]`` (a point ``p`` maps
        to ``R @ p + t``) and the width/height are scaled by the warp's isotropic
        scale factor ``sqrt(|det R|)``.

        Args:
            boxes: ``(N, 4)`` ``xyxy`` boxes.
            warp: ``(2, 3)`` affine matrix.

        Returns:
            ``(N, 4)`` float32 warped, axis-aligned ``xyxy`` boxes.
        """
        if boxes.size == 0:
            return boxes.astype(np.float32, copy=False)
        rot = warp[:, :2]
        trans = warp[:, 2]
        centers = (boxes[:, :2] + boxes[:, 2:]) * 0.5  # (N, 2)
        sizes = boxes[:, 2:] - boxes[:, :2]  # (N, 2) width, height
        scale = float(np.sqrt(abs(np.linalg.det(rot))))
        new_centers = centers @ rot.T + trans  # (N, 2)
        half = sizes * scale * 0.5
        return np.concatenate([new_centers - half, new_centers + half], axis=1).astype(np.float32)

    def _associate(self, track_ids: list[int], dets: Detections) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Match on IoU cost with appearance fusion, gated by ``match_threshold``.

        Like `SortTracker._associate` but blends a cosine appearance cost into the
        IoU cost (under the IoU proximity gate) when detection embeddings and at
        least one non-empty gallery are available. Outside the gate, or where a
        track has no appearance, the cell uses the plain IoU cost.

        Returns:
            ``(matches, unmatched_track_idx, unmatched_det_idx)`` index arrays.
        """
        if not track_ids or len(dets) == 0:
            return (
                np.empty((0, 2), dtype=np.int64),
                np.arange(len(track_ids), dtype=np.int64),
                np.arange(len(dets), dtype=np.int64),
            )
        track_boxes = np.stack([self._tracks[track_id].bbox for track_id in track_ids], axis=0)
        cost = self._distance(track_boxes, dets.bboxes)
        if dets.embeddings is not None:
            appearance_cost = self._appearance_cost(track_ids, dets.embeddings)
            if appearance_cost is not None:
                cost = fuse_appearance_cost(
                    cost,
                    appearance_cost,
                    appearance_weight=self._cfg.appearance_weight,
                    iou_floor=self._cfg.appearance_iou_floor,
                )
        if self.config.match_class_only:
            track_classes = np.array([self._tracks[track_id].class_id for track_id in track_ids])
            cost[track_classes[:, None] != dets.class_ids[None, :]] = self._UNMATCHABLE_COST
        return linear_assignment(cost, self.config.match_threshold)

    def _appearance_cost(self, track_ids: list[int], det_embeddings: np.ndarray) -> np.ndarray | None:
        """Build the ``(T, N)`` appearance cost, or None if no gallery is usable.

        Tracks without a usable gallery get an all-``NaN`` row.
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
        if dets.embeddings is not None:
            self._admit(track_id, dets.embeddings[det_idx], float(dets.scores[det_idx]))

    def _spawn_track(self, dets: Detections, det_idx: int, *, src_index: int) -> None:
        new_id = self._next_id
        super()._spawn_track(dets, det_idx, src_index=src_index)
        if dets.embeddings is not None:
            self._admit(new_id, dets.embeddings[det_idx], float(dets.scores[det_idx]))

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

    def _measurement_noise_scale(self, score: float) -> float:
        """Return the NSA-Kalman measurement-noise multiplier for a hit.

        With ``nsa_kalman`` off this is ``1.0``. When on it returns ``1 - score``
        floored at `_NSA_NOISE_FLOOR`.
        """
        if not self._cfg.nsa_kalman:
            return 1.0
        return max(1.0 - score, self._NSA_NOISE_FLOOR)
