# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Tracker interface and algorithm registry.

Concrete trackers register themselves with the `register_algorithm`
decorator, and `BaseTracker.from_config` dispatches on the registered
name. The registry is populated once the algorithm modules are imported.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar, Generic, TypeVar

import numpy as np

from getitrack.config import TrackerConfig
from getitrack.core.detection import TrackedDetections
from getitrack.core.registry import ALGORITHM_REGISTRY, resolve_tracker_config
from getitrack.logger import enable_logging

_LOGGER = logging.getLogger(__name__)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from getitrack.core.detection import Detections
    from getitrack.core.track import Track

ConfigT = TypeVar("ConfigT", bound=TrackerConfig)


class BaseTracker(ABC, Generic[ConfigT]):
    """Abstract base class for multi-object trackers.

    Concrete subclasses implement `_update_impl`; the public `update`
    wraps it with cross-cutting concerns such as verbose logging. The
    base owns the monotonic id allocator and `_frame_id` bookkeeping so
    subclasses focus on association logic. Track ids are scoped per
    instance (not per process), so parallel tracker instances do not
    collide.
    """

    algorithm_name: ClassVar[str] = ""
    config_cls: ClassVar[type[TrackerConfig]]
    config: ConfigT

    def __init__(self, config: ConfigT) -> None:
        self.config = config
        self._next_id: int = 1
        self._frame_id: int | None = None
        # source_rows of the last processed frame, for remapping filtered-space
        # det_indices back to input rows.
        self._last_source_rows: np.ndarray | None = None
        if config.verbose:
            enable_logging()

    def update(self, detections: Detections) -> TrackedDetections:
        """Process one frame's detections and return the tracker output.

        Applies ``class_filter`` before the algorithm runs, so excluded
        classes never spawn or match tracks. ``det_indices`` on the output
        always index into the unfiltered ``detections`` passed here.
        """
        class_filter = self.config.class_filter
        if class_filter is None:
            filtered, source_rows = detections, None
        else:
            filtered, source_rows = detections.filter_by_class(class_filter)
        self._last_source_rows = source_rows
        tracked = self._remap_to_input_rows(self._update_impl(filtered))
        if self.config.verbose:
            self._log_update(filtered, tracked)
        return tracked

    def _remap_to_input_rows(self, tracked: TrackedDetections) -> TrackedDetections:
        """Remap ``det_indices`` from the last frame's filtered space to input rows.

        Maps matched (``>= 0``) entries back to rows of the unfiltered
        `Detections` passed to `update`, leaving -1 rows untouched. A no-op when
        no ``class_filter`` was applied.
        """
        if self._last_source_rows is None or tracked.det_indices is None:
            return tracked
        remapped = self._remap_det_indices(self._last_source_rows, tracked.det_indices)
        return replace(tracked, det_indices=remapped)

    @staticmethod
    def _remap_det_indices(source_rows: np.ndarray, det_indices: np.ndarray) -> np.ndarray:
        """Map ``det_indices`` from filtered-row space back to input rows."""
        remapped = det_indices.copy()
        matched = remapped >= 0
        remapped[matched] = source_rows[remapped[matched]]
        return remapped

    @abstractmethod
    def _update_impl(self, detections: Detections) -> TrackedDetections:
        """Algorithm-specific tracking step for one frame."""

    @staticmethod
    def _compose_tracked_detections(
        tracks: Sequence[Track],
        det_indices: Sequence[int],
        frame_id: int,
    ) -> TrackedDetections:
        """Assemble a `TrackedDetections` from tracks and their det indices.

        Reads ``bbox``, ``score``, ``class_id``, ``track_id``, and ``state`` off
        each `Track` in order, pairing row ``i`` with ``det_indices[i]``.

        Args:
            tracks: Tracks to emit, one per output row.
            det_indices: Row indices into the frame's input `Detections`,
                aligned with ``tracks``; -1 marks a row with no source detection.
            frame_id: Frame the output belongs to.

        Returns:
            A `TrackedDetections` with one row per track. When ``tracks`` is
            empty the result still carries an empty int64 ``det_indices`` array.
        """
        if not tracks:
            empty = TrackedDetections.create_empty(frame_id=frame_id)
            return replace(empty, det_indices=np.empty((0,), dtype=np.int64))
        return TrackedDetections(
            bboxes=np.stack([t.bbox for t in tracks], axis=0).astype(np.float32),
            scores=np.array([t.score for t in tracks], dtype=np.float32),
            class_ids=np.array([t.class_id for t in tracks], dtype=np.int64),
            track_ids=np.array([t.track_id for t in tracks], dtype=np.int64),
            track_states=np.array([int(t.state) for t in tracks], dtype=np.int8),
            frame_id=frame_id,
            det_indices=np.asarray(det_indices, dtype=np.int64),
        )

    def _log_update(self, detections: Detections, tracked: TrackedDetections) -> None:
        """Emit a one-line per-frame summary on the ``getitrack`` logger."""
        pairs = ", ".join(
            f"{tid}:{cls}:{score:.2f}"
            for tid, cls, score in zip(
                tracked.track_ids.tolist(),
                tracked.class_ids.tolist(),
                tracked.scores.tolist(),
                strict=True,
            )
        )
        _LOGGER.info(
            "frame %4d: %d detections, %d tracks [id:class:score %s]",
            detections.frame_id,
            len(detections),
            len(tracked),
            pairs,
        )

    def reset(self) -> None:
        """Clear internal state between videos or sequences."""
        self._next_id = 1
        self._frame_id = None
        self._last_source_rows = None

    def _allocate_id(self) -> int:
        """Return a fresh monotonic id for a new track."""
        new_id = self._next_id
        self._next_id += 1
        return new_id

    @classmethod
    def from_config(cls, config: TrackerConfig | dict[str, Any] | str | Path) -> BaseTracker:
        """Instantiate a tracker dispatched on ``config.algorithm``.

        Accepts a tracker-config variant, a dict, or a path to a YAML file.
        """
        if isinstance(config, TrackerConfig):
            resolved = resolve_tracker_config(config.model_dump())
        elif isinstance(config, dict):
            resolved = resolve_tracker_config(config)
        elif isinstance(config, str | Path):
            resolved = TrackerConfig.from_yaml(config)
        else:
            msg = f"unsupported config type: {type(config).__name__}"
            raise TypeError(msg)

        name = resolved.algorithm.value
        if name not in ALGORITHM_REGISTRY:
            known = sorted(ALGORITHM_REGISTRY) or ["<none registered>"]
            msg = f"unknown algorithm '{name}'; registered: {known}"
            raise KeyError(msg)
        return ALGORITHM_REGISTRY[name](resolved)
