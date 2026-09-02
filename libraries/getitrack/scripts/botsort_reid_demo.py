# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""End-to-end BoT-SORT demo: appearance (ReID) + camera-motion compensation.

Runs BoT-SORT over a video and writes an annotated H.264 clip plus a run log.
Detections come from OpenCV's built-in HOG people detector, so the only model
weights needed are torchreid's (downloaded on first use). Use it to smoke both
ReID backends and GMC on real footage::

    python scripts/botsort_reid_demo.py --video clip.mp4 --backend torch --model-name osnet_x1_0
    python scripts/botsort_reid_demo.py --video clip.mp4 --backend openvino --model-name osnet_x1_0 --no-gmc

The torch backend runs the torchreid model natively; the openvino backend runs
an IR auto-exported and cached from it. Install the extra first: ``pip install
-e ".[reid]"``. H.264 output requires ``ffmpeg`` on PATH (falls back to mp4v with
a warning otherwise).
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import shutil
import subprocess
import time
from dataclasses import replace
from pathlib import Path

import cv2
import numpy as np

from getitrack.algorithms import BotSortTracker
from getitrack.algorithms.configs.botsort import BotSortConfig
from getitrack.config import GMCConfig, GMCMethod, LifecycleConfig, ReIDBackend, ReIDConfig
from getitrack.core.detection import Detections, TrackedDetections

_LOGGER = logging.getLogger(__name__)
_RESULTS_ROOT = Path(__file__).resolve().parents[1] / "results" / "botsort_reid_demo"


def _palette(track_id: int) -> tuple[int, int, int]:
    """Deterministic BGR colour per track id."""
    rng = np.random.default_rng(track_id * 2654435761 % (2**32))
    r, g, b = (int(c) for c in rng.integers(64, 256, size=3))
    return (b, g, r)


def _detect_people(hog: cv2.HOGDescriptor, frame: np.ndarray, frame_id: int) -> Detections:
    """Detect people in ``frame`` with HOG and return them as `Detections`."""
    rects, weights = hog.detectMultiScale(frame, winStride=(8, 8), padding=(8, 8), scale=1.05)
    if len(rects) == 0:
        return Detections.create_empty(frame_id=frame_id)
    boxes = np.array([[x, y, x + w, y + h] for (x, y, w, h) in rects], dtype=np.float32)
    scores = 1.0 / (1.0 + np.exp(-np.asarray(weights, dtype=np.float32).reshape(-1)))
    return Detections(
        bboxes=boxes,
        scores=scores.astype(np.float32),
        class_ids=np.zeros(len(boxes), dtype=np.int64),
        frame_id=frame_id,
    )


