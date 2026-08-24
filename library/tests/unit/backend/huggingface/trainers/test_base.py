# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for ``GetiTuneHFTrainer``."""

from __future__ import annotations

import tempfile
from unittest.mock import MagicMock

import torch
import transformers as tf
from torchvision import tv_tensors
from transformers import TrainingArguments

from getitune.backend.huggingface.models import HFDetectionModel, HFMulticlassClsModel
from getitune.backend.huggingface.trainers.base import GetiTuneHFTrainer
from getitune.config.data import SubsetConfig
from getitune.data.entity.sample import SampleBatch
from getitune.data.module import DataModule
from getitune.types.label import LabelInfo
from getitune.types.task import TaskType


def _label_info() -> LabelInfo:
    return LabelInfo(
        label_names=["cat", "dog", "bird"], label_ids=["0", "1", "2"], label_groups=[["cat", "dog", "bird"]]
    )


def _detection_model() -> HFDetectionModel:
    return HFDetectionModel(tf.RTDetrV2Config(num_queries=10, decoder_layers=2), _label_info())


def _multiclass_model() -> HFMulticlassClsModel:
    config = tf.ViTConfig(hidden_size=32, num_hidden_layers=1, num_attention_heads=2, intermediate_size=64)
    return HFMulticlassClsModel(config, _label_info())


def _mock_datamodule(*, with_gpu_augmentations: bool = False) -> MagicMock:
    datamodule = MagicMock()
    datamodule.train_subset = SubsetConfig(
        batch_size=2,
        num_workers=0,
        augmentations_gpu=(
            [{"class_path": "kornia.augmentation.RandomHorizontalFlip", "init_args": {"p": 1.0}}]
            if with_gpu_augmentations
            else []
        ),
    )
    datamodule.val_subset = SubsetConfig(batch_size=2, num_workers=0, augmentations_gpu=[])
    return datamodule


def _detection_batch(device: torch.device | None = None) -> SampleBatch:
    device = device or torch.device("cpu")
    images = torch.rand(2, 3, 64, 64, dtype=torch.float32, device=device)
    bboxes = [
        tv_tensors.BoundingBoxes(  # pyrefly: ignore[no-matching-overload]
            torch.tensor([[10.0, 10.0, 30.0, 30.0]], device=device),
            format=tv_tensors.BoundingBoxFormat.XYXY,
            canvas_size=(64, 64),
        ),
        tv_tensors.BoundingBoxes(  # pyrefly: ignore[no-matching-overload]
            torch.zeros((0, 4), device=device), format=tv_tensors.BoundingBoxFormat.XYXY, canvas_size=(64, 64)
        ),
    ]
    labels = [torch.tensor([1], device=device), torch.zeros(0, dtype=torch.long, device=device)]
    return SampleBatch(images=images, bboxes=bboxes, labels=labels)


def _build_trainer(model_wrapper, datamodule, **args_kwargs) -> GetiTuneHFTrainer:
    with tempfile.TemporaryDirectory() as tmp_dir:
        args = TrainingArguments(
            output_dir=tmp_dir,
            report_to=[],
            remove_unused_columns=False,
            label_names=list(model_wrapper.label_keys),
            use_cpu=True,
            **args_kwargs,
        )
        return GetiTuneHFTrainer(
            model_wrapper,
            datamodule,
            model=model_wrapper.hf_model,
            args=args,
            train_dataset=[0],
            eval_dataset=[0],
        )


class TestGpuPipelineConstruction:
    def test_no_pipeline_when_subset_has_no_gpu_augmentations(self) -> None:
        model = _multiclass_model()
        trainer = _build_trainer(model, _mock_datamodule(with_gpu_augmentations=False))
        assert trainer._train_gpu_pipeline is None
        assert trainer._eval_gpu_pipeline is None

    def test_pipeline_built_when_subset_has_gpu_augmentations(self) -> None:
        model = _multiclass_model()
        trainer = _build_trainer(model, _mock_datamodule(with_gpu_augmentations=True))
        assert trainer._train_gpu_pipeline is not None
        # val subset in the mock has no augmentations_gpu configured
        assert trainer._eval_gpu_pipeline is None


