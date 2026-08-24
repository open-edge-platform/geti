# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""OC-SORT: observation-centric detection-to-track association.

OC-SORT extends SORT's motion-only tracking with three observation-centric
mechanisms:

* OCM (observation-centric momentum): a velocity-direction consistency term
  added to the first association cost.
* OCR (observation-centric recovery): a recovery pass matching leftover
  detections against each track's last observation instead of its Kalman
  prediction.
* ORU (observation-centric re-update): on re-acquisition after a gap, the
  filter is rewound to the last observation and replayed along a virtual
  trajectory to the new one.

Kalman state stays in its own dict for batched prediction; the remaining
observation-centric state is grouped per track id in ``_ObsTrack``.

Reference: Cao et al., "Observation-Centric SORT: Rethinking SORT for Robust
Multi-Object Tracking" (CVPR 2023).
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, ClassVar

import numpy as np

from getitrack.algorithms.configs.ocsort import OCSortConfig
from getitrack.core.base import BaseTracker
from getitrack.core.detection import Detections, TrackedDetections
from getitrack.core.registry import register_algorithm
from getitrack.core.track import Track, TrackState
from getitrack.matching import BaseDistanceMetric, linear_assignment
from getitrack.motion import KalmanFilter
from getitrack.utils import xyah_to_xyxy, xyxy_to_xyah

if TYPE_CHECKING:
    from getitrack.config import LifecycleConfig

_DIRECTION_EPS = 1e-6


def _subset(dets: Detections, indices: list[int] | np.ndarray) -> Detections:
    """Row-select a `Detections` by integer indices."""
    idx = np.asarray(indices, dtype=np.int64)
    return Detections(
        bboxes=dets.bboxes[idx],
        scores=dets.scores[idx],
        class_ids=dets.class_ids[idx],
        frame_id=dets.frame_id,
        embeddings=None if dets.embeddings is None else dets.embeddings[idx],
    )


