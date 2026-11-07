# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.models import DatasetFormat, ExportDatasetJobParams, Task, TaskType


class TestExportDatasetJobParams:
    @pytest.mark.parametrize(
        ("task_type", "export_format"),
        [
            (TaskType.CLASSIFICATION, DatasetFormat.GETI),
            (TaskType.CLASSIFICATION, DatasetFormat.VOC),
            (TaskType.DETECTION, DatasetFormat.GETI),
            (TaskType.DETECTION, DatasetFormat.COCO),
            (TaskType.DETECTION, DatasetFormat.YOLO),
            (TaskType.INSTANCE_SEGMENTATION, DatasetFormat.GETI),
            (TaskType.INSTANCE_SEGMENTATION, DatasetFormat.COCO),
            (TaskType.INSTANCE_SEGMENTATION, DatasetFormat.YOLO_SEG),
        ],
    )
    def test_validate_format_valid(self, task_type: TaskType, export_format: DatasetFormat):
        """Test that valid combinations of task and export format are accepted."""
        try:
            ExportDatasetJobParams(
                project_id=uuid4(),
                task=Task(task_type=task_type),
                export_format=export_format,
            )
        except ValidationError:
            pytest.fail("Validation failed for a valid combination.")

    def test_validate_format_yolo_cls_valid_for_multiclass(self):
        """Test that the YOLO classification format is accepted for single-label classification."""
        params = ExportDatasetJobParams(
            project_id=uuid4(),
            task=Task(task_type=TaskType.CLASSIFICATION, exclusive_labels=True),
            export_format=DatasetFormat.YOLO_CLS,
        )
        assert params.export_format is DatasetFormat.YOLO_CLS

    def test_validate_format_yolo_cls_invalid_for_multilabel(self):
        """Test that the YOLO classification format is rejected for multi-label classification."""
        with pytest.raises(
            ValidationError, match="Export format 'yolo_cls' is only supported for single-label"
        ):
            ExportDatasetJobParams(
                project_id=uuid4(),
                task=Task(task_type=TaskType.CLASSIFICATION, exclusive_labels=False),
                export_format=DatasetFormat.YOLO_CLS,
            )

    def test_validate_format_yolo_seg_valid_for_instance_segmentation(self):
        """Test that the YOLO segmentation format is accepted for instance segmentation projects."""
        params = ExportDatasetJobParams(
            project_id=uuid4(),
            task=Task(task_type=TaskType.INSTANCE_SEGMENTATION),
            export_format=DatasetFormat.YOLO_SEG,
        )
        assert params.export_format is DatasetFormat.YOLO_SEG

    @pytest.mark.parametrize(
        ("task_type", "export_format"),
        [
            (TaskType.CLASSIFICATION, DatasetFormat.COCO),
            (TaskType.CLASSIFICATION, DatasetFormat.YOLO),
            (TaskType.DETECTION, DatasetFormat.VOC),
            (TaskType.DETECTION, DatasetFormat.YOLO_CLS),
            (TaskType.DETECTION, DatasetFormat.YOLO_SEG),
            (TaskType.INSTANCE_SEGMENTATION, DatasetFormat.YOLO),
            (TaskType.INSTANCE_SEGMENTATION, DatasetFormat.VOC),
            (TaskType.INSTANCE_SEGMENTATION, DatasetFormat.YOLO_CLS),
        ],
    )
    def test_validate_format_invalid(self, task_type: TaskType, export_format: DatasetFormat):
        """Test that invalid combinations of task and export format raise a ValueError."""
        with pytest.raises(
            ValidationError, match=f"Export format '{export_format}' is not supported for {task_type} task."
        ):
            ExportDatasetJobParams(
                project_id=uuid4(),
                task=Task(task_type=task_type),
                export_format=export_format,
            )

    def test_dataset_id_and_dataset_view_id_mutually_exclusive(self):
        """Test that setting both dataset_id and dataset_view_id raises a ValueError."""
        with pytest.raises(ValidationError, match="dataset_id and dataset_view_id are mutually exclusive"):
            ExportDatasetJobParams(
                project_id=uuid4(),
                task=Task(task_type=TaskType.DETECTION),
                export_format=DatasetFormat.COCO,
                dataset_id=uuid4(),
                dataset_view_id=uuid4(),
            )

    def test_dataset_view_id_alone_is_valid(self):
        """Test that dataset_view_id can be set without dataset_id."""
        params = ExportDatasetJobParams(
            project_id=uuid4(),
            task=Task(task_type=TaskType.DETECTION),
            export_format=DatasetFormat.COCO,
            dataset_view_id=uuid4(),
        )
        assert params.dataset_id is None
        assert params.dataset_view_id is not None