class TestMoveBatchToDevice:
    def test_moves_images_and_ragged_fields(self) -> None:
        batch = _detection_batch()
        moved = GetiTuneHFTrainer._move_batch_to_device(batch, torch.device("cpu"))
        assert isinstance(moved.images, torch.Tensor)
        assert moved.images.device.type == "cpu"
        assert moved.bboxes is not None
        assert moved.labels is not None
        assert all(b.device.type == "cpu" for b in moved.bboxes)
        assert all(t.device.type == "cpu" for t in moved.labels)

    def test_handles_none_optional_fields(self) -> None:
        batch = SampleBatch(images=torch.rand(1, 3, 8, 8))
        moved = GetiTuneHFTrainer._move_batch_to_device(batch, torch.device("cpu"))
        assert moved.bboxes is None
        assert moved.masks is None
        assert moved.keypoints is None


class TestApplyGpuAugmentation:
    def test_augments_images_and_rewraps_bboxes_as_tv_tensors(self) -> None:
        model = _detection_model()
        trainer = _build_trainer(model, _mock_datamodule(with_gpu_augmentations=True))
        batch = _detection_batch()
        pipeline = trainer._train_gpu_pipeline
        assert pipeline is not None

        augmented = trainer._apply_gpu_augmentation(pipeline, batch)

        assert isinstance(augmented.images, torch.Tensor)
        assert isinstance(batch.images, torch.Tensor)
        assert augmented.images.shape == batch.images.shape
        assert augmented.bboxes is not None
        assert all(isinstance(b, tv_tensors.BoundingBoxes) for b in augmented.bboxes)


class TestDictShapeOverrides:
    """SampleBatch isn't a Mapping; Trainer's base implementations assume one."""

    def test_get_num_items_in_batch_returns_none(self) -> None:
        model = _multiclass_model()
        trainer = _build_trainer(model, _mock_datamodule())
        assert trainer._get_num_items_in_batch([_detection_batch()], torch.device("cpu")) is None

    def test_prepare_inputs_is_a_no_op(self) -> None:
        model = _multiclass_model()
        trainer = _build_trainer(model, _mock_datamodule())
        batch = _detection_batch()
        assert trainer._prepare_inputs(batch) is batch

    def test_floating_point_ops_returns_zero(self) -> None:
        model = _multiclass_model()
        trainer = _build_trainer(model, _mock_datamodule())
        assert trainer.floating_point_ops(_detection_batch()) == 0


class TestComputeLoss:
    def test_computes_a_finite_loss_via_build_targets(self) -> None:
        model = _detection_model()
        trainer = _build_trainer(model, _mock_datamodule())
        batch = _detection_batch()

        loss = trainer.compute_loss(model.hf_model, batch)

        assert torch.isfinite(loss)

    def test_return_outputs_also_returns_the_raw_model_output(self) -> None:
        model = _detection_model()
        trainer = _build_trainer(model, _mock_datamodule())
        batch = _detection_batch()

        loss, outputs = trainer.compute_loss(model.hf_model, batch, return_outputs=True)

        assert torch.isfinite(loss)
        assert outputs.loss is loss

    def test_applies_gpu_augmentation_during_training(self) -> None:
        """model.training selects the train pipeline; augmenting must not break the forward pass."""
        model = _detection_model()
        trainer = _build_trainer(model, _mock_datamodule(with_gpu_augmentations=True))
        model.hf_model.train()

        loss = trainer.compute_loss(model.hf_model, _detection_batch())

        assert torch.isfinite(loss)

    def test_prediction_step_returns_loss_only(self) -> None:
        model = _detection_model()
        trainer = _build_trainer(model, _mock_datamodule())
        model.hf_model.eval()

        loss, logits, labels = trainer.prediction_step(model.hf_model, _detection_batch(), prediction_loss_only=True)

        assert loss is not None
        assert torch.isfinite(loss)
        assert logits is None
        assert labels is None


