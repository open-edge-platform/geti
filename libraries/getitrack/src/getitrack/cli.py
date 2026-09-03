# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Typer command-line interface.

Exposes two commands:

- ``getitrack track``: run a tracker over precomputed detections (MOT text
  format), write per-frame track results, and optionally an annotated video.
- ``getitrack eval``: compute MOT metrics (MOTA, IDF1, id switches, ...) from
  predicted tracks against ground truth, both in MOT text format.

The ``eval`` command needs the optional ``[eval]`` extra (``motmetrics``,
``pandas``); ``track`` does not.

``track`` consumes precomputed detections rather than raw frames. The detection
file is MOT-challenge text, one detection per line::

    frame,id,x,y,w,h[,score[,class]]

where ``x, y`` is the top-left corner in absolute pixels. The ``id`` column is
ignored for detections (use ``-1``); ``score`` defaults to 1.0 and ``class``
to 0 when omitted. Track results are written in the same format with the
assigned track id in the ``id`` column.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import TYPE_CHECKING, Annotated

import numpy as np
import typer
import yaml

from getitrack.config import TrackerConfig
from getitrack.core.base import BaseTracker
from getitrack.core.detection import Detections, TrackedDetections
from getitrack.core.registry import resolve_tracker_config
from getitrack.io import VideoReader, VideoWriter
from getitrack.visualization import TrackAnnotator

if TYPE_CHECKING:
    from getitrack.evaluation import MotMetrics

app = typer.Typer(name="getitrack", help="Multi-object tracking toolkit.", no_args_is_help=True)

_MOT_MIN_COLS = 6
_MOT_SCORE_COL = 6
_MOT_CLASS_COL = 7


