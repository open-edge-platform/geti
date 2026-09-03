# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""CLEAR-MOT and identity metrics from MOT-format tracks.

`load_mot` parses a MOT-challenge text file into per-frame `MotFrame`
records, `iou_distance_matrix` builds the IoU cost matrix used for
ground-truth-to-hypothesis matching, and `evaluate_mot` accumulates the
frame-by-frame correspondences with `motmetrics` and returns a `MotMetrics`
summary.

The MOT text format is one detection per line::

    frame,id,x,y,w,h[,conf[,class[,visibility]]]

where ``x, y`` is the top-left corner and ``w, h`` the box size in absolute
pixels. Only the first six columns are used; any trailing columns are ignored.
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, cast

import motmetrics as mm
import numpy as np

if TYPE_CHECKING:
    import pandas as pd

_MOT_MIN_COLS = 6
"""Minimum comma-separated columns in a MOT line: frame,id,x,y,w,h."""

_METRIC_FIELDS: tuple[str, ...] = (
    "mota",
    "motp",
    "idf1",
    "precision",
    "recall",
    "num_switches",
    "num_fragmentations",
    "mostly_tracked",
    "partially_tracked",
    "mostly_lost",
    "num_false_positives",
    "num_misses",
    "num_matches",
    "num_unique_objects",
)
"""`motmetrics` metric names computed for every evaluation."""


@dataclass(frozen=True)
class MotFrame:
    """One frame's tracks parsed from a MOT file.

    Attributes:
        ids: ``(N,)`` int64 array of track identifiers.
        boxes: ``(N, 4)`` float64 array of ``xywh`` boxes (top-left corner
            plus width and height) aligned row-for-row with ``ids``.
    """

    ids: np.ndarray
    boxes: np.ndarray


@dataclass(frozen=True)
class MotMetrics:
    """CLEAR-MOT and identity metrics for one sequence.

    Attributes:
        mota: Multiple-object tracking accuracy in ``(-inf, 1]``.
        motp: Multiple-object tracking precision (mean matched distance), or
            None when there are no matches.
        idf1: Identity F1 score in ``[0, 1]``.
        precision: Detection precision in ``[0, 1]``.
        recall: Detection recall in ``[0, 1]``.
        num_switches: Identity switches.
        num_fragmentations: Track fragmentations.
        mostly_tracked: Ground-truth tracks covered for >= 80% of their life.
        partially_tracked: Ground-truth tracks covered for 20-80% of their life.
        mostly_lost: Ground-truth tracks covered for <= 20% of their life.
        num_false_positives: Hypotheses with no matching ground truth.
        num_misses: Ground-truth objects with no matching hypothesis.
        num_matches: Successful ground-truth-to-hypothesis matches.
        num_unique_objects: Distinct ground-truth identities.
    """

    mota: float
    motp: float | None
    idf1: float
    precision: float
    recall: float
    num_switches: int
    num_fragmentations: int
    mostly_tracked: int
    partially_tracked: int
    mostly_lost: int
    num_false_positives: int
    num_misses: int
    num_matches: int
    num_unique_objects: int

    def as_dict(self) -> dict[str, float | int | None]:
        """Return the metrics as a plain ``{name: value}`` mapping."""
        return {
            "mota": self.mota,
            "motp": self.motp,
            "idf1": self.idf1,
            "precision": self.precision,
            "recall": self.recall,
            "num_switches": self.num_switches,
            "num_fragmentations": self.num_fragmentations,
            "mostly_tracked": self.mostly_tracked,
            "partially_tracked": self.partially_tracked,
            "mostly_lost": self.mostly_lost,
            "num_false_positives": self.num_false_positives,
            "num_misses": self.num_misses,
            "num_matches": self.num_matches,
            "num_unique_objects": self.num_unique_objects,
        }