def _draw_tracks(frame: np.ndarray, tracked: TrackedDetections) -> None:
    """Draw each track's box and id onto ``frame`` in place."""
    for box, tid in zip(tracked.bboxes.astype(int), tracked.track_ids.tolist(), strict=True):
        colour = _palette(tid)
        cv2.rectangle(frame, (box[0], box[1]), (box[2], box[3]), colour, 2)
        cv2.putText(frame, f"id {tid}", (box[0], box[1] - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.6, colour, 2)


def _build_tracker(backend: str, model_name: str, *, use_gmc: bool) -> BotSortTracker:
    reid = ReIDConfig(enabled=True, backend=ReIDBackend(backend), model_name=model_name)
    gmc = GMCConfig(enabled=use_gmc, method=GMCMethod.SPARSE_OPT_FLOW)
    config = BotSortConfig(reid=reid, gmc=gmc, lifecycle=LifecycleConfig(min_hits=2, max_age=30))
    return BotSortTracker(config)


def _transcode_h264(src: Path, dst: Path) -> bool:
    """Transcode ``src`` to H.264 yuv420p ``dst`` with ffmpeg; return success."""
    if shutil.which("ffmpeg") is None:
        return False
    cmd = ["ffmpeg", "-y", "-i", str(src), "-c:v", "libx264", "-pix_fmt", "yuv420p", str(dst)]
    return subprocess.run(cmd, capture_output=True, check=False).returncode == 0  # noqa: S603  # fixed command


def run(args: argparse.Namespace) -> None:
    """Track the video with BoT-SORT and write the annotated clip plus the run log."""
    out_dir = _RESULTS_ROOT / f"{args.backend}{'_gmc' if not args.no_gmc else ''}"
    out_dir.mkdir(parents=True, exist_ok=True)

    capture = cv2.VideoCapture(args.video)
    if not capture.isOpened():
        msg = f"could not open video: {args.video}"
        raise SystemExit(msg)
    fps = capture.get(cv2.CAP_PROP_FPS) or 30.0
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))

    hog = cv2.HOGDescriptor()
    hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
    tracker = _build_tracker(args.backend, args.model_name, use_gmc=not args.no_gmc)

    raw_path = out_dir / "annotated_raw.mp4"
    writer = cv2.VideoWriter(str(raw_path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))

    rows: list[dict[str, object]] = []
    frame_id = 0
    max_track_id = 0
    started = time.perf_counter()
    while True:
        ok, frame = capture.read()
        if not ok or (args.max_frames and frame_id >= args.max_frames):
            break
        dets = _detect_people(hog, frame, frame_id)
        provider = tracker.reid_provider
        if provider is not None and len(dets.bboxes) > 0:
            dets = replace(dets, embeddings=provider.extract(frame, dets.bboxes))
        warp = tracker.apply_camera_motion(frame)
        tracked = tracker.update(dets)
        if len(tracked.track_ids) > 0:
            max_track_id = max(max_track_id, int(tracked.track_ids.max()))
        _draw_tracks(frame, tracked)
        writer.write(frame)
        rows.append(
            {
                "frame": frame_id,
                "detections": len(dets.bboxes),
                "tracks": len(tracked.track_ids),
                "warp_tx": None if warp is None else round(float(warp[0, 2]), 3),
                "warp_ty": None if warp is None else round(float(warp[1, 2]), 3),
            }
        )
        frame_id += 1

    capture.release()
    writer.release()
    elapsed = time.perf_counter() - started

    final_path = out_dir / "annotated.mp4"
    if _transcode_h264(raw_path, final_path):
        raw_path.unlink(missing_ok=True)
    else:
        final_path = raw_path
        _LOGGER.warning("ffmpeg not found or failed; leaving mp4v output (may not play in some viewers).")

    with (out_dir / "frames.csv").open("w", newline="") as handle:
        fieldnames = ["frame", "detections", "tracks", "warp_tx", "warp_ty"]
        csv_writer = csv.DictWriter(handle, fieldnames=fieldnames)
        csv_writer.writeheader()
        csv_writer.writerows(rows)
    summary = {
        "video": args.video,
        "backend": args.backend,
        "model_name": args.model_name,
        "gmc": not args.no_gmc,
        "frames": frame_id,
        "total_detections": sum(int(r["detections"]) for r in rows),
        "max_track_id": max_track_id,
        "max_active_tracks": max((int(r["tracks"]) for r in rows), default=0),
        "elapsed_s": round(elapsed, 2),
        "fps": round(frame_id / elapsed, 2) if elapsed > 0 else None,
        "output_video": str(final_path),
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


def main() -> None:
    """Parse arguments and run the demo."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video", required=True, help="Path to the input video.")
    parser.add_argument("--backend", choices=["torch", "openvino"], default="torch", help="ReID inference backend.")
    parser.add_argument("--model-name", default="osnet_x1_0", help="torchreid architecture name.")
    parser.add_argument("--no-gmc", action="store_true", help="Disable camera-motion compensation.")
    parser.add_argument("--max-frames", type=int, default=0, help="Process at most this many frames (0 = all).")
    run(parser.parse_args())


if __name__ == "__main__":
    main()
