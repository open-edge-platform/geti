# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Tests for getitrack.cli."""

from pathlib import Path

import numpy as np
from typer.testing import CliRunner

from getitrack.cli import app
from getitrack.io import VideoReader, VideoWriter

runner = CliRunner()

_W, _H = 128, 96


def _make_video(path, n_frames) -> Path:
    with VideoWriter(path, fps=30.0, frame_size=(_W, _H)) as writer:
        for _ in range(n_frames):
            writer.write(np.full((_H, _W, 3), 30, dtype=np.uint8))
    return path


def _make_mot_detections(path, n_frames) -> Path:
    """Two boxes drifting horizontally in opposite directions, score 0.9."""
    lines = []
    for frame in range(1, n_frames + 1):
        x1 = 5 + 2 * frame
        x2 = 80 - 2 * frame
        lines.append(f"{frame},-1,{x1},10,20,20,0.9,0")
        lines.append(f"{frame},-1,{x2},50,20,20,0.9,0")
    path.write_text("\n".join(lines) + "\n")
    return path


def _make_config(path) -> Path:
    path.write_text("lifecycle:\n  min_hits: 1\n")
    return path


class TestTrack:
    def test_headless_writes_mot_results(self, tmp_path):
        n_frames = 8
        dets = _make_mot_detections(tmp_path / "det.txt", n_frames)
        cfg = _make_config(tmp_path / "cfg.yaml")
        out = tmp_path / "tracks.txt"
        result = runner.invoke(app, ["track", "--detections", str(dets), "--config", str(cfg), "--output", str(out)])
        assert result.exit_code == 0, result.output
        rows = [line.split(",") for line in out.read_text().splitlines()]
        # min_hits=1 promotes immediately: 2 tracks on every frame.
        assert len(rows) == 2 * n_frames
        assert {int(r[1]) for r in rows} == {1, 2}
        assert "2 tracks" in result.output

    def test_default_output_path(self, tmp_path):
        dets = _make_mot_detections(tmp_path / "det.txt", 4)
        result = runner.invoke(app, ["track", "--detections", str(dets)])
        assert result.exit_code == 0, result.output
        assert (tmp_path / "det_tracks.txt").is_file()

    def test_with_video_and_output_video(self, tmp_path):
        n_frames = 6
        video = _make_video(tmp_path / "clip.mp4", n_frames)
        dets = _make_mot_detections(tmp_path / "det.txt", n_frames)
        out_video = tmp_path / "annotated.mp4"
        result = runner.invoke(
            app,
            ["track", "--detections", str(dets), "--video", str(video), "--output-video", str(out_video)],
        )
        assert result.exit_code == 0, result.output
        with VideoReader(out_video) as reader:
            assert len(list(reader)) == n_frames

    def test_output_video_without_video_fails(self, tmp_path):
        dets = _make_mot_detections(tmp_path / "det.txt", 3)
        result = runner.invoke(
            app,
            ["track", "--detections", str(dets), "--output-video", str(tmp_path / "out.mp4")],
        )
        assert result.exit_code != 0

    def test_missing_detections_file_fails(self, tmp_path):
        result = runner.invoke(app, ["track", "--detections", str(tmp_path / "nope.txt")])
        assert result.exit_code != 0

    def test_malformed_detection_line_fails(self, tmp_path):
        bad = tmp_path / "det.txt"
        bad.write_text("1,2,3\n")
        result = runner.invoke(app, ["track", "--detections", str(bad)])
        assert result.exit_code != 0

    def test_explicit_algorithm(self, tmp_path):
        dets = _make_mot_detections(tmp_path / "det.txt", 3)
        result = runner.invoke(app, ["track", "--detections", str(dets), "--algorithm", "bytetrack"])
        assert result.exit_code == 0, result.output

    def test_unknown_algorithm_fails(self, tmp_path):
        dets = _make_mot_detections(tmp_path / "det.txt", 2)
        result = runner.invoke(app, ["track", "--detections", str(dets), "--algorithm", "nope"])
        assert result.exit_code != 0

    def test_algorithm_overrides_config(self, tmp_path):
        # The config names an unregistered algorithm; --algorithm overrides it.
        dets = _make_mot_detections(tmp_path / "det.txt", 3)
        cfg = tmp_path / "cfg.yaml"
        cfg.write_text("algorithm: nope\nlifecycle:\n  min_hits: 1\n")
        result = runner.invoke(
            app,
            ["track", "--detections", str(dets), "--config", str(cfg), "--algorithm", "bytetrack"],
        )
        assert result.exit_code == 0, result.output

    def test_bad_algorithm_override_over_valid_config_fails(self, tmp_path):
        dets = _make_mot_detections(tmp_path / "det.txt", 2)
        cfg = _make_config(tmp_path / "cfg.yaml")
        result = runner.invoke(
            app,
            ["track", "--detections", str(dets), "--config", str(cfg), "--algorithm", "nope"],
        )
        assert result.exit_code != 0