def _centers(boxes: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return ``(cx, cy)`` of ``xyxy`` boxes."""
    return (boxes[:, 0] + boxes[:, 2]) / 2.0, (boxes[:, 1] + boxes[:, 3]) / 2.0


def _speed_direction(box1: np.ndarray, box2: np.ndarray) -> np.ndarray:
    """Unit ``(dy, dx)`` direction from ``box1`` center to ``box2`` center."""
    cx1, cy1 = (box1[0] + box1[2]) / 2.0, (box1[1] + box1[3]) / 2.0
    cx2, cy2 = (box2[0] + box2[2]) / 2.0, (box2[1] + box2[3]) / 2.0
    speed = np.array([cy2 - cy1, cx2 - cx1], dtype=np.float64)
    norm = float(np.sqrt(speed[0] ** 2 + speed[1] ** 2)) + _DIRECTION_EPS
    return speed / norm


def _velocity_direction_batch(det_boxes: np.ndarray, prev_boxes: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Unit direction from each previous-observation center to each detection center.

    Returns ``(dy, dx)``, each ``(num_tracks, num_dets)``.
    """
    dcx, dcy = _centers(det_boxes)
    pcx, pcy = _centers(prev_boxes)
    dx = dcx[None, :] - pcx[:, None]
    dy = dcy[None, :] - pcy[:, None]
    norm = np.sqrt(dx**2 + dy**2) + _DIRECTION_EPS
    return dy / norm, dx / norm


def _direction_cost(
    det_boxes: np.ndarray,
    prev_boxes: np.ndarray,
    velocities: np.ndarray,
    valid: np.ndarray,
    scores: np.ndarray,
    inertia: float,
) -> np.ndarray:
    """OCM momentum_bonus ``(num_tracks, num_dets)`` for direction-consistent pairs.

    For each track velocity ``v`` and the direction ``u`` from its prior
    observation to a detection, the momentum_bonus is ``(pi/2 - |angle(v, u)|) / pi``,
    scaled by ``inertia`` and the detection score, and zero where the track
    has no velocity estimate.
    """
    n_tracks, n_dets = prev_boxes.shape[0], det_boxes.shape[0]
    if n_tracks == 0 or n_dets == 0:
        return np.zeros((n_tracks, n_dets), dtype=np.float32)
    dir_y, dir_x = _velocity_direction_batch(det_boxes, prev_boxes)
    vel_y = velocities[:, 0][:, None]
    vel_x = velocities[:, 1][:, None]
    cos = np.clip(vel_x * dir_x + vel_y * dir_y, -1.0, 1.0)
    angle = np.arccos(cos)
    reward = (np.pi / 2.0 - np.abs(angle)) / np.pi
    mask = valid.astype(np.float32)[:, None]
    scaled_scores = scores.astype(np.float32)[None, :]
    return (mask * reward * inertia) * scaled_scores


@dataclass
class _ObsTrack:
    """Observation-centric state stored alongside a `Track`."""

    obs_state: tuple[np.ndarray, np.ndarray]  # Kalman snapshot at the last observation (ORU)
    observations: dict[int, np.ndarray]  # track age -> observed box (OCM)
    last_obs: np.ndarray  # last observed box (OCR)
    velocity: np.ndarray | None  # unit velocity (dy, dx), None until two observations


@register_algorithm("ocsort", config=OCSortConfig)
class OCSortTracker(BaseTracker[OCSortConfig]):
    """OC-SORT multi-object tracker.

    Each frame: predict all tracks; associate high-score detections with an
    IoU-plus-momentum (OCM) cost; optionally recover tracks from low-score
    detections (BYTE); recover the rest against each track's last observation
    (OCR); re-update matched filters along a virtual trajectory when they had
    missed frames (ORU); spawn tracks from leftover high-score detections.
    ``update`` returns the ACTIVE tracks for the frame.
    """

    algorithm_name: ClassVar[str] = "ocsort"

    _INVALID_COST: ClassVar[float] = 1e6
    # Assignment ceiling: above any real combined cost, below _INVALID_COST, so
    # masked pairs the solver is forced to pick are still rejected.
    _MATCH_COST_CEILING: ClassVar[float] = _INVALID_COST / 2.0

    def __init__(self, config: OCSortConfig) -> None:
        super().__init__(config)
        self._kalman = KalmanFilter.from_config(config.motion)
        # Association distance selected by config; defaults to IoUDistance.
        self._distance: BaseDistanceMetric = BaseDistanceMetric.from_metric(config.distance_metric)
        self._tracks: dict[int, Track] = {}
        # Current Kalman state, kept as its own dict for batched multi_predict.
        self._kalman_states: dict[int, tuple[np.ndarray, np.ndarray]] = {}
        # Observation-centric bookkeeping, one record per live track.
        self._obs: dict[int, _ObsTrack] = {}
        self._first_frame_id: int | None = None
        # track_id -> row index into this frame's input Detections.
        self._frame_det_index: dict[int, int] = {}

    def reset(self) -> None:  # noqa: D102
        super().reset()
        self._tracks.clear()
        self._kalman_states.clear()
        self._obs.clear()
        self._first_frame_id = None
        self._frame_det_index.clear()

    def _update_impl(self, detections: Detections) -> TrackedDetections:
        """Run one OC-SORT iteration and return the active set."""
        self._frame_id = detections.frame_id
        if self._first_frame_id is None:
            self._first_frame_id = detections.frame_id
        self._frame_det_index.clear()
        config = self.config
        lifecycle = config.lifecycle

        # Strict bounds: a score exactly on det_threshold falls outside both bands.
        scores = detections.scores
        high_score_indices = np.flatnonzero(scores > config.det_threshold)
        high_dets = _subset(detections, high_score_indices)

        self._predict_all()
        track_ids = list(self._tracks)

        # First association: all tracks vs high-score detections, IoU + OCM.
        matches, unmatched_track_idx, unmatched_det_idx = self._associate_first(track_ids, high_dets)
        for track_pos, det_pos in matches:
            self._apply_hit(
                track_ids[track_pos], high_dets, det_pos, lifecycle, src_index=int(high_score_indices[det_pos])
            )
        unmatched_track_ids = [track_ids[i] for i in unmatched_track_idx]

        # Optional BYTE stage: leftover tracks vs low-score detections, IoU only.
        if config.use_byte:
            low_score_indices = np.flatnonzero((scores > config.score_threshold) & (scores < config.det_threshold))
            unmatched_track_ids = self._associate_byte(
                unmatched_track_ids, _subset(detections, low_score_indices), low_score_indices, lifecycle
            )

        # OCR: leftover high detections vs unmatched tracks' last observation.
        unmatched_high_indices = [int(i) for i in unmatched_det_idx]
        unmatched_track_ids, unmatched_high_indices = self._associate_recovery(
            unmatched_track_ids, high_dets, high_score_indices, unmatched_high_indices, lifecycle
        )

        for track_id in unmatched_track_ids:
            self._tracks[track_id].mark_miss(lifecycle)

        for det_pos in unmatched_high_indices:
            self._spawn_track(high_dets, det_pos, src_index=int(high_score_indices[det_pos]))

        for track_id in list(self._tracks):
            if self._tracks[track_id].should_remove:
                self._remove_track(track_id)

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

    def _associate_first(self, track_ids: list[int], dets: Detections) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """First pass: association cost with the OCM momentum bonus, gated on the configured metric."""
        if not track_ids or len(dets) == 0:
            return self._empty_association(len(track_ids), len(dets))
        track_boxes = np.stack([self._tracks[track_id].bbox for track_id in track_ids], axis=0)
        metric_cost = self._distance(track_boxes, dets.bboxes)

        prev_boxes = np.stack([self._previous_observation(track_id) for track_id in track_ids], axis=0)
        velocities = np.stack(
            [v if (v := self._obs[track_id].velocity) is not None else np.zeros(2) for track_id in track_ids],
            axis=0,
        )
        valid = np.array([self._obs[track_id].velocity is not None for track_id in track_ids])
        momentum_bonus = _direction_cost(dets.bboxes, prev_boxes, velocities, valid, dets.scores, self.config.inertia)

        cost = metric_cost - momentum_bonus
        # Mask pairs failing the distance or class gate; the momentum_bonus only reorders the rest.
        invalid = metric_cost > self.config.match_threshold
        class_mismatch = self._class_mismatch(track_ids, dets)
        if class_mismatch is not None:
            invalid = invalid | class_mismatch
        cost[invalid] = self._INVALID_COST
        return linear_assignment(cost, self._MATCH_COST_CEILING)

    def _associate_byte(
        self, track_ids: list[int], low_dets: Detections, low_score_indices: np.ndarray, lifecycle: LifecycleConfig
    ) -> list[int]:
        """BYTE pass: unmatched tracks vs low-score detections, on the configured metric."""
        if not track_ids or len(low_dets) == 0:
            return track_ids
        track_boxes = np.stack([self._tracks[track_id].bbox for track_id in track_ids], axis=0)
        cost = self._distance(track_boxes, low_dets.bboxes)
        class_mismatch = self._class_mismatch(track_ids, low_dets)
        if class_mismatch is not None:
            cost[class_mismatch] = self._INVALID_COST
        matches, unmatched_track_idx, _ = linear_assignment(cost, self.config.match_threshold)
        for track_pos, det_pos in matches:
            self._apply_hit(
                track_ids[track_pos], low_dets, det_pos, lifecycle, src_index=int(low_score_indices[det_pos])
            )
        return [track_ids[i] for i in unmatched_track_idx]

    def _associate_recovery(
        self,
        track_ids: list[int],
        high_dets: Detections,
        high_score_indices: np.ndarray,
        unmatched_high_indices: list[int],
        lifecycle: LifecycleConfig,
    ) -> tuple[list[int], list[int]]:
        """OCR pass: leftover detections vs unmatched tracks' last observation."""
        if not track_ids or not unmatched_high_indices:
            return track_ids, unmatched_high_indices
        left_dets = _subset(high_dets, unmatched_high_indices)
        last_boxes = np.stack([self._obs[track_id].last_obs for track_id in track_ids], axis=0)
        cost = self._distance(last_boxes, left_dets.bboxes)
        class_mismatch = self._class_mismatch(track_ids, left_dets)
        if class_mismatch is not None:
            cost[class_mismatch] = self._INVALID_COST
        matches, unmatched_track_idx, unmatched_det_idx = linear_assignment(cost, self.config.match_threshold)
        for track_pos, det_pos in matches:
            real_det_pos = unmatched_high_indices[det_pos]
            self._apply_hit(
                track_ids[track_pos],
                high_dets,
                real_det_pos,
                lifecycle,
                src_index=int(high_score_indices[real_det_pos]),
            )
        remaining_tracks = [track_ids[i] for i in unmatched_track_idx]
        remaining_dets = [unmatched_high_indices[i] for i in unmatched_det_idx]
        return remaining_tracks, remaining_dets

    def _apply_hit(
        self,
        track_id: int,
        dets: Detections,
        det_idx: int,
        lifecycle: LifecycleConfig,
        *,
        src_index: int,
    ) -> None:
        """Record an observation: update velocity, re-update the filter (ORU), advance the FSM."""
        track = self._tracks[track_id]
        obs = self._obs[track_id]
        new_box = dets.bboxes[det_idx].astype(np.float32)
        score = float(dets.scores[det_idx])
        gap_steps = track.time_since_update + 1

        prev_box = self._previous_observation(track_id)
        obs.velocity = _speed_direction(prev_box, new_box)

        self._reupdate_from_last_observation(track_id, obs.last_obs, new_box, gap_steps)
        obs.obs_state = self._kalman_states[track_id]

        track.mark_hit(new_box, score, lifecycle)
        obs.observations[track.age] = new_box
        # Only ages within the delta_t lookback window are read afterwards.
        cutoff = track.age - self.config.delta_t
        for stale_age in [a for a in obs.observations if a < cutoff]:
            del obs.observations[stale_age]
        obs.last_obs = new_box
        self._frame_det_index[track_id] = src_index

    def _reupdate_from_last_observation(
        self, track_id: int, last_box: np.ndarray, new_box: np.ndarray, steps: int
    ) -> None:
        """Rewind the filter to the last observation and replay a virtual trajectory to ``new_box``.

        The virtual observations interpolate box center and size linearly across
        the ``steps`` frames since the last real observation. For ``steps == 1``
        (a consecutive hit) this reduces to a single predict-update cycle.
        """
        mean, cov = self._obs[track_id].obs_state
        lcx, lcy = (last_box[0] + last_box[2]) / 2.0, (last_box[1] + last_box[3]) / 2.0
        lw, lh = last_box[2] - last_box[0], last_box[3] - last_box[1]
        ncx, ncy = (new_box[0] + new_box[2]) / 2.0, (new_box[1] + new_box[3]) / 2.0
        nw, nh = new_box[2] - new_box[0], new_box[3] - new_box[1]
        for i in range(1, steps + 1):
            t = i / steps
            cx, cy = lcx + t * (ncx - lcx), lcy + t * (ncy - lcy)
            w, h = lw + t * (nw - lw), lh + t * (nh - lh)
            virtual = np.array([cx - w / 2.0, cy - h / 2.0, cx + w / 2.0, cy + h / 2.0], dtype=np.float32)
            measurement = xyxy_to_xyah(virtual[None, :])[0]
            mean, cov = self._kalman.predict(mean, cov)
            mean, cov = self._kalman.update(mean, cov, measurement)
        self._kalman_states[track_id] = (mean, cov)

    def _spawn_track(self, dets: Detections, det_idx: int, *, src_index: int) -> None:
        """Create a new track from an unmatched high-score detection."""
        track_id = self._allocate_id()
        bbox = dets.bboxes[det_idx].astype(np.float32)
        class_id = int(dets.class_ids[det_idx])
        score = float(dets.scores[det_idx])
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
        measurement = xyxy_to_xyah(bbox[None, :])[0]
        self._kalman_states[track_id] = self._kalman.initiate(measurement)
        self._obs[track_id] = _ObsTrack(
            obs_state=self._kalman_states[track_id],
            observations={track.age: bbox},
            last_obs=bbox,
            velocity=None,
        )
        self._frame_det_index[track_id] = src_index

    def _previous_observation(self, track_id: int) -> np.ndarray:
        """Return the observation ``delta_t`` frames back, else the nearest newer one, else the most recent."""
        observations = self._obs[track_id].observations
        age = self._tracks[track_id].age
        for dt in range(self.config.delta_t, 0, -1):
            if age - dt in observations:
                return observations[age - dt]
        return observations[max(observations)]

    def _class_mismatch(self, track_ids: list[int], dets: Detections) -> np.ndarray | None:
        """Boolean ``(num_tracks, num_dets)`` mask of class-mismatched pairs, or None."""
        if not self.config.match_class_only:
            return None
        track_classes = np.array([self._tracks[track_id].class_id for track_id in track_ids])
        return track_classes[:, None] != dets.class_ids[None, :]

    def _remove_track(self, track_id: int) -> None:
        """Drop all state for a removed track."""
        self._tracks.pop(track_id, None)
        self._kalman_states.pop(track_id, None)
        self._obs.pop(track_id, None)

    @staticmethod
    def _empty_association(n_tracks: int, n_dets: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        return (
            np.empty((0, 2), dtype=np.int64),
            np.arange(n_tracks, dtype=np.int64),
            np.arange(n_dets, dtype=np.int64),
        )

    def _compose_output(self, frame_id: int) -> TrackedDetections:
        """Emit the ACTIVE tracks, each at its last observed box."""
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
