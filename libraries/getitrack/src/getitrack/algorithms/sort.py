# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""SORT: single-stage IoU detection-to-track association.

Each frame, every track's Kalman state is advanced, detections above the
score floor are matched to the predicted boxes with a Hungarian assignment
on IoU cost, matched tracks are updated with their detection, unmatched
tracks record a miss, and each unmatched detection spawns a new track.

Tracks live in one ``_tracks`` dict keyed by id, with lifecycle state on each
`Track` and Kalman state on the tracker in `_kalman_states`. Matching is
class-aware when ``match_class_only`` is set.

Reference: Bewley et al., "Simple Online and Realtime Tracking" (ICIP 2016).
"""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING, ClassVar

import numpy as np

from getitrack.algorithms.configs.sort import SortConfig
from getitrack.core.base import BaseTracker
from getitrack.core.detection import Detections, TrackedDetections
from getitrack.core.registry import register_algorithm
from getitrack.core.track import Track, TrackState
from getitrack.matching import BaseDistanceMetric, linear_assignment
from getitrack.motion import KalmanFilter
from getitrack.utils import xyah_to_xyxy, xyxy_to_xyah

if TYPE_CHECKING:
    from getitrack.config import LifecycleConfig


@register_algorithm("sort", config=SortConfig)
class SortTracker(BaseTracker[SortConfig]):
    """SORT multi-object tracker.

    Single-stage association: all tracks are matched against the frame's
    detections on IoU cost between detection boxes and Kalman-predicted track
    boxes. Matched tracks are updated, unmatched tracks record a miss, and
    each unmatched detection spawns a new track. ``update`` returns the
    ACTIVE tracks for the frame.
    """

    algorithm_name: ClassVar[str] = "sort"

    _UNMATCHABLE_COST: ClassVar[np.float32] = np.nextafter(np.float32(1.0), np.float32(2.0))

    def __init__(self, config: SortConfig) -> None:
        super().__init__(config)
        self._kalman = KalmanFilter.from_config(config.motion)
        # Association distance selected by config; defaults to IoUDistance.
        self._distance: BaseDistanceMetric = BaseDistanceMetric.from_metric(config.distance_metric)
        self._tracks: dict[int, Track] = {}
        self._kalman_states: dict[int, tuple[np.ndarray, np.ndarray]] = {}
        self._first_frame_id: int | None = None
        # track_id -> row index into this frame's input Detections.
        self._frame_det_index: dict[int, int] = {}

    def reset(self) -> None:  # noqa: D102
        super().reset()
        self._tracks.clear()
        self._kalman_states.clear()
        self._first_frame_id = None
        self._frame_det_index.clear()

    def _update_impl(self, detections: Detections) -> TrackedDetections:
        """Run one SORT iteration and return the active set."""
        self._frame_id = detections.frame_id
        if self._first_frame_id is None:
            self._first_frame_id = detections.frame_id
        self._frame_det_index.clear()
        lifecycle = self.config.lifecycle

        kept_indices = np.flatnonzero(detections.scores > self.config.score_threshold)
        dets = detections.select(kept_indices)

        self._predict_all()
        track_ids = list(self._tracks)

        matches, unmatched_track_idx, unmatched_det_idx = self._associate(track_ids, dets)
        for track_pos, det_pos in matches:
            self._apply_hit(track_ids[track_pos], dets, det_pos, lifecycle, src_index=int(kept_indices[det_pos]))
        for i in unmatched_track_idx:
            self._tracks[track_ids[i]].mark_miss(lifecycle)
        for det_pos in unmatched_det_idx:
            self._spawn_track(dets, int(det_pos), src_index=int(kept_indices[det_pos]))

        for track_id in list(self._tracks):
            if self._tracks[track_id].should_remove:
                del self._tracks[track_id]
                self._kalman_states.pop(track_id, None)

        return self._compose_output(detections.frame_id)

    def _predict_all(self) -> None:
        """Advance every track's Kalman state and refresh its predicted box."""
        if not self._kalman_states:
            return
        track_ids = list(self._kalman_states)
        means = np.stack([self._kalman_states[track_id][0] for track_id in track_ids], axis=0)
        covs = np.stack([self._kalman_states[track_id][1] for track_id in track_ids], axis=0)
        # Unobserved tracks predict with zero height velocity.
        for i, track_id in enumerate(track_ids):
            if self._tracks[track_id].state != TrackState.ACTIVE:
                means[i, 7] = 0.0
        means, covs = self._kalman.multi_predict(means, covs)
        for i, track_id in enumerate(track_ids):
            self._kalman_states[track_id] = (means[i], covs[i])
            self._tracks[track_id].bbox = xyah_to_xyxy(means[i, :4][None, :])[0].astype(np.float32)

    def _associate(self, track_ids: list[int], dets: Detections) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Match tracks to detections on IoU cost gated by ``match_threshold``."""
        if not track_ids or len(dets) == 0:
            return (
                np.empty((0, 2), dtype=np.int64),
                np.arange(len(track_ids), dtype=np.int64),
                np.arange(len(dets), dtype=np.int64),
            )
        track_boxes = np.stack([self._tracks[track_id].bbox for track_id in track_ids], axis=0)
        cost = self._distance(track_boxes, dets.bboxes)
        if self.config.match_class_only:
            track_classes = np.array([self._tracks[track_id].class_id for track_id in track_ids])
            cost[track_classes[:, None] != dets.class_ids[None, :]] = self._UNMATCHABLE_COST
        return linear_assignment(cost, self.config.match_threshold)

    def _apply_hit(
        self,
        track_id: int,
        dets: Detections,
        det_idx: int,
        lifecycle: LifecycleConfig,
        *,
        src_index: int,
    ) -> None:
        """Record an observed detection: update the filter and advance the lifecycle."""
        track = self._tracks[track_id]
        bbox = dets.bboxes[det_idx]
        score = float(dets.scores[det_idx])
        track.mark_hit(bbox, score, lifecycle)
        self._frame_det_index[track_id] = src_index
        measurement = xyxy_to_xyah(bbox[None, :])[0]
        mean, covariance = self._kalman_states[track_id]
        self._kalman_states[track_id] = self._kalman.update(mean, covariance, measurement)

    def _spawn_track(self, dets: Detections, det_idx: int, *, src_index: int) -> None:
        """Create a new track from an unmatched detection."""
        track_id = self._allocate_id()
        bbox = dets.bboxes[det_idx].astype(np.float32)
        class_id = int(dets.class_ids[det_idx])
        score = float(dets.scores[det_idx])
        # Tracks activate immediately when min_hits <= 1 or on the first frame.
        skip_tentative = self.config.lifecycle.min_hits <= 1 or dets.frame_id == self._first_frame_id
        initial_state = TrackState.ACTIVE if skip_tentative else TrackState.TENTATIVE
        track = Track(
            track_id=track_id,
            class_id=class_id,
            bbox=bbox,
            score=score,
            state=initial_state,
            _start_frame=dets.frame_id,
        )
        self._tracks[track_id] = track
        self._frame_det_index[track_id] = src_index
        measurement = xyxy_to_xyah(bbox[None, :])[0]
        self._kalman_states[track_id] = self._kalman.initiate(measurement)

    def _compose_output(self, frame_id: int) -> TrackedDetections:
        """Emit the ACTIVE tracks for the frame."""
        active = [t for t in self._tracks.values() if t.state == TrackState.ACTIVE]
        if not active:
            empty = TrackedDetections.create_empty(frame_id=frame_id)
            return replace(empty, det_indices=np.empty((0,), dtype=np.int64))
        return TrackedDetections(
            bboxes=np.stack([t.bbox for t in active], axis=0).astype(np.float32),
            scores=np.array([t.score for t in active], dtype=np.float32),
            class_ids=np.array([t.class_id for t in active], dtype=np.int64),
            track_ids=np.array([t.track_id for t in active], dtype=np.int64),
            track_states=np.array([int(t.state) for t in active], dtype=np.int8),
            frame_id=frame_id,
            det_indices=np.array([self._frame_det_index.get(t.track_id, -1) for t in active], dtype=np.int64),
        )
