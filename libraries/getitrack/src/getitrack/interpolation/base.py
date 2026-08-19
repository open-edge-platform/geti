# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Interpolation-strategy base class and shared internal types.

`BaseInterpolator` owns the clip-level pipeline (gap detection, causal
lookahead, smoothing, row assembly) as a template method; concrete strategies
override only `fill`. Strategies self-register via a ``method`` class variable,
so `from_config` dispatches by `InterpolationMethod` the way
`BaseTracker.from_config` resolves algorithms.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass
from itertools import pairwise
from typing import TYPE_CHECKING, ClassVar

import numpy as np

from getitrack.config import InterpolationConfig
from getitrack.core.detection import TrackedDetections
from getitrack.core.track import TrackState

if TYPE_CHECKING:
    from collections.abc import Sequence

    from getitrack.config import InterpolationMethod, MotionConfig

# Populated as each strategy module is imported (see the package __init__).
_INTERPOLATOR_REGISTRY: dict[InterpolationMethod, type[BaseInterpolator]] = {}


@dataclass(frozen=True)
class Observation:
    """One observed appearance of a track: frame, box, score, and class."""

    frame_id: int
    bbox: np.ndarray
    score: float
    class_id: int


@dataclass(frozen=True)
class _SynthRow:
    """One synthesised gap-fill row destined for a specific output frame."""

    track_id: int
    bbox: np.ndarray
    score: float
    class_id: int


