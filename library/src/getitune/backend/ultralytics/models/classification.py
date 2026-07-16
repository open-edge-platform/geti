# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Ultralytics classification models (multi-class and multi-label)."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from getitune.backend.lightning.models.base import DataInputParams
from getitune.backend.ultralytics.models.utils import ensure_classify_transforms, patch_multilabel_classify_head
from getitune.backend.ultralytics.trainers.classification import (
    ClassificationTrainer,
    MultiLabelClassificationTrainer,
)
from getitune.backend.ultralytics.validators.classification import (
    ClassificationValidator,
    MultiLabelClassificationValidator,
)
from getitune.config.data import IntensityConfig
from getitune.types.export import TaskLevelExportParameters

from .base import UltralyticsModel

if TYPE_CHECKING:
    from ultralytics import YOLO

    from getitune.backend.ultralytics.exporter import UltralyticsModelExporter


class UltralyticsMultiClassClsModel(UltralyticsModel):
    """YOLO multi-class classification model.

    Supported variants: ``yolo26n-cls``, ``yolo26s-cls``, ``yolo26m-cls``,
    ``yolo26l-cls``, ``yolo26x-cls``.
    """

    task: ClassVar[str] = "classify"
    trainer_cls: ClassVar[type] = ClassificationTrainer
    validator_cls: ClassVar[type] = ClassificationValidator
    metric_keys: ClassVar[dict[str, str]] = {
        "metrics/accuracy_top1": "val/accuracy_top1",
        "metrics/accuracy_top5": "val/accuracy_top5",
        "train/loss": "train/loss",
        "lr/pg0": "lr",
    }

    _pretrained_weights: ClassVar[dict[str, str]] = {
        "yolo26n-cls": "https://github.com/ultralytics/assets/releases/download/v8.4.0/yolo26n-cls.pt",
        "yolo26s-cls": "https://github.com/ultralytics/assets/releases/download/v8.4.0/yolo26s-cls.pt",
        "yolo26m-cls": "https://github.com/ultralytics/assets/releases/download/v8.4.0/yolo26m-cls.pt",
        "yolo26l-cls": "https://github.com/ultralytics/assets/releases/download/v8.4.0/yolo26l-cls.pt",
        "yolo26x-cls": "https://github.com/ultralytics/assets/releases/download/v8.4.0/yolo26x-cls.pt",
    }
    _DEFAULT_DATA_INPUT_PARAMS: ClassVar[DataInputParams] = DataInputParams(
        input_size=(224, 224),
        mean=(0.0, 0.0, 0.0),
        std=(1.0, 1.0, 1.0),
        intensity_config=IntensityConfig(mode="scale_to_unit", storage_dtype="uint8"),
    )

    @property
    def _default_preprocessing_params(self) -> dict[str, DataInputParams]:
        """Per-variant preprocessing defaults.

        All YOLO26-cls models use 224x224 input with identity mean/std (no
        additional normalization after intensity scaling to [0, 1]).
        """
        return dict.fromkeys(
            ("yolo26n-cls", "yolo26s-cls", "yolo26m-cls", "yolo26l-cls", "yolo26x-cls"),
            self._DEFAULT_DATA_INPUT_PARAMS,
        )

    @property
    def _export_parameters(self) -> TaskLevelExportParameters:
        """Multi-class classification export parameters."""
        return TaskLevelExportParameters(
            model_type="Classification",
            model_name=self.model_name,
            task_type="classification",
            label_info=self.label_info,
            optimization_config={},
            confidence_threshold=None,
            multilabel=False,
            hierarchical=False,
            iou_threshold=None,
            nms_execute=False,
        )

    @property
    def _exporter(self) -> UltralyticsModelExporter:
        """Build and return the model exporter with standard (non-letterbox) resize."""
        from getitune.backend.ultralytics.exporter import UltralyticsModelExporter

        return UltralyticsModelExporter(
            task_level_export_parameters=self._export_parameters,
            data_input_params=self.data_input_params,
            resize_mode="standard",
            pad_value=0,
            swap_rgb=False,
        )

    def ensure_predict_ready(self) -> None:
        """Backfill ``model.transforms`` required by Ultralytics' classification predictor."""
        ensure_classify_transforms(self)


