# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from io import BytesIO
from pathlib import Path
from uuid import uuid4
from zipfile import ZipFile

from datumaro.experimental.categories import LabelCategories
from datumaro.experimental.export_import import import_dataset
from datumaro.experimental.fields import Subset
from PIL import Image

from app.execution import PrepareDataset
from app.models.jobs import PrepareDatasetForImportJobParams


def test_prepare_roboflow_yolo_archive(tmp_path: Path) -> None:
    dataset_id = uuid4()
    staged_dir = tmp_path / str(dataset_id)
    staged_dir.mkdir()
    archive_path = staged_dir / "roboflow.zip"
    image = BytesIO()
    Image.new("RGB", (100, 100)).save(image, format="JPEG")

    with ZipFile(archive_path, "w") as archive:
        archive.writestr(
            "data.yaml",
            "train: ../train/images\nval: ../valid/images\ntest: ../test/images\nnc: 1\nnames: ['License_Plate']\n",
        )
        for split in ("train", "valid", "test"):
            archive.writestr(f"{split}/images/{split}.jpg", image.getvalue())
            archive.writestr(f"{split}/labels/{split}.txt", "0 0.5 0.5 0.4 0.2\n")

    PrepareDataset(staged_datasets_dir=tmp_path).execute(PrepareDatasetForImportJobParams(staged_dataset_id=dataset_id))

    dataset = import_dataset(staged_dir / "dataset")
    assert isinstance(dataset.label_categories, LabelCategories)
    assert list(dataset.label_categories.labels) == ["License_Plate"]
    assert len(dataset) == 3
    assert {sample.subset for sample in dataset} == {Subset.TRAINING, Subset.VALIDATION, Subset.TESTING}
    for sample in dataset:
        assert sample.labels.tolist() == [0]
        assert sample.bboxes.tolist() == [[50, 50, 40, 20]]
