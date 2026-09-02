# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Generate a performance-only Markdown report from structured benchmark results."""

from __future__ import annotations

import argparse
import json
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

_REQUIRED_FIELDS = {
    "schema_version",
    "task",
    "model",
    "dataset",
    "scenario",
    "seed",
    "training_device",
    "training_batch_size",
    "openvino_device",
    "git_sha",
    "software",
    "fp16",
    "int8",
}


def _load_result(path: Path) -> dict[str, Any]:
    """Load and validate one canonical performance result."""
    try:
        result = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        msg = f"Could not read performance result: {path}"
        raise ValueError(msg) from exc
    if not isinstance(result, dict):
        msg = f"Performance result must be a JSON object: {path}"
        raise TypeError(msg)
    missing = _REQUIRED_FIELDS - result.keys()
    if missing:
        msg = f"Performance result {path} is missing required fields: {sorted(missing)}"
        raise ValueError(msg)
    for precision, expected in (("fp16", "FP16"), ("int8", "INT8")):
        section = result[precision]
        required = {"precision", "inference_batch_size", "throughput_fps", "latency_ms"}
        if not isinstance(section, dict) or not required <= section.keys():
            msg = f"Performance result {path} has an incomplete {precision} section."
            raise ValueError(msg)
        if section["precision"] != expected:
            msg = f"Performance result {path} expected {expected}, got {section['precision']}."
            raise ValueError(msg)
        numeric = (section["inference_batch_size"], section["throughput_fps"], section["latency_ms"])
        if not all(isinstance(value, (int, float)) and value > 0 for value in numeric):
            msg = f"Performance result {path} has nonpositive {precision} measurements."
            raise ValueError(msg)
    device_names = (str(result["training_device"]).strip(), str(result["openvino_device"]).strip())
    logical_names = {"", "unknown", "auto", "cpu", "gpu", "xpu", "cuda", "mps"}
    if any(name.lower() in logical_names for name in device_names):
        msg = f"Performance result {path} has a missing physical device name."
        raise ValueError(msg)
    if not isinstance(result["training_batch_size"], int) or result["training_batch_size"] < 1:
        msg = f"Performance result {path} has an invalid training batch size."
        raise ValueError(msg)
    software = result["software"]
    required_software = {"python", "getitune", "torch", "openvino", "nncf"}
    if not isinstance(software, dict) or not required_software <= software.keys():
        msg = f"Performance result {path} has incomplete software metadata."
        raise ValueError(msg)
    return result


def _training_iter_ms(seed_dir: Path) -> float:
    """Return post-warmup training iteration time in milliseconds."""
    import csv

    metrics_files = sorted((seed_dir / "train").glob("csv/version_*/metrics.csv"))
    if not metrics_files:
        msg = f"Training metrics not found for performance result: {seed_dir}"
        raise ValueError(msg)
    with metrics_files[-1].open(newline="", encoding="utf-8") as stream:
        values = [float(row["train/iter_time"]) for row in csv.DictReader(stream) if row.get("train/iter_time")]
    if not values:
        msg = f"train/iter_time is missing from {metrics_files[-1]}"
        raise ValueError(msg)
    measured = values[1:] or values
    return 1000 * sum(measured) / len(measured)


def generate_performance_report(result_roots: list[Path], output: Path) -> None:
    """Combine canonical seed results into a strict performance-only report."""
    rows: list[dict[str, Any]] = []
    for root in result_roots:
        files = sorted(root.glob("**/performance_result.json"))
        if not files:
            msg = f"No performance_result.json files found under {root}"
            raise ValueError(msg)
        for path in files:
            result = _load_result(path)
            result["training_iter_ms"] = _training_iter_ms(path.parent)
            rows.append(result)

    model_groups: dict[tuple[object, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = (
            row["task"],
            row["model"],
            row["dataset"],
            row["scenario"],
            row["training_device"],
            row["openvino_device"],
            row["training_batch_size"],
            row["fp16"]["inference_batch_size"],
        )
        model_groups[key].append(row)

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for model_rows in model_groups.values():
        representative = dict(model_rows[0])
        fp16 = dict(representative["fp16"])
        int8 = dict(representative["int8"])
        representative["training_iter_ms"] = statistics.mean(row["training_iter_ms"] for row in model_rows)
        fp16["throughput_fps"] = statistics.mean(row["fp16"]["throughput_fps"] for row in model_rows)
        fp16["latency_ms"] = statistics.mean(row["fp16"]["latency_ms"] for row in model_rows)
        int8["throughput_fps"] = statistics.mean(row["int8"]["throughput_fps"] for row in model_rows)
        int8["latency_ms"] = statistics.mean(row["int8"]["latency_ms"] for row in model_rows)
        representative["fp16"] = fp16
        representative["int8"] = int8
        grouped[str(representative["task"])].append(representative)

    for task_rows in grouped.values():
        visible_keys: set[tuple[object, ...]] = set()
        for row in task_rows:
            key = (row["model"], row["training_device"], row["openvino_device"])
            if key in visible_keys:
                msg = (
                    f"Performance report has duplicate visible rows for {row['model']}; "
                    "use one dataset/scenario per model and hardware combination."
                )
                raise ValueError(msg)
            visible_keys.add(key)

    lines = [
        "# GetiTune Performance Report",
        "",
        "> Performance-only report. Accuracy metrics are intentionally excluded.",
        "",
    ]
    environments: dict[tuple[str, str], dict[str, object]] = {}
    for row in rows:
        key = (str(row["training_device"]), str(row["openvino_device"]))
        software = row["software"]
        existing = environments.get(key)
        if existing is not None and existing != software:
            msg = f"Conflicting software versions for training/OpenVINO devices {key}."
            raise ValueError(msg)
        environments[key] = software

    lines.extend(
        [
            "## Software Environment",
            "",
            "| Training Device | OpenVINO Device | Python | PyTorch | OpenVINO |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for (training_device, openvino_device), software in sorted(environments.items()):
        lines.append(
            f"| {training_device} | {openvino_device} | {software['python']} | "
            f"{software['torch']} | {software['openvino']} |"
        )
    lines.append("")

    header = (
        "| Model | Training Device | OpenVINO Device | Train Batch | OV Inference Batch | "
        "Train Iteration (ms) | FP16 FPS | FP Latency (ms) | INT8 FPS | INT8 Latency (ms) |"
    )
    separator = "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"
    for task, task_rows in sorted(grouped.items()):
        lines.extend([f"## {task}", "", header, separator])
        for row in sorted(task_rows, key=lambda item: (str(item["model"]), str(item["training_device"]))):
            fp16 = row["fp16"]
            int8 = row["int8"]
            if fp16["inference_batch_size"] != int8["inference_batch_size"]:
                msg = f"FP16 and INT8 inference batches differ for {row['model']}."
                raise ValueError(msg)
            lines.append(
                f"| {row['model']} | {row['training_device']} | {row['openvino_device']} | "
                f"{row['training_batch_size']} | {fp16['inference_batch_size']} | "
                f"{row['training_iter_ms']:.2f} | {fp16['throughput_fps']:.2f} | "
                f"{fp16['latency_ms']:.2f} | {int8['throughput_fps']:.2f} | {int8['latency_ms']:.2f} |"
            )
        lines.append("")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    """Run the performance report generator CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result_roots", type=Path, nargs="+", help="Benchmark result directories.")
    parser.add_argument("--output", type=Path, default=Path("performance_report.md"))
    args = parser.parse_args()
    generate_performance_report(args.result_roots, args.output)


if __name__ == "__main__":
    main()
