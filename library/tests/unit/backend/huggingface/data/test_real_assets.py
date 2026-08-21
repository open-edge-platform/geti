# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Real Datumaro assets, all five tasks, finite loss.

Every other test in this backend uses synthetic batches so it stays fast and
isolated. This file is the one place that exercises the full path against
real parquet-backed Geti datasets under ``tests/assets/``:

    DataModule -> HFDatasetAdapter -> collate_fn -> model.build_targets -> hf_model

Models are still built from bare ``transformers`` configs (no Hub access),
so this stays offline; only the *data* side is real.
"""

from __future__ import annotations

import math
from pathlib import Path

import pytest
import transformers as tf

from getitune.backend.huggingface.data import HFDatasetAdapter
from getitune.backend.huggingface.models import (
    HFDetectionModel,
    HFInstSegModel,
    HFMulticlassClsModel,
    HFMultilabelClsModel,
    HFSemanticSegModel,
)
from getitune.data.module import DataModule
from getitune.types.task import TaskType

ASSETS_ROOT = Path(__file__).resolve().parents[4] / "assets"


def _detection_model(num_labels: int) -> HFDetectionModel:
    return HFDetectionModel(tf.RTDetrV2Config(num_queries=30, decoder_layers=2), num_labels)


def _instseg_model(num_labels: int) -> HFInstSegModel:
    return HFInstSegModel(tf.Mask2FormerConfig(num_queries=20), num_labels)


def _multiclass_model(num_labels: int) -> HFMulticlassClsModel:
    config = tf.ViTConfig(hidden_size=32, num_hidden_layers=1, num_attention_heads=2, intermediate_size=64)
    return HFMulticlassClsModel(config, num_labels)


def _multilabel_model(num_labels: int) -> HFMultilabelClsModel:
    config = tf.ViTConfig(hidden_size=32, num_hidden_layers=1, num_attention_heads=2, intermediate_size=64)
    return HFMultilabelClsModel(config, num_labels)


def _semantic_seg_model(num_labels: int) -> HFSemanticSegModel:
    return HFSemanticSegModel(tf.SegformerConfig(), num_labels)


@pytest.mark.parametrize(
    ("task", "dataset_dir", "make_model"),
    [
        (TaskType.DETECTION, "detection_coco", _detection_model),
        (TaskType.INSTANCE_SEGMENTATION, "instance_segmentation_coco", _instseg_model),
        (TaskType.MULTI_CLASS_CLS, "classification_cifar10", _multiclass_model),
        (TaskType.MULTI_LABEL_CLS, "multilabel_classification_coco", _multilabel_model),
        (TaskType.SEMANTIC_SEGMENTATION, "segmentation_pets", _semantic_seg_model),
    ],
)
def test_real_dataset_produces_a_finite_loss(task: TaskType, dataset_dir: str, make_model) -> None:
    datamodule = DataModule(task=task, data_root=str(ASSETS_ROOT / dataset_dir))
    vision_dataset = datamodule.subsets["train"]
    num_labels = vision_dataset.label_info.num_classes

    adapter = HFDatasetAdapter(vision_dataset, task_kind=task.value.lower())
    batch = adapter.collate_fn([adapter[0], adapter[1]])

    model = make_model(num_labels)
    out = model.forward(batch)

    assert math.isfinite(float(out.loss))  # type: ignore[attr-defined]
