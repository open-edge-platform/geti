# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Configuration model for the ByteTrack tracker."""

from __future__ import annotations

from typing import Annotated, ClassVar, Literal

from pydantic import Field, model_validator

from getitrack.config import AlgorithmType, TrackerConfig


class ByteTrackConfig(TrackerConfig):
    """ByteTrack-specific configuration."""

    # Margin above the high/low split a detection must clear to spawn a new track.
    _NEW_TRACK_MARGIN: ClassVar[float] = 0.1

    # Literal pins the value in the JSON schema and typing.
    algorithm: Literal[AlgorithmType.BYTETRACK] = AlgorithmType.BYTETRACK  # pyrefly: ignore[bad-override]
    """Algorithm identifier; fixed to ``bytetrack``."""

    match_threshold: Annotated[float, Field(ge=0.0, le=1.0)] = 0.8
    """Maximum assignment cost accepted when matching detections to tracks.
    The cost is ``1 - IoU``, score-fused to ``1 - IoU * score`` where fusion
    applies, so larger values accept weaker overlaps."""

    high_score_threshold: Annotated[float, Field(ge=0.0, le=1.0)] = 0.5
    """High/low detection split for two-stage association (ByteTrack's ``track_thresh``).
    Spawning a new track additionally requires a score 0.1 above this value."""

    match_class_only: bool = True
    """Restrict matching to detection-track pairs that share a class id."""

    @property
    def new_track_floor(self) -> float:
        """Minimum score for an unmatched high detection to spawn a new track."""
        return self.high_score_threshold + self._NEW_TRACK_MARGIN

    @model_validator(mode="after")
    def _check_thresholds(self) -> ByteTrackConfig:
        """Reject thresholds that contradict the high/low split or new-track gate."""
        if self.score_threshold >= self.high_score_threshold:
            msg = "score_threshold must be below high_score_threshold"
            raise ValueError(msg)
        if self.new_track_floor > 1.0:
            ceiling = 1.0 - self._NEW_TRACK_MARGIN
            msg = f"high_score_threshold must be <= {ceiling} to leave room for the new-track margin"
            raise ValueError(msg)
        return self
