# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import sys
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.execution.pretrained_auto_label import PretrainedAutoLabel, PretrainedAutoLabelDependencies
from app.models import DatasetItemAnnotationStatus, TaskType
from app.models.jobs import PretrainedAutoLabelJobParams


def test_pretrained_auto_label_only_queries_items_without_annotations(monkeypatch, fxt_db_session_factory):
    """Auto-label must never replace reviewed annotations or existing predictions."""
    monkeypatch.setitem(sys.modules, "ultralytics", SimpleNamespace(YOLO=MagicMock()))
    project_id = uuid4()
    project = MagicMock(id=project_id)
    project.task.task_type = TaskType.DETECTION
    dataset_service = MagicMock()
    dataset_service.list_dataset_items_with_media.return_value = []
    project_service = MagicMock()
    project_service.get_project_by_id.return_value = project
    execution = PretrainedAutoLabel(
        PretrainedAutoLabelDependencies(
            base_weights_service=MagicMock(),
            dataset_service=dataset_service,
            label_service=MagicMock(),
            media_service=MagicMock(),
            project_service=project_service,
            db_session_factory=fxt_db_session_factory,
        )
    )

    with pytest.raises(ValueError, match="no unannotated images"):
        execution.auto_label(
            PretrainedAutoLabelJobParams(
                project_id=project_id,
                model_architecture_id="object-detection-yolo11-n",
            )
        )

    filters = dataset_service.list_dataset_items_with_media.call_args.kwargs["filters"]
    assert filters.annotation_status is DatasetItemAnnotationStatus.MISSING_ANNOTATIONS
    dataset_service.set_dataset_item_annotations.assert_not_called()
