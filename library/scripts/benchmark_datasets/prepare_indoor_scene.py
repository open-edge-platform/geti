#!/usr/bin/env python3
# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Download and prepare the indoor scene benchmark dataset.

Uses the official archive and exports it in the experimental Datumaro format
for multi-class classification benchmarks.

Archive: https://groups.csail.mit.edu/vision/LabelMe/NewImages/indoorCVPR_09.tar
"""

from __future__ import annotations

import shutil
import xml.etree.ElementTree as ET
from typing import TYPE_CHECKING
from pathlib import Path

import numpy as np
from datumaro.experimental import Dataset, LazyImage
from datumaro.experimental.data_formats.coco.sample import CocoCategories, CocoSample
from datumaro.experimental.export_import import export_dataset
from datumaro.experimental.fields import ImageInfo, Subset
from PIL import Image

from getitune.benchmark.dataset_helpers import download, extract_archive, parse_args

if TYPE_CHECKING:
    pass

_REPO = "Voxel51/IndoorSceneRecognition"
_REVISION = "main"
_ARCHIVE_URL = "https://groups.csail.mit.edu/vision/LabelMe/NewImages/indoorCVPR_09.tar"
_ANNOTATIONS_URL = "https://groups.csail.mit.edu/vision/LabelMe/NewImages/indoorCVPR_09annotations.tar"


def _build_dataset(snapshot_root: Path) -> Dataset:
    annotation_root = snapshot_root / "Annotations"
    label_names = tuple(sorted(p.name for p in annotation_root.iterdir() if p.is_dir()))
    dataset: Dataset = Dataset(CocoSample, categories={"labels": CocoCategories(labels=label_names)})
    label_to_idx = {label: idx for idx, label in enumerate(label_names)}

    image_root = snapshot_root / "Images"
    image_by_stem = {p.stem: p for p in image_root.rglob("*.jpg")}
    image_id = 0
    for label_dir in sorted(p for p in annotation_root.iterdir() if p.is_dir()):
        label = label_dir.name
        for xml_path in sorted(label_dir.glob("*.xml")):
            tree = ET.parse(xml_path)
            stem = tree.findtext("filename") or xml_path.stem
            src = image_by_stem.get(Path(stem).stem)
            if src is None:
                continue
            with Image.open(src) as im:
                width, height = im.size
            dataset.append(
                CocoSample(
                    image=LazyImage(src),
                    image_info=ImageInfo(width=width, height=height),
                    image_id=image_id,
                    subset=Subset.TRAINING,
                    bboxes=None,
                    labels=np.asarray([label_to_idx[label]], dtype=np.int64),
                    polygons=None,
                    areas=None,
                    iscrowd=None,
                    caption_group_ids=None,
                    captions=None,
                    keypoints=None,
                ),
            )
            image_id += 1
    return dataset


def main() -> None:
    args = parse_args(description="Prepare the indoor_scene benchmark dataset.")
    staging = args.archive_dir / f"{args.name}_raw"
    image_archive = download(_ARCHIVE_URL, dest_dir=args.archive_dir, filename=f"{args.name}.tar")
    ann_archive = download(_ANNOTATIONS_URL, dest_dir=args.archive_dir, filename=f"{args.name}_annotations.tar")
    extract_archive(image_archive, staging)
    extract_archive(ann_archive, staging)
    dataset = _build_dataset(staging)
    if args.dest.exists():
        shutil.rmtree(args.dest)
    args.dest.parent.mkdir(parents=True, exist_ok=True)
    export_dataset(dataset, args.dest)
    image_archive.unlink(missing_ok=True)
    ann_archive.unlink(missing_ok=True)
    shutil.rmtree(args.archive_dir / f"{args.name}_raw", ignore_errors=True)


if __name__ == "__main__":
    main()
