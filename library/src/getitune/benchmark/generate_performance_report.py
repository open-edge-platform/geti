# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Generate a performance-only report from benchmark artifacts.

This utility intentionally does not evaluate accuracy. It is for hardware and
runtime performance comparisons where accuracy is not part of the report:
training iteration time, OpenVINO throughput, and OpenVINO latency.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from contextlib import suppress
from pathlib import Path


def _read_json(path: Path) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _read_training_config(path: Path) -> dict[str, object]:
    """Read training device and batch size from the benchmark hparams YAML."""
    try:
        import yaml

        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return {}
    return data if isinstance(data, dict) else {}


def _training_metadata(seed_dir: Path) -> tuple[str, object]:
    """Return real training device and configured training batch size."""
    hparams = next(iter(sorted((seed_dir / "train").glob("csv/version_*/hparams.yaml"))), None)
    if hparams is None:
        return "unknown", "-"
    config = _read_training_config(hparams)
    train_subset = config.get("train_subset", {})
    batch_size = train_subset.get("batch_size", "-") if isinstance(train_subset, dict) else "-"
    return str(config.get("device", "unknown")), batch_size


def _read_training_iter_time(path: Path) -> float | None:
    """Read post-warmup train iteration time from the latest metrics CSV."""
    candidates = sorted(path.glob("csv/version_*/metrics.csv"))
    if not candidates:
        return None
    try:
        with candidates[-1].open(newline="", encoding="utf-8") as stream:
            rows = list(csv.DictReader(stream))
    except OSError:
        return None
    values = []
    for row in rows:
        value = row.get("train/iter_time")
        if value:
            try:
                values.append(float(value))
            except ValueError:
                continue
    if not values:
        return None
    return sum(values[1:] or values) / len(values[1:] or values)


def _benchmark_metrics(seed_dir: Path, relative: str) -> dict[str, object]:
    """Read normalized metrics, falling back to benchmark-app's raw report."""
    result = _read_json(seed_dir / relative)
    if result:
        return result

    report = _read_json(seed_dir / relative.replace("result.json", "benchmark_report.json"))
    execution = report.get("execution_results", {})
    if not isinstance(execution, dict) or execution.get("error"):
        return {}

    prefix = "export" if "export" in relative else "optimize"
    mode = "throughput" if "throughput" in relative else "latency"
    values: dict[str, object] = {}
    for source, target in (
        ("throughput", "fps"),
        ("latency (ms)", "latency_ms"),
        ("avg latency", "avg_latency_ms"),
        ("total execution time (ms)", "duration_ms"),
        ("total number of iterations", "iterations"),
    ):
        value = execution.get(source)
        if isinstance(value, (int, float)):
            values[f"{prefix}:{mode}:{target}"] = float(value)
        elif isinstance(value, str):
            with suppress(IndexError, ValueError):
                values[f"{prefix}:{mode}:{target}"] = float(value.split()[0])
    return values


def _collect(result_root: Path) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    rows: list[dict[str, object]] = []
    incomplete: list[dict[str, object]] = []
    required = {
        "FP throughput": "benchmark/export/throughput/result.json",
        "FP latency": "benchmark/export/latency/result.json",
        "INT8 throughput": "benchmark/optimize/throughput/result.json",
        "INT8 latency": "benchmark/optimize/latency/result.json",
    }
    for train_csv in result_root.glob("**/0/train/csv/version_*/metrics.csv"):
        seed_dir = train_csv.parents[3]
        parts = seed_dir.relative_to(result_root).parts
        if len(parts) < 4:
            continue
        task = "/".join(parts[:-3])
        model, dataset, _seed = parts[-3:]
        device, batch_size = _training_metadata(seed_dir)
        row: dict[str, object] = {"task": task, "model": model, "dataset": dataset, "hardware": device}
        row["training_batch_size"] = batch_size
        row["training:train/iter_time"] = _read_training_iter_time(seed_dir / "train")
        missing: list[str] = []
        # Result files contain flat metrics; use their keys directly.
        for label, relative in required.items():
            data = _benchmark_metrics(seed_dir, relative)
            prefix = "export" if "export" in relative else "optimize"
            mode = "throughput" if "throughput" in relative else "latency"
            found = False
            for metric in ("fps", "latency_ms"):
                value = data.get(f"{prefix}:{mode}:{metric}")
                if isinstance(value, (int, float)):
                    row[f"{prefix}:{mode}:{metric}"] = value
                    found = True
            if not found:
                missing.append(label)
        rows.append(row)
        if missing:
            incomplete.append({**row, "missing": ", ".join(missing)})
    return rows, incomplete


def _fmt(value: object, digits: int = 2) -> str:
    return "-" if value is None else f"{float(value):.{digits}f}"


def generate_performance_report(result_roots: list[Path], output: Path) -> None:
    """Write a performance-only report combining all supplied result roots."""
    rows: list[dict[str, object]] = []
    incomplete: list[dict[str, object]] = []
    for root in result_roots:
        complete, missing = _collect(root)
        rows.extend(complete)
        incomplete.extend(missing)

    by_task: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        by_task[str(row["task"])].append(row)

    lines = [
        "# GetiTune Performance Report",
        "",
        "> Performance-only report. Accuracy metrics are intentionally excluded.",
        "> Use this report for hardware/runtime comparisons when accuracy is not important.",
        "",
        f"Complete results: **{len(rows)}**",
        f"Incomplete results: **{len(incomplete)}**",
        "",
    ]
    for task, task_rows in sorted(by_task.items()):
        lines.extend(
            [
                f"## {task}",
                "",
                "| Model | Hardware | Train batch | Train iter (s) | FP FPS | FP latency (ms) | "
                "INT8 FPS | INT8 latency (ms) |",
                "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        lines.extend(
            f"| {row['model']} | {row['hardware']} | {row['training_batch_size']} | "
            f"{_fmt(row.get('training:train/iter_time'))} | "
            f"{_fmt(row.get('export:throughput:fps'))} | "
            f"{_fmt(row.get('export:latency:latency_ms'))} | "
            f"{_fmt(row.get('optimize:throughput:fps'))} | "
            f"{_fmt(row.get('optimize:latency:latency_ms'))} |"
            for row in sorted(task_rows, key=lambda item: (str(item["model"]), str(item["hardware"])))
        )
        lines.append("")

    if incomplete:
        lines.extend(
            [
                "## Incomplete Cases",
                "",
                "| Model | Hardware | Missing |",
                "| --- | --- | --- |",
            ]
        )
        lines.extend(
            f"| {row['model']} | {row['hardware']} | {row['missing']} |"
            for row in sorted(incomplete, key=lambda item: (str(item["task"]), str(item["model"])))
        )
        lines.append("")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    """Parse command-line arguments and generate a performance-only report."""
    parser = argparse.ArgumentParser(
        description="Generate a performance-only report; accuracy is intentionally not evaluated."
    )
    parser.add_argument("result_roots", type=Path, nargs="+", help="Benchmark result directories to scan.")
    parser.add_argument(
        "--output", type=Path, default=Path("performance_report.md"), help="Output Markdown path."
    )
    args = parser.parse_args()
    generate_performance_report(args.result_roots, args.output)


if __name__ == "__main__":
    main()
