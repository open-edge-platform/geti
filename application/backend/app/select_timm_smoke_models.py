#!/usr/bin/env python3
# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Select one lightweight representative model per timm architecture family.

For each distinct ``family`` in ``timm_catalog_snapshot.json``, picks the
backbone with the lowest ``gigaflops``, so the resulting set is cheap to
train while still covering every architectural family at least once. Families
whose lightest backbone exceeds ``--max-gigaflops`` are skipped (and reported on
stderr) because they cannot be trained on the CPU CI runner. Used to seed the
smoke-test suite in ``tests/bdd/features/timm_training.feature``.

Usage (from ``application/backend/``)::

    uv run python app/select_timm_smoke_models.py
    uv run python app/select_timm_smoke_models.py --format gherkin
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

_DEFAULT_SNAPSHOT = Path(__file__).resolve().parent / "supported_models" / "timm_catalog_snapshot.json"
# Families whose lightest backbone exceeds this budget get OOM-killed when training on the CPU CI runner
# (samvit_base: 972, gemma4_vit: 771, mobilenetv5: 871 GFLOPs). The heaviest family that trains fine is
# sam2_hiera at 148 GFLOPs, so this value sits in the gap with headroom for new families.
_DEFAULT_MAX_GIGAFLOPS = 300.0


def select_lightest_per_family(
    snapshot_path: Path, max_gigaflops: float | None = None
) -> tuple[list[tuple[str, str]], list[tuple[str, str, float]]]:
    """Select the backbone with the lowest gigaflops for each timm family.

    Args:
        snapshot_path: Path to the timm catalog snapshot JSON.
        max_gigaflops: Optional compute budget. Families whose lightest backbone exceeds it are skipped,
            since every other backbone of that family is heavier. ``None`` disables the filter.

    Returns:
        A tuple ``(selected, skipped)`` where ``selected`` is a sorted list of ``(family, model_name)``
        and ``skipped`` is a sorted list of ``(family, model_name, gigaflops)`` exceeding the budget.
    """
    data = json.loads(snapshot_path.read_text(encoding="utf-8"))
    lightest_by_family: dict[str, dict] = {}

    for entry in data["backbones"]:
        family = entry["family"]
        current = lightest_by_family.get(family)
        if current is None or entry["gigaflops"] < current["gigaflops"]:
            lightest_by_family[family] = entry

    selected: list[tuple[str, str]] = []
    skipped: list[tuple[str, str, float]] = []
    for family, entry in sorted(lightest_by_family.items()):
        if max_gigaflops is not None and entry["gigaflops"] > max_gigaflops:
            skipped.append((family, entry["model_name"], entry["gigaflops"]))
        else:
            selected.append((family, entry["model_name"]))
    return selected, skipped


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, default=_DEFAULT_SNAPSHOT, help="Path to the timm catalog snapshot.")
    parser.add_argument(
        "--max-gigaflops",
        type=float,
        default=_DEFAULT_MAX_GIGAFLOPS,
        help="Skip families whose lightest backbone exceeds this compute budget (default: %(default)s).",
    )
    parser.add_argument(
        "--format",
        choices=["python", "gherkin"],
        default="python",
        help="Output format: 'python' for a repr'd list of tuples, 'gherkin' for an Examples table.",
    )
    return parser.parse_args()


def _format_gherkin_table(headers: list[str], rows: Sequence[tuple[str, ...]], indent: str = "      ") -> str:
    """Render *rows* as a column-aligned Gherkin table with *headers*, matching standard Gherkin style.

    Each column is padded to the width of its longest cell (header included), and cells are
    left-aligned with a single space of padding on each side of the `|` separators, e.g.::

        | family  | model_architecture_id   |
        | byobnet | bat_resnext26ts.ch_in1k |
        | resnet  | resnet10t.c3_in1k       |
    """
    columns = list(zip(headers, *rows, strict=True)) if rows else [(h,) for h in headers]
    widths = [max(len(str(cell)) for cell in column) for column in columns]

    def _format_row(cells: tuple[str, ...]) -> str:
        padded = (str(cell).ljust(width) for cell, width in zip(cells, widths, strict=True))
        return f"{indent}| " + " | ".join(padded) + " |"

    lines = [_format_row(tuple(headers)), *(_format_row(row) for row in rows)]
    return "\n".join(lines)


def main() -> None:
    """Entry point for the script."""
    args = _parse_args()
    selection, skipped = select_lightest_per_family(args.snapshot, max_gigaflops=args.max_gigaflops)

    # Report skipped families on stderr so stdout stays a clean, pasteable table.
    for family, model_name, gigaflops in skipped:
        print(
            f"Skipped {family} ({model_name}, {gigaflops} GFLOPs > {args.max_gigaflops})",
            file=sys.stderr,
        )

    if args.format == "gherkin":
        print(_format_gherkin_table(["family", "model_architecture_id"], selection))
    else:
        print(f"{len(selection)} families:")
        for pair in selection:
            print(pair)


if __name__ == "__main__":
    main()
