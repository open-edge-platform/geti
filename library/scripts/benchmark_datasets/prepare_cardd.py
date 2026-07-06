#!/usr/bin/env python3
# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Download and prepare the CarDD (car damage) detection benchmark.

Uses the Kaggle dataset "CarDD with YOLO annotations (images + labels)" (a
YOLO-format mirror of CarDD: A Novel Dataset for Vision-based Car Damage
Detection) and exports it in the experimental Datumaro format.

The Kaggle mirror uses the "subset-first" Roboflow-style YOLO layout::

    <root>/data.yaml
    <root>/train/images/*.jpg
    <root>/train/labels/*.txt
    <root>/val/images/*.jpg
    <root>/val/labels/*.txt
    <root>/test/images/*.jpg
    <root>/test/labels/*.txt

with standard fixed-length bounding-box labels (``class_id cx cy w h``,
normalized to ``[0, 1]``) — unlike the ``brain_tumor_instseg`` Kaggle mirror,
this one carries bboxes only (no polygons), so the dataset is prepared as a
**detection** benchmark (6 classes: dent, scratch, crack, glass shatter, lamp
broken, tire flat).

This dataset is gated behind a Kaggle account. Two ways to provide it:

1. Automatic download — requires the ``kagglehub`` package (``pip install kagglehub`` or
   ``uv sync --group kagglehub`` from ``library/``) and API credentials
   configured via the ``KAGGLE_API_TOKEN`` environment variable, or a
   ``~/.kaggle/access_token`` file. See https://www.kaggle.com/docs/api.
2. Manual placement — download the dataset yourself (e.g. from
   https://www.kaggle.com/datasets/gabrielfcarvalho/cardd-with-yolo-annotations-images-labels)
   and pass ``--raw-dir <path>`` pointing at the extracted dataset root to skip
   the network step entirely while still running through this script's
   transform/export logic.
"""

from __future__ import annotations

import shutil
from typing import TYPE_CHECKING

import numpy as np
import yaml
from datumaro.experimental import Dataset, LazyImage
from datumaro.experimental.data_formats.coco.sample import CocoCategories, CocoSample
from datumaro.experimental.export_import import export_dataset
from datumaro.experimental.fields import ImageInfo, Subset
from PIL import Image

from getitune.benchmark.dataset_helpers import (
    download_kaggle_dataset,
    parse_args,
    resolve_raw_source,
)

if TYPE_CHECKING:
    from pathlib import Path

_KAGGLE_DATASET_ID = "gabrielfcarvalho/cardd-with-yolo-annotations-images-labels"

# Roboflow subset directory name -> Datumaro subset. This mirror uses "val"
# (not "valid"); both are accepted for robustness.
_SUBSET_DIR_TO_SUBSET = {
    "train": Subset.TRAINING,
    "valid": Subset.VALIDATION,
    "val": Subset.VALIDATION,
    "test": Subset.TESTING,
}


def _find_yolo_root(root: Path) -> Path:
    """Find a Roboflow-style ``data.yaml`` export root under *root*.

    "subset-first" layout: ``<root>/<subset>/images/`` + ``<root>/<subset>/labels/``
    for each of ``train`` / ``val`` (or ``valid``) / ``test`` — see
    ``prepare_brain_tumor_instseg.py`` for another dataset using this same
    Kaggle/Roboflow export shape.
    """
    candidates = sorted(
        candidate
        for candidate in (path.parent for path in root.rglob("data.yaml"))
        if any((candidate / subset_dir / "images").is_dir() for subset_dir in _SUBSET_DIR_TO_SUBSET)
    )
    if not candidates:
        msg = f"No Roboflow-style YOLO dataset root found under {root}"
        raise RuntimeError(msg)
    return candidates[0]


def _load_label_names(yolo_root: Path) -> tuple[str, ...]:
    """Read class names (in class-id order) from a YOLO ``data.yaml``."""
    with (yolo_root / "data.yaml").open(encoding="utf-8") as f:
        data = yaml.safe_load(f)

    names = data.get("names", [])
    if isinstance(names, dict):
        return tuple(names[k] for k in sorted(names, key=int))
    return tuple(names)


def _parse_yolo_detection_label(
    label_path: Path,
    width: int,
    height: int,
) -> tuple[np.ndarray | None, np.ndarray | None, np.ndarray | None, np.ndarray | None]:
    """Parse a standard YOLO detection label file into per-instance annotation arrays.

    Each line is ``class_id cx cy w h`` with coordinates normalized to
    ``[0, 1]``; converts to absolute-pixel top-left ``xywh`` bboxes, plus
    bbox-area and an all-``False`` ``iscrowd`` array.

    Returns ``(bboxes, labels, areas, iscrowd)``, all ``None`` when
    *label_path* doesn't exist or has no valid annotation lines.
    """
    if not label_path.exists():
        return None, None, None, None

    bboxes: list[list[float]] = []
    labels: list[int] = []
    areas: list[float] = []

    for raw_line in label_path.read_text(encoding="utf-8").splitlines():
        parts = raw_line.split()
        if len(parts) != 5:
            continue

        class_id, cx, cy, w, h = (float(p) for p in parts)
        abs_w = w * width
        abs_h = h * height
        x_min = (cx * width) - abs_w / 2
        y_min = (cy * height) - abs_h / 2

        labels.append(int(class_id))
        bboxes.append([x_min, y_min, abs_w, abs_h])
        areas.append(abs_w * abs_h)

    if not labels:
        return None, None, None, None

    return (
        np.asarray(bboxes, dtype=np.float32),
        np.asarray(labels, dtype=np.int64),
        np.asarray(areas, dtype=np.float32),
        np.zeros(len(labels), dtype=np.bool_),
    )


def _build_dataset(yolo_root: Path) -> Dataset:
    """Parse a Roboflow YOLO-detection export into a Datumaro ``CocoSample`` dataset."""
    dataset: Dataset = Dataset(
        CocoSample,
        categories={"labels": CocoCategories(labels=_load_label_names(yolo_root))},
    )

    image_id = 0
    for subset_dir_name, subset_enum in _SUBSET_DIR_TO_SUBSET.items():
        images_dir = yolo_root / subset_dir_name / "images"
        labels_dir = yolo_root / subset_dir_name / "labels"
        if not images_dir.is_dir():
            continue

        for image_path in sorted(p for p in images_dir.iterdir() if p.is_file()):
            with Image.open(image_path) as im:
                width, height = im.size

            bboxes, labels, areas, iscrowd = _parse_yolo_detection_label(
                labels_dir / f"{image_path.stem}.txt",
                width,
                height,
            )

            dataset.append(
                CocoSample(
                    image=LazyImage(image_path),
                    image_info=ImageInfo(width=width, height=height),
                    image_id=image_id,
                    subset=subset_enum,
                    bboxes=bboxes,
                    labels=labels,
                    polygons=None,
                    areas=areas,
                    iscrowd=iscrowd,
                    caption_group_ids=None,
                    captions=None,
                    keypoints=None,
                ),
            )
            image_id += 1

    if len(dataset) == 0:
        msg = f"No images found under YOLO dataset root {yolo_root}"
        raise RuntimeError(msg)

    return dataset


def main() -> None:
    """Prepare the cardd benchmark dataset (Kaggle download or --raw-dir) and export it."""
    args = parse_args(description="Prepare the cardd benchmark dataset.")

    def _download() -> Path:
        return download_kaggle_dataset(_KAGGLE_DATASET_ID)

    raw_root = resolve_raw_source(args, _download)
    dataset = _build_dataset(_find_yolo_root(raw_root))

    if args.dest.exists():
        shutil.rmtree(args.dest)
    args.dest.parent.mkdir(parents=True, exist_ok=True)
    export_dataset(dataset, args.dest)

    print(f"Dataset '{args.name}' ready at {args.dest}")


if __name__ == "__main__":
    main()
