# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Regression tests: standalone validator DataLoaders must follow device, not hardcode pin_memory=True."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
import torch

from getitune.backend.ultralytics.validators.classification import (
    ClassificationValidator,
    MultiLabelClassificationValidator,
)
from getitune.backend.ultralytics.validators.detection import DetectionValidator
from getitune.backend.ultralytics.validators.instance_segmentation import SegmentationValidator
from getitune.backend.ultralytics.validators.semantic_segmentation import SemanticSegmentationValidator
from getitune.backend.ultralytics.validators.yolo_detr import YoloDetrValidator

# Validators that fall through to GetiTuneValidatorMixin._build_adapter_dataloader
# share one DataLoader import; ClassificationValidator/MultiLabelClassificationValidator
# and SemanticSegmentationValidator override it with their own import.
_VALIDATOR_CASES = [
    pytest.param(DetectionValidator, "getitune.backend.ultralytics.validators.base.DataLoader", id="detection"),
    pytest.param(
        SegmentationValidator,
        "getitune.backend.ultralytics.validators.base.DataLoader",
        id="instance_segmentation",
    ),
    pytest.param(YoloDetrValidator, "getitune.backend.ultralytics.validators.base.DataLoader", id="yolo_detr"),
    pytest.param(
        ClassificationValidator,
        "getitune.backend.ultralytics.validators.classification.DataLoader",
        id="classification",
    ),
    pytest.param(
        MultiLabelClassificationValidator,
        "getitune.backend.ultralytics.validators.classification.DataLoader",
        id="multilabel_classification",
    ),
    pytest.param(
        SemanticSegmentationValidator,
        "getitune.backend.ultralytics.validators.semantic_segmentation.DataLoader",
        id="semantic_segmentation",
    ),
]


def _make_datamodule() -> SimpleNamespace:
    subset = MagicMock()
    return SimpleNamespace(
        test_subset=SimpleNamespace(subset_name="test"),
        val_subset=SimpleNamespace(subset_name="val"),
        subsets={"test": subset, "val": subset},
    )


class TestValidatorPinMemoryPolicy:
    """Standalone validator DataLoader pin_memory must follow device, across every validator."""

    @pytest.mark.parametrize(("validator_cls", "loader_patch_target"), _VALIDATOR_CASES)
    @pytest.mark.parametrize(
        ("device_type", "expected_pin_memory"),
        [
            ("cpu", False),
            ("cuda:0", True),
            ("xpu:0", True),
        ],
    )
    def test_build_adapter_dataloader_respects_device(
        self,
        device_type: str,
        expected_pin_memory: bool,
        validator_cls: type,
        loader_patch_target: str,
    ) -> None:
        validator = object.__new__(validator_cls)
        validator._datamodule = _make_datamodule()
        validator.device = torch.device(device_type)
        validator.args = SimpleNamespace(batch=4)

        with patch(loader_patch_target) as mock_dataloader_cls:
            validator._build_adapter_dataloader()

        _, kwargs = mock_dataloader_cls.call_args
        assert kwargs["pin_memory"] is expected_pin_memory