class UltralyticsMultiLabelClsModel(UltralyticsModel):
    """YOLO multi-label classification model.

    Reuses the upstream ``classify`` backbone and pretrained weights, but
    replaces the softmax inference activation with sigmoid and the CE loss
    with binary cross-entropy.

    Supported variants: ``yolo26n-cls``, ``yolo26s-cls``, ``yolo26m-cls``,
    ``yolo26l-cls``, ``yolo26x-cls``.
    """

    task: ClassVar[str] = "classify"
    trainer_cls: ClassVar[type] = MultiLabelClassificationTrainer
    validator_cls: ClassVar[type] = MultiLabelClassificationValidator
    is_multilabel: ClassVar[bool] = True
    metric_keys: ClassVar[dict[str, str]] = {
        "metrics/accuracy": "val/accuracy",
        "metrics/mAP": "val/mAP",
        "train/loss": "train/loss",
        "lr/pg0": "lr",
    }

    _pretrained_weights: ClassVar[dict[str, str]] = {
        "yolo26n-cls": "https://github.com/ultralytics/assets/releases/download/v8.4.0/yolo26n-cls.pt",
        "yolo26s-cls": "https://github.com/ultralytics/assets/releases/download/v8.4.0/yolo26s-cls.pt",
        "yolo26m-cls": "https://github.com/ultralytics/assets/releases/download/v8.4.0/yolo26m-cls.pt",
        "yolo26l-cls": "https://github.com/ultralytics/assets/releases/download/v8.4.0/yolo26l-cls.pt",
        "yolo26x-cls": "https://github.com/ultralytics/assets/releases/download/v8.4.0/yolo26x-cls.pt",
    }
    _DEFAULT_DATA_INPUT_PARAMS: ClassVar[DataInputParams] = DataInputParams(
        input_size=(224, 224),
        mean=(0.0, 0.0, 0.0),
        std=(1.0, 1.0, 1.0),
        intensity_config=IntensityConfig(mode="scale_to_unit", storage_dtype="uint8"),
    )

    @property
    def _default_preprocessing_params(self) -> dict[str, DataInputParams]:
        """Per-variant preprocessing defaults.

        All YOLO26-cls models use 224x224 input with identity mean/std.
        """
        return dict.fromkeys(
            ("yolo26n-cls", "yolo26s-cls", "yolo26m-cls", "yolo26l-cls", "yolo26x-cls"),
            self._DEFAULT_DATA_INPUT_PARAMS,
        )

    @property
    def _export_parameters(self) -> TaskLevelExportParameters:
        """Multi-label classification export parameters."""
        return TaskLevelExportParameters(
            model_type="Classification",
            model_name=self.model_name,
            task_type="classification",
            label_info=self.label_info,
            optimization_config={},
            confidence_threshold=0.5,
            multilabel=True,
            hierarchical=False,
            output_raw_scores=True,
            nms_execute=False,
        )

    @property
    def _exporter(self) -> UltralyticsModelExporter:
        """Build and return the model exporter with standard (non-letterbox) resize."""
        from getitune.backend.ultralytics.exporter import UltralyticsModelExporter

        return UltralyticsModelExporter(
            task_level_export_parameters=self._export_parameters,
            data_input_params=self.data_input_params,
            resize_mode="standard",
            pad_value=0,
            swap_rgb=False,
        )

    def _build_yolo(self) -> YOLO:
        """Build the YOLO model and rewire the Classify head for multi-label."""
        yolo = super()._build_yolo()
        model = yolo.model
        if model is None:
            msg = "YOLO model was not built"
            raise RuntimeError(msg)
        patch_multilabel_classify_head(model)
        return yolo

    def ensure_predict_ready(self) -> None:
        """Backfill ``model.transforms`` required by Ultralytics' classification predictor."""
        ensure_classify_transforms(self)