class TestEval:
    @staticmethod
    def _write_seq(path: Path, n_frames: int, *, swap_from: int | None = None) -> Path:
        lines = []
        for frame in range(1, n_frames + 1):
            first = 2 if swap_from is not None and frame >= swap_from else 1
            second = 1 if swap_from is not None and frame >= swap_from else 2
            lines.append(f"{frame},{first},10,10,20,20,1,0,1")
            lines.append(f"{frame},{second},80,80,20,20,1,0,1")
        path.write_text("\n".join(lines) + "\n")
        return path

    def test_perfect_metrics(self, tmp_path):
        gt = self._write_seq(tmp_path / "gt.txt", 5)
        result = runner.invoke(app, ["eval", "--predictions", str(gt), "--ground-truth", str(gt)])
        assert result.exit_code == 0, result.output
        assert "mota" in result.output
        assert "| mota | 1.0000 |" in result.output
        assert "| num_switches | 0 |" in result.output

    def test_id_swap_reports_switches(self, tmp_path):
        gt = self._write_seq(tmp_path / "gt.txt", 6)
        pred = self._write_seq(tmp_path / "pred.txt", 6, swap_from=4)
        result = runner.invoke(app, ["eval", "--predictions", str(pred), "--ground-truth", str(gt)])
        assert result.exit_code == 0, result.output
        assert "| num_switches | 2 |" in result.output

    def test_writes_json_output(self, tmp_path):
        import json

        gt = self._write_seq(tmp_path / "gt.txt", 4)
        out = tmp_path / "metrics.json"
        result = runner.invoke(
            app,
            ["eval", "--predictions", str(gt), "--ground-truth", str(gt), "--output", str(out)],
        )
        assert result.exit_code == 0, result.output
        data = json.loads(out.read_text())
        assert data["mota"] == 1.0
        assert data["num_switches"] == 0

    def test_missing_ground_truth_fails(self, tmp_path):
        gt = self._write_seq(tmp_path / "gt.txt", 2)
        result = runner.invoke(app, ["eval", "--predictions", str(gt), "--ground-truth", str(tmp_path / "nope.txt")])
        assert result.exit_code != 0

    def test_iou_threshold_flows_through(self, tmp_path):
        # GT and pred boxes overlap with IoU = 1/3: a match at 0.3, a miss at 0.7.
        gt = tmp_path / "gt.txt"
        pred = tmp_path / "pred.txt"
        gt.write_text("1,1,0,0,10,10,1,0,1\n")
        pred.write_text("1,1,0,5,10,10,1,0,1\n")

        loose = runner.invoke(
            app,
            ["eval", "--predictions", str(pred), "--ground-truth", str(gt), "--iou-threshold", "0.3"],
        )
        assert loose.exit_code == 0, loose.output
        assert "| num_misses | 0 |" in loose.output

        strict = runner.invoke(
            app,
            ["eval", "--predictions", str(pred), "--ground-truth", str(gt), "--iou-threshold", "0.7"],
        )
        assert strict.exit_code == 0, strict.output
        assert "| num_misses | 1 |" in strict.output
        assert "| motp | N/A |" in strict.output


class TestHelp:
    def test_lists_commands(self):
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "track" in result.output
        assert "eval" in result.output

    def test_track_help(self):
        result = runner.invoke(app, ["track", "--help"])
        assert result.exit_code == 0
        assert "--detections" in result.output

    def test_eval_help(self):
        result = runner.invoke(app, ["eval", "--help"])
        assert result.exit_code == 0
        assert "--predictions" in result.output
        assert "--ground-truth" in result.output