class TestEvaluateWithMetricAndPredictBatches:
    """Real detection data end to end, mirroring TestTrainEndToEnd in test_engine.py.

    ``evaluate_with_metric``/``predict_batches`` bypass ``Trainer``'s own
    evaluation loop entirely (see their docstrings), so they need to be
    exercised against real dataloaders, not a mocked datamodule.
    """

    def _build_real_trainer(self, model: HFDetectionModel, dm: DataModule) -> GetiTuneHFTrainer:
        dm.test_subset.num_workers = 0
        with tempfile.TemporaryDirectory() as tmp_dir:
            args = TrainingArguments(
                output_dir=tmp_dir,
                report_to=[],
                remove_unused_columns=False,
                label_names=list(model.label_keys),
                use_cpu=True,
                per_device_eval_batch_size=dm.test_subset.batch_size,
            )
            return GetiTuneHFTrainer(model, dm, model=model.hf_model, args=args, eval_dataset=dm.subsets["test"])

    def test_evaluate_with_metric_returns_a_finite_map(self) -> None:
        dm = DataModule(task=TaskType.DETECTION, data_root="tests/assets/detection_coco")
        num_labels = dm.subsets["train"].label_info.num_classes
        model = HFDetectionModel(tf.RTDetrV2Config(num_queries=10, decoder_layers=2), num_labels)
        trainer = self._build_real_trainer(model, dm)

        result = trainer.evaluate_with_metric(model.build_default_metric())

        assert torch.isfinite(result["map"])

    def test_predict_batches_returns_one_prediction_batch_per_dataloader_batch(self) -> None:
        dm = DataModule(task=TaskType.DETECTION, data_root="tests/assets/detection_coco")
        num_labels = dm.subsets["train"].label_info.num_classes
        model = HFDetectionModel(tf.RTDetrV2Config(num_queries=10, decoder_layers=2), num_labels)
        trainer = self._build_real_trainer(model, dm)

        batches = trainer.predict_batches()

        assert len(batches) == len(trainer.get_test_dataloader())
        assert sum(batch.batch_size for batch in batches) == len(dm.subsets["test"])
        for batch in batches:
            assert batch.bboxes is not None
            assert batch.scores is not None
            assert batch.labels is not None


class TestTrainerLoopExercisesOverrides:
    """The real ``Trainer`` loop must not trip the base ``Mapping``-assumption paths.

    ``_prepare_inputs``, ``_get_num_items_in_batch``, ``floating_point_ops`` and
    ``prediction_step`` all exist only because ``transformers.Trainer`` assumes a
    dict-like batch and we feed it ``SampleBatch`` dataclasses instead. This test
    drives the actual training and evaluation loops with a tiny real model so a
    regression that drops an override (or makes ``Trainer`` touch a batch as a
    dict) fails loudly rather than silently.
    """

    def test_train_and_eval_run_without_dict_assumptions(self) -> None:
        import transformers as tf

        from getitune.backend.huggingface.models import HFDetectionModel

        dm = DataModule(task=TaskType.DETECTION, data_root="tests/assets/detection_coco")
        num_labels = dm.subsets["train"].label_info.num_classes
        model = HFDetectionModel(tf.RTDetrV2Config(num_queries=10, decoder_layers=2), num_labels)
        dm.train_subset.num_workers = 0
        dm.val_subset.num_workers = 0

        with tempfile.TemporaryDirectory() as tmp_dir:
            args = TrainingArguments(
                output_dir=tmp_dir,
                report_to=[],
                remove_unused_columns=False,
                label_names=list(model.label_keys),
                use_cpu=True,
                per_device_train_batch_size=dm.train_subset.batch_size,
                per_device_eval_batch_size=dm.val_subset.batch_size,
                max_steps=2,
                eval_strategy="steps",
                eval_steps=1,
                logging_strategy="steps",
                logging_steps=1,
                save_strategy="no",
            )
            trainer = GetiTuneHFTrainer(
                model,
                dm,
                model=model.hf_model,
                args=args,
                train_dataset=dm.subsets["train"],
                eval_dataset=dm.subsets["val"],
            )

            # Exercises _prepare_inputs / _get_num_items_in_batch /
            # floating_point_ops through Trainer.training_step, and
            # prediction_step through the eval loop invoked by eval_strategy.
            trainer.train()

        log_history = trainer.state.log_history
        train_loss_entries = [e for e in log_history if "loss" in e]
        eval_loss_entries = [e for e in log_history if "eval_loss" in e]

        # A training loss entry proves the training-step overrides were hit.
        assert train_loss_entries, "expected training loss entries in the log history"
        # An eval_loss entry proves prediction_step ran through Trainer.evaluate().
        assert eval_loss_entries, "expected eval_loss entries; prediction_step was not exercised"
        for entry in train_loss_entries + eval_loss_entries:
            value = entry.get("loss", entry.get("eval_loss"))
            assert torch.isfinite(torch.tensor(value, dtype=torch.float32))