def load_mot(path: str | Path) -> dict[int, MotFrame]:
    """Parse a MOT-format track file grouped by 1-based frame number.

    Args:
        path: Path to a MOT-challenge text file.

    Returns:
        A mapping from frame number to the `MotFrame` for that frame. Frames
        with no rows are absent from the mapping.

    Raises:
        ValueError: If a non-empty line has fewer than six columns.
    """
    path = Path(path)
    ids: dict[int, list[int]] = defaultdict(list)
    boxes: dict[int, list[list[float]]] = defaultdict(list)
    for lineno, raw in enumerate(path.read_text().splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        parts = line.split(",")
        if len(parts) < _MOT_MIN_COLS:
            msg = f"{path}:{lineno}: expected at least {_MOT_MIN_COLS} comma-separated values; got {len(parts)}"
            raise ValueError(msg)
        frame = int(float(parts[0]))
        track_id = int(float(parts[1]))
        x, y, w, h = (float(v) for v in parts[2:6])
        ids[frame].append(track_id)
        boxes[frame].append([x, y, w, h])
    return {
        frame: MotFrame(
            ids=np.asarray(ids[frame], dtype=np.int64),
            boxes=np.asarray(boxes[frame], dtype=np.float64),
        )
        for frame in ids
    }


def iou_distance_matrix(
    objs: np.ndarray,
    hyps: np.ndarray,
    max_iou_distance: float = 0.5,
) -> np.ndarray:
    """Compute a ``1 - IoU`` distance matrix between two sets of boxes.

    Boxes are ``xywh`` (top-left corner plus width and height). Pairs whose
    distance exceeds ``max_iou_distance`` are set to ``np.nan``.

    Args:
        objs: ``(M, 4)`` ground-truth boxes in ``xywh`` format.
        hyps: ``(N, 4)`` hypothesis boxes in ``xywh`` format.
        max_iou_distance: Largest ``1 - IoU`` distance accepted as a match.
            A value of 0.5 requires ``IoU >= 0.5``.

    Returns:
        An ``(M, N)`` float64 distance matrix; disallowed pairs are ``np.nan``.
    """
    objs = np.asarray(objs, dtype=np.float64).reshape(-1, 4)
    hyps = np.asarray(hyps, dtype=np.float64).reshape(-1, 4)
    if objs.shape[0] == 0 or hyps.shape[0] == 0:
        return np.empty((objs.shape[0], hyps.shape[0]), dtype=np.float64)

    obj_xyxy = objs.copy()
    obj_xyxy[:, 2:] += obj_xyxy[:, :2]
    hyp_xyxy = hyps.copy()
    hyp_xyxy[:, 2:] += hyp_xyxy[:, :2]

    inter_x1 = np.maximum(obj_xyxy[:, None, 0], hyp_xyxy[None, :, 0])
    inter_y1 = np.maximum(obj_xyxy[:, None, 1], hyp_xyxy[None, :, 1])
    inter_x2 = np.minimum(obj_xyxy[:, None, 2], hyp_xyxy[None, :, 2])
    inter_y2 = np.minimum(obj_xyxy[:, None, 3], hyp_xyxy[None, :, 3])
    inter_w = np.clip(inter_x2 - inter_x1, a_min=0.0, a_max=None)
    inter_h = np.clip(inter_y2 - inter_y1, a_min=0.0, a_max=None)
    intersection = inter_w * inter_h

    area_obj = (objs[:, 2] * objs[:, 3])[:, None]
    area_hyp = (hyps[:, 2] * hyps[:, 3])[None, :]
    union = area_obj + area_hyp - intersection

    iou = np.where(union > 0.0, intersection / np.where(union > 0.0, union, 1.0), 0.0)
    distances = 1.0 - iou
    distances[distances > max_iou_distance] = np.nan
    return distances


def evaluate_mot(
    ground_truth: dict[int, MotFrame],
    predictions: dict[int, MotFrame],
    *,
    iou_threshold: float = 0.5,
    name: str = "sequence",
) -> MotMetrics:
    """Evaluate predicted tracks against ground truth with CLEAR-MOT metrics.

    Frames are the union of both inputs; a frame missing from one side
    contributes an empty box set (pure misses or false positives). Matching
    is IoU-based: a ground-truth/hypothesis pair may match only when their
    ``IoU`` is at least ``iou_threshold``.

    Args:
        ground_truth: Per-frame ground-truth tracks.
        predictions: Per-frame predicted tracks.
        iou_threshold: Minimum IoU for a valid match, in ``[0, 1]``.
        name: Label attached to the returned summary.

    Returns:
        The `MotMetrics` summary for the sequence.
    """
    max_iou_distance = 1.0 - iou_threshold
    accumulator = mm.MOTAccumulator(auto_id=True)
    frames = sorted(set(ground_truth) | set(predictions))
    empty_boxes = np.empty((0, 4), dtype=np.float64)
    empty_ids = np.empty((0,), dtype=np.int64)
    for frame in frames:
        gt = ground_truth.get(frame)
        pred = predictions.get(frame)
        gt_ids = gt.ids if gt is not None else empty_ids
        pred_ids = pred.ids if pred is not None else empty_ids
        gt_boxes = gt.boxes if gt is not None else empty_boxes
        pred_boxes = pred.boxes if pred is not None else empty_boxes
        distances = iou_distance_matrix(gt_boxes, pred_boxes, max_iou_distance)
        accumulator.update(gt_ids.tolist(), pred_ids.tolist(), distances)

    handler = mm.metrics.create()
    summary = cast("pd.DataFrame", handler.compute(accumulator, metrics=list(_METRIC_FIELDS), name=name))
    row = summary.loc[name]

    def _float(field: str) -> float:
        value = float(cast("float", row[field]))
        return 0.0 if math.isnan(value) else value

    def _optional_float(field: str) -> float | None:
        value = float(cast("float", row[field]))
        return None if math.isnan(value) else value

    def _int(field: str) -> int:
        value = float(cast("float", row[field]))
        return 0 if math.isnan(value) else int(value)

    return MotMetrics(
        mota=_float("mota"),
        motp=_optional_float("motp"),
        idf1=_float("idf1"),
        precision=_float("precision"),
        recall=_float("recall"),
        num_switches=_int("num_switches"),
        num_fragmentations=_int("num_fragmentations"),
        mostly_tracked=_int("mostly_tracked"),
        partially_tracked=_int("partially_tracked"),
        mostly_lost=_int("mostly_lost"),
        num_false_positives=_int("num_false_positives"),
        num_misses=_int("num_misses"),
        num_matches=_int("num_matches"),
        num_unique_objects=_int("num_unique_objects"),
    )
