# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""High-Speed IOU Tracker (Bochinski et al., AVSS 2017).

Tracks greedily claim the highest-overlap remaining detection in insertion
order. Association uses only the last observation, with no motion prediction
or global assignment. An unmatched track ends immediately.

The reference returns complete trajectories offline. This streaming adapter
emits ACTIVE tracks once both minimum length and peak score are satisfied;
it does not retrospectively emit tentative observations.
"""

from __future__ import annotations

from typing import ClassVar

import numpy as np

from getitrack.algorithms.configs.iou import IOUConfig
from getitrack.core.base import BaseTracker
from getitrack.core.detection import Detections, TrackedDetections
from getitrack.core.registry import register_algorithm
from getitrack.core.track import Track, TrackState
from getitrack.matching.distance.base import iou_matrix


@register_algorithm("iou", config=IOUConfig)
class IOUTracker(BaseTracker[IOUConfig]):
    """Greedy IoU tracker with consecutive observations and peak-score confirmation."""

    algorithm_name: ClassVar[str] = "iou"

    def __init__(self, config: IOUConfig) -> None:
        super().__init__(config)
        self._tracks: dict[int, Track] = {}
        self._max_scores: dict[int, float] = {}
        self._frame_det_index: dict[int, int] = {}

    def reset(self) -> None:  # noqa: D102
        super().reset()
        self._tracks.clear()
        self._max_scores.clear()
        self._frame_det_index.clear()

    def _update_impl(self, detections: Detections) -> TrackedDetections:
        """Associate one frame and emit only confirmed, observed tracks."""
        self._frame_id = detections.frame_id
        self._frame_det_index.clear()
        kept_indices = np.flatnonzero(detections.scores >= self.config.score_threshold)
        dets = detections.select(kept_indices)
        available = np.ones(len(dets), dtype=bool)
        track_ids = list(self._tracks)
        if track_ids:
            boxes = np.stack([self._tracks[track_id].bbox for track_id in track_ids])
            overlaps = iou_matrix(boxes, dets.bboxes)
            for row, track_id in enumerate(track_ids):
                track = self._tracks[track_id]
                eligible = available.copy()
                if self.config.match_class_only:
                    eligible &= dets.class_ids == track.class_id
                candidates = np.flatnonzero(eligible)
                if len(candidates):
                    det_idx = int(candidates[np.argmax(overlaps[row, candidates])])
                    if overlaps[row, det_idx] >= self.config.iou_threshold:
                        track.mark_hit(dets.bboxes[det_idx], float(dets.scores[det_idx]), self.config.lifecycle)
                        self._max_scores[track_id] = max(self._max_scores[track_id], track.score)
                        self._confirm(track)
                        self._frame_det_index[track_id] = int(kept_indices[det_idx])
                        available[det_idx] = False
                        continue
                # IOU ends a trajectory at the first miss; it never coasts or recovers.
                del self._tracks[track_id]
                del self._max_scores[track_id]

        for det_idx in np.flatnonzero(available):
            track_id = self._allocate_id()
            track = Track(
                track_id=track_id,
                class_id=int(dets.class_ids[det_idx]),
                bbox=dets.bboxes[det_idx],
                score=float(dets.scores[det_idx]),
                _start_frame=detections.frame_id,
            )
            self._tracks[track_id] = track
            self._max_scores[track_id] = track.score
            self._frame_det_index[track_id] = int(kept_indices[det_idx])
            self._confirm(track)

        active = [track for track in self._tracks.values() if track.state == TrackState.ACTIVE]
        return self._compose_tracked_detections(
            active, [self._frame_det_index[track.track_id] for track in active], detections.frame_id
        )

    def _confirm(self, track: Track) -> None:
        """Require both sufficient observations and a sufficiently high peak score."""
        confirmed = track.hits >= self.config.lifecycle.min_hits and self._max_scores[track.track_id] >= float(
            np.float32(self.config.high_score_threshold)
        )
        track.state = TrackState.ACTIVE if confirmed else TrackState.TENTATIVE