class BaseInterpolator(ABC):
    """Fills short per-track gaps across a clip of `TrackedDetections`.

    Subclasses supply only `fill`; the shared clip pipeline lives in
    `interpolate`. Stateless between calls, so one instance serves any number of
    clips.
    """

    #: The `InterpolationMethod` this strategy fills for; set by each subclass.
    method: ClassVar[InterpolationMethod]

    def __init_subclass__(cls, **kwargs: object) -> None:
        """Register a concrete strategy under its declared ``method``."""
        super().__init_subclass__(**kwargs)
        method = getattr(cls, "method", None)
        if method is None:
            return  # intermediate subclass without a method; nothing to register
        if method in _INTERPOLATOR_REGISTRY:
            msg = f"interpolation method '{method}' already registered by {_INTERPOLATOR_REGISTRY[method].__name__}"
            raise ValueError(msg)
        _INTERPOLATOR_REGISTRY[method] = cls

    def __init__(self, config: InterpolationConfig | None = None, *, motion: MotionConfig | None = None) -> None:
        """Store config and motion; ``motion`` is read only by motion-based strategies (``KALMAN``)."""
        self._config = config if config is not None else InterpolationConfig()
        self._motion = motion

    @property
    def config(self) -> InterpolationConfig:
        """The interpolation configuration in effect."""
        return self._config

    @classmethod
    def from_config(
        cls,
        config: InterpolationConfig | None = None,
        *,
        motion: MotionConfig | None = None,
    ) -> BaseInterpolator:
        """Build the interpolator registered for ``config.method``."""
        cfg = config if config is not None else InterpolationConfig()
        try:
            strategy_cls = _INTERPOLATOR_REGISTRY[cfg.method]
        except KeyError as exc:  # pragma: no cover - registry is populated at package import
            known = sorted(method.value for method in _INTERPOLATOR_REGISTRY)
            msg = f"no interpolator registered for method '{cfg.method}'; registered: {known}"
            raise KeyError(msg) from exc
        return strategy_cls(cfg, motion=motion)

    @abstractmethod
    def fill(
        self,
        observations: list[Observation],
        start: Observation,
        end: Observation,
        frame_ids: list[int],
    ) -> np.ndarray:
        """Return ``(len(frame_ids), 4)`` float32 ``xyxy`` boxes for one gap.

        ``observations`` is the track's full ordered list; spline uses it,
        endpoint-only strategies rely on ``start``/``end``.
        """

    def interpolate(
        self,
        frames: Sequence[TrackedDetections],
        *,
        online: bool | None = None,
    ) -> list[TrackedDetections]:
        """Return a gap-filled copy of the clip, sorted by ``frame_id``.

        Bridges gaps up to ``max_gap`` between two observed frames; frames that
        gain no rows are returned unchanged. Idempotent: a track never gets a
        second row in a frame and observed boxes are never modified. ``online``
        overrides `InterpolationConfig.online`; in causal mode a gap frame is
        filled only once its closing observation is within ``online_buffer``
        frames. Synthesised rows carry ``interpolated=True`` and ``det_index=-1``.
        """
        if not self._config.enabled:
            return list(frames)
        ordered = sorted(frames, key=lambda frame: frame.frame_id)
        if not ordered:
            return []

        use_online = self._config.online if online is None else online
        position_by_frame = {frame.frame_id: index for index, frame in enumerate(ordered)}
        observations = self._collect_observations(ordered)

        # Every (frame, track) pair already present blocks a synthesised row, so
        # a track never gets two rows in one frame and the pass is idempotent.
        occupied: set[tuple[int, int]] = {
            (index, int(track_id)) for index, frame in enumerate(ordered) for track_id in frame.track_ids.tolist()
        }

        additions: defaultdict[int, list[_SynthRow]] = defaultdict(list)
        for track_id in sorted(observations):
            for frame_id, bbox, score, class_id in self._interpolate_track(observations[track_id], online=use_online):
                position = position_by_frame.get(frame_id)
                if position is None or (position, track_id) in occupied:
                    continue
                additions[position].append(_SynthRow(track_id, bbox, score, class_id))
                occupied.add((position, track_id))

        return [
            self._augment_frame(frame, additions[index]) if index in additions else frame
            for index, frame in enumerate(ordered)
        ]

    @staticmethod
    def _collect_observations(ordered: list[TrackedDetections]) -> dict[int, list[Observation]]:
        """Group observed (non-interpolated) rows by track id in frame order."""
        observations: defaultdict[int, list[Observation]] = defaultdict(list)
        for frame in ordered:
            interpolated = frame.interpolated
            for row in range(len(frame)):
                if interpolated is not None and bool(interpolated[row]):
                    continue
                observations[int(frame.track_ids[row])].append(
                    Observation(
                        frame_id=frame.frame_id,
                        bbox=frame.bboxes[row].astype(np.float32),
                        score=float(frame.scores[row]),
                        class_id=int(frame.class_ids[row]),
                    )
                )
        return dict(observations)

    def _interpolate_track(
        self,
        observations: list[Observation],
        *,
        online: bool,
    ) -> list[tuple[int, np.ndarray, float, int]]:
        """Synthesise this track's gap rows, delegating each gap to `fill` and then smoothing."""
        cfg = self._config
        synth: dict[int, tuple[np.ndarray, float, int]] = {}
        for start, end in pairwise(observations):
            gap = end.frame_id - start.frame_id - 1
            if gap < 1 or gap > cfg.max_gap:
                continue
            frame_ids = [
                frame_id
                for frame_id in range(start.frame_id + 1, end.frame_id)
                if not online or (end.frame_id - frame_id) <= cfg.online_buffer
            ]
            if not frame_ids:
                continue
            # Causal horizon: a strategy that fits the whole trajectory (spline)
            # must not see observations past this gap's closing anchor, or an
            # already-emitted gap frame would shift when later frames arrive.
            visible = [obs for obs in observations if not online or obs.frame_id <= end.frame_id]
            boxes = self.fill(visible, start, end, frame_ids)
            span = float(end.frame_id - start.frame_id)
            for frame_id, box in zip(frame_ids, boxes, strict=True):
                weight = (frame_id - start.frame_id) / span
                score = float(np.clip((1.0 - weight) * start.score + weight * end.score, 0.0, 1.0))
                synth[frame_id] = (box, score, start.class_id)

        if synth and cfg.smoothing_window > 1:
            smoothed = self._smooth_synth_boxes(observations, synth, online=online)
            synth = {
                frame_id: (smoothed[frame_id], score, class_id) for frame_id, (_, score, class_id) in synth.items()
            }

        return [(frame_id, box, score, class_id) for frame_id, (box, score, class_id) in sorted(synth.items())]

    def _smooth_synth_boxes(
        self,
        observations: list[Observation],
        synth: dict[int, tuple[np.ndarray, float, int]],
        *,
        online: bool,
    ) -> dict[int, np.ndarray]:
        """Replace each synthesised box with a centred moving average over the track's trajectory.

        Observed boxes are untouched (keeps the pass idempotent). In causal mode
        the window is trimmed to ``frame + online_buffer`` so smoothing reads no
        further ahead than the fill did.
        """
        trajectory: dict[int, np.ndarray] = {observation.frame_id: observation.bbox for observation in observations}
        for frame_id, (box, _, _) in synth.items():
            trajectory[frame_id] = box
        frame_ids = sorted(trajectory)
        boxes = np.stack([trajectory[frame_id] for frame_id in frame_ids], axis=0).astype(np.float64)

        radius = self._config.smoothing_window // 2
        smoothed: dict[int, np.ndarray] = {}
        for index, frame_id in enumerate(frame_ids):
            if frame_id not in synth:
                continue
            low = max(0, index - radius)
            high = min(len(frame_ids), index + radius + 1)
            if online:
                # Causal horizon: drop samples later than the lookahead used to fill.
                horizon = frame_id + self._config.online_buffer
                while high > index + 1 and frame_ids[high - 1] > horizon:
                    high -= 1
            smoothed[frame_id] = boxes[low:high].mean(axis=0).astype(np.float32)
        return smoothed

    @staticmethod
    def _augment_frame(frame: TrackedDetections, synth_rows: list[_SynthRow]) -> TrackedDetections:
        """Append synthesised rows to a frame, normalising the optional columns."""
        n_real = len(frame)
        n_synth = len(synth_rows)

        synth_bboxes = np.stack([row.bbox for row in synth_rows], axis=0).astype(np.float32)
        bboxes = np.concatenate([frame.bboxes, synth_bboxes], axis=0)
        scores = np.concatenate([frame.scores, np.array([row.score for row in synth_rows], dtype=np.float32)], axis=0)
        class_ids = np.concatenate(
            [frame.class_ids, np.array([row.class_id for row in synth_rows], dtype=np.int64)], axis=0
        )
        track_ids = np.concatenate(
            [frame.track_ids, np.array([row.track_id for row in synth_rows], dtype=np.int64)], axis=0
        )
        track_states = np.concatenate(
            [frame.track_states, np.full(n_synth, int(TrackState.ACTIVE), dtype=np.int8)], axis=0
        )

        real_det = frame.det_indices if frame.det_indices is not None else np.full(n_real, -1, dtype=np.int64)
        det_indices = np.concatenate([real_det, np.full(n_synth, -1, dtype=np.int64)], axis=0)

        real_interp = frame.interpolated if frame.interpolated is not None else np.zeros(n_real, dtype=np.bool_)
        interpolated = np.concatenate([real_interp, np.ones(n_synth, dtype=np.bool_)], axis=0)

        return TrackedDetections(
            bboxes=bboxes,
            scores=scores,
            class_ids=class_ids,
            track_ids=track_ids,
            track_states=track_states,
            frame_id=frame.frame_id,
            det_indices=det_indices,
            interpolated=interpolated,
        )
