# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

import pytest
from getidata import Sample, import_dataset

from app.datumaro_converter import (
    DetectionImportExportSample,
    InstanceSegmentationImportExportSample,
    MulticlassClassificationImportExportSample,
    MultilabelClassificationImportExportSample,
)

ANNOTATION_TYPE_TO_SAMPLE: dict[str, type[Sample]] = {
    "bounding_box": DetectionImportExportSample,
    "multilabel": MultilabelClassificationImportExportSample,
    "single_label": MulticlassClassificationImportExportSample,
    "polygon": InstanceSegmentationImportExportSample,
}


def test_import_dataset(archive: Path) -> None:
    """Import supported regression archives and reject the removed legacy format."""
    annotation_type, dataset_format = archive.stem.split("-", 1)
    if dataset_format == "datumaro":
        with pytest.raises(ValueError, match="Could not detect dataset format"):
            import_dataset(archive)
        return
    dataset = import_dataset(archive)
    sample_type = ANNOTATION_TYPE_TO_SAMPLE[annotation_type]
    dataset = dataset.convert_to_schema(sample_type)
    assert len(dataset) > 0