def _load_config(config: Path | None, algorithm: str | None) -> TrackerConfig:
    """Load a tracker config from YAML, applying an optional algorithm override."""
    if config is not None and algorithm is None:
        return TrackerConfig.from_yaml(config)
    data: dict[str, object] = {}
    if config is not None:
        with Path(config).open(encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    if algorithm is not None:
        data["algorithm"] = algorithm
    return resolve_tracker_config(data)


def _load_mot_detections(path: Path) -> dict[int, list[list[float]]]:
    """Parse a MOT-format detection file grouped by 1-based frame number.

    Each line is ``frame,id,x,y,w,h[,score[,class]]`` with ``x, y`` the
    top-left corner. Scores are clipped into ``[0, 1]``; a missing score
    defaults to 1.0 and a missing class to 0.

    Args:
        path: Path to the MOT-format detection file.

    Returns:
        A mapping from frame number to a list of ``[x1, y1, x2, y2, score,
        class]`` rows.

    Raises:
        ValueError: If a non-empty line has fewer than six columns.
    """
    per_frame: dict[int, list[list[float]]] = defaultdict(list)
    for lineno, raw in enumerate(path.read_text().splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        parts = line.split(",")
        if len(parts) < _MOT_MIN_COLS:
            msg = f"{path}:{lineno}: expected at least {_MOT_MIN_COLS} comma-separated values; got {len(parts)}"
            raise ValueError(msg)
        frame = int(float(parts[0]))
        x, y, w, h = (float(v) for v in parts[2:6])
        score = float(parts[_MOT_SCORE_COL]) if len(parts) > _MOT_SCORE_COL else 1.0
        class_id = int(float(parts[_MOT_CLASS_COL])) if len(parts) > _MOT_CLASS_COL else 0
        score = min(max(score, 0.0), 1.0)
        per_frame[frame].append([x, y, x + w, y + h, score, float(class_id)])
    return per_frame


def _detections_for_frame(per_frame: dict[int, list[list[float]]], frame_id: int) -> Detections:
    """Build a `Detections` for one frame from parsed MOT rows."""
    rows = per_frame.get(frame_id)
    if not rows:
        return Detections.create_empty(frame_id=frame_id)
    arr = np.asarray(rows, dtype=np.float64)
    return Detections(
        bboxes=arr[:, 0:4].astype(np.float32),
        scores=arr[:, 4].astype(np.float32),
        class_ids=arr[:, 5].astype(np.int64),
        frame_id=frame_id,
    )


def _mot_rows(tracked: TrackedDetections) -> list[str]:
    """Render one frame's tracker output as MOT-format text lines."""
    rows = []
    for bbox, track_id, score, class_id in zip(
        tracked.bboxes,
        tracked.track_ids,
        tracked.scores,
        tracked.class_ids,
        strict=True,
    ):
        x1, y1, x2, y2 = (float(v) for v in bbox)
        rows.append(
            f"{tracked.frame_id},{int(track_id)},{x1:.2f},{y1:.2f},{x2 - x1:.2f},{y2 - y1:.2f}"
            f",{float(score):.4f},{int(class_id)},-1",
        )
    return rows


@app.command()
def track(
    detections: Annotated[
        Path,
        typer.Option("--detections", "-d", exists=True, dir_okay=False, help="MOT-format detection file."),
    ],
    video: Annotated[
        Path | None,
        typer.Option("--video", "-v", exists=True, dir_okay=False, help="Input video, required for annotation."),
    ] = None,
    config: Annotated[
        Path | None,
        typer.Option("--config", "-c", exists=True, dir_okay=False, help="Tracker YAML config."),
    ] = None,
    algorithm: Annotated[
        str | None,
        typer.Option("--algorithm", "-a", help="Tracking algorithm. Overrides the config value."),
    ] = None,
    output: Annotated[
        Path | None,
        typer.Option(
            "--output", "-o", help="Track results file (MOT format). Defaults to '<detections stem>_tracks.txt'."
        ),
    ] = None,
    output_video: Annotated[
        Path | None,
        typer.Option("--output-video", help="Annotated video path. Requires --video."),
    ] = None,
) -> None:
    """Run a tracker over precomputed detections and write MOT-format results.

    When ``--video`` is given, frames are read from it and its length bounds
    the sequence; otherwise the sequence spans frame 1 to the highest frame in
    the detection file. ``--output-video`` writes an annotated clip and needs
    ``--video`` for the source frames.
    """
    if output_video is not None and video is None:
        msg = "--output-video requires --video"
        raise typer.BadParameter(msg)

    tracker = BaseTracker.from_config(_load_config(config, algorithm))
    per_frame = _load_mot_detections(detections)
    if output is None:
        output = detections.with_name(f"{detections.stem}_tracks.txt")

    if video is not None:
        rows, track_ids, n_frames = _track_video(tracker, per_frame, video, output_video)
    else:
        rows, track_ids, n_frames = _track_headless(tracker, per_frame)

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(rows) + "\n" if rows else "")
    typer.echo(f"Processed {n_frames} frames, {len(track_ids)} tracks -> {output}")
    if output_video is not None:
        typer.echo(f"Annotated video -> {output_video}")


def _track_video(
    tracker: BaseTracker,
    per_frame: dict[int, list[list[float]]],
    video: Path,
    output_video: Path | None,
) -> tuple[list[str], set[int], int]:
    """Track over the frames of a video, optionally writing an annotated clip."""
    annotator = TrackAnnotator()
    rows: list[str] = []
    track_ids: set[int] = set()
    n_frames = 0
    with VideoReader(video) as reader:
        writer = None
        if output_video is not None:
            writer = VideoWriter(output_video, fps=reader.fps or 30.0, frame_size=(reader.width, reader.height))
        try:
            for index, frame in enumerate(reader):
                frame_id = index + 1  # MOT frame numbers are 1-based.
                tracked = tracker.update(_detections_for_frame(per_frame, frame_id))
                rows.extend(_mot_rows(tracked))
                track_ids.update(int(t) for t in tracked.track_ids)
                if writer is not None:
                    writer.write(annotator.annotate(frame, tracked))
                n_frames += 1
        finally:
            if writer is not None:
                writer.close()
    return rows, track_ids, n_frames


def _track_headless(
    tracker: BaseTracker,
    per_frame: dict[int, list[list[float]]],
) -> tuple[list[str], set[int], int]:
    """Track over detections alone, spanning frame 1 to the highest frame seen."""
    rows: list[str] = []
    track_ids: set[int] = set()
    last_frame = max(per_frame) if per_frame else 0
    for frame_id in range(1, last_frame + 1):
        tracked = tracker.update(_detections_for_frame(per_frame, frame_id))
        rows.extend(_mot_rows(tracked))
        track_ids.update(int(t) for t in tracked.track_ids)
    return rows, track_ids, last_frame


def _render_metrics_table(metrics: MotMetrics) -> str:
    """Render metrics as a Markdown pipe table."""
    lines = ["| metric | value |", "| --- | --- |"]
    for key, value in metrics.as_dict().items():
        if value is None:
            cell = "N/A"
        elif isinstance(value, float):
            cell = f"{value:.4f}"
        else:
            cell = str(value)
        lines.append(f"| {key} | {cell} |")
    return "\n".join(lines)


@app.command(name="eval")
def evaluate(
    predictions: Annotated[
        Path,
        typer.Option("--predictions", "-p", exists=True, dir_okay=False, help="Predicted tracks (MOT format)."),
    ],
    ground_truth: Annotated[
        Path,
        typer.Option("--ground-truth", "-g", exists=True, dir_okay=False, help="Ground-truth tracks (MOT format)."),
    ],
    iou_threshold: Annotated[
        float,
        typer.Option("--iou-threshold", min=0.0, max=1.0, help="Minimum IoU for a ground-truth/hypothesis match."),
    ] = 0.5,
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Write the metrics to this JSON file."),
    ] = None,
) -> None:
    """Compute MOT metrics from predicted tracks against ground truth."""
    try:
        from getitrack.evaluation import evaluate_mot, load_mot
    except ImportError as exc:
        typer.echo(
            "The 'eval' command needs extra dependencies. Install them with: pip install 'getitrack[eval]'",
            err=True,
        )
        raise typer.Exit(code=1) from exc
    metrics = evaluate_mot(
        load_mot(ground_truth),
        load_mot(predictions),
        iou_threshold=iou_threshold,
        name=predictions.stem,
    )
    typer.echo(_render_metrics_table(metrics))
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(metrics.as_dict(), indent=2) + "\n")
        typer.echo(f"Metrics -> {output}")


if __name__ == "__main__":
    app()
