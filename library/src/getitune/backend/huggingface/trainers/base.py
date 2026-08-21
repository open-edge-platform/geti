# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""The ``transformers.Trainer`` bridge for the Hugging Face backend."""

from __future__ import annotations

import multiprocessing
from typing import TYPE_CHECKING, Any

import torch.utils.data
from torchvision import tv_tensors
from transformers import Trainer

from getitune.backend.huggingface.data.adapter import HFDatasetAdapter
from getitune.data.augmentation import GPUAugmentationPipeline
from getitune.data.augmentation.task_keys import DATA_KEYS_BY_TASK

if TYPE_CHECKING:
    from collections.abc import Sequence

    from torch.utils.data import DataLoader
    from torchmetrics import Metric, MetricCollection

    from getitune.backend.huggingface.models.base import HFModel
    from getitune.config.data import SubsetConfig
    from getitune.data.dataset.base import VisionDataset
    from getitune.data.entity.sample import PredictionBatch, SampleBatch
    from getitune.data.module import DataModule

__all__ = ["GetiTuneHFTrainer"]

# Workers must use spawn, not the platform default (fork on Linux). By the
# time training starts, the process has usually already loaded XPU driver
# threads, and forking a multi-threaded process is unsafe — it can corrupt
# state in ways that only surface later, in unrelated code. Every other
# dataloader in getitune already does this (``DataModule``, Ultralytics'
# ``InfiniteDataLoader``); this one needs to as well.
_MP_CONTEXT = multiprocessing.get_context("spawn")


class GetiTuneHFTrainer(Trainer):
    """Binds ``transformers.Trainer`` to a Geti ``DataModule`` and ``HFModel``.

    One trainer class for every task. Ultralytics needs a per-task trainer
    subclass because it binds to upstream task trainers through MRO; here
    the only thing that differs per task is what
    ``model_wrapper.build_targets`` does, and that's already handled one
    level down, in the model wrapper.

    Args:
        model_wrapper: The ``HFModel`` being trained. Supplies
            ``build_targets`` and the task used to pick the GPU augmentation
            pipeline's ``data_keys``.
        datamodule: The Geti ``DataModule`` supplying the train/eval splits.
        *args: Forwarded to ``transformers.Trainer`` (typically ``model`` and
            ``args``).
        **kwargs: Forwarded to ``transformers.Trainer``.
    """

    def __init__(
        self,
        model_wrapper: HFModel,
        datamodule: DataModule,
        *args: Any,  # noqa: ANN401
        **kwargs: Any,  # noqa: ANN401
    ) -> None:
        self.model_wrapper = model_wrapper
        self.datamodule = datamodule
        self._train_gpu_pipeline = self._build_gpu_pipeline(datamodule.train_subset, sanitize=True)
        self._eval_gpu_pipeline = self._build_gpu_pipeline(datamodule.val_subset, sanitize=False)
        self._test_gpu_pipeline = self._build_gpu_pipeline(datamodule.test_subset, sanitize=False)
        super().__init__(*args, **kwargs)

    def _build_gpu_pipeline(
        self, subset_config: SubsetConfig | None, *, sanitize: bool
    ) -> GPUAugmentationPipeline | None:
        """Build the GPU augmentation pipeline for one subset, or ``None`` if unconfigured.

        Skipped entirely when the subset has no ``augmentations_gpu`` — most
        commonly meaning normalization happens on the CPU stage instead, in
        which case there is nothing for this pipeline to do.
        """
        if subset_config is None or not subset_config.augmentations_gpu:
            return None
        data_keys = ["input", *DATA_KEYS_BY_TASK.get(self.model_wrapper.task, ())]
        return GPUAugmentationPipeline.from_config(subset_config, data_keys=data_keys, sanitize_annotations=sanitize)

    def get_train_dataloader(self) -> DataLoader:
        """Return a DataLoader over the training split, via ``HFDatasetAdapter``."""
        return self._build_dataloader(self.datamodule.subsets["train"], self.datamodule.train_subset, shuffle=True)

    def get_eval_dataloader(self, eval_dataset: Any = None) -> DataLoader:  # noqa: ANN401
        """Return a DataLoader over the validation split, via ``HFDatasetAdapter``."""
        return self._build_dataloader(self.datamodule.subsets["val"], self.datamodule.val_subset, shuffle=False)

    def get_test_dataloader(self) -> DataLoader:
        """Return a DataLoader over the test split, via ``HFDatasetAdapter``."""
        return self._build_dataloader(self.datamodule.subsets["test"], self.datamodule.test_subset, shuffle=False)

    def _build_dataloader(
        self, vision_dataset: VisionDataset, subset_config: SubsetConfig, *, shuffle: bool
    ) -> DataLoader:
        adapter = HFDatasetAdapter(vision_dataset, task_kind=self.model_wrapper.task.value.lower())
        batch_size = self.args.per_device_train_batch_size if shuffle else self.args.per_device_eval_batch_size
        num_workers = subset_config.num_workers
        return torch.utils.data.DataLoader(
            adapter,
            batch_size=batch_size,
            shuffle=shuffle,
            num_workers=num_workers,
            collate_fn=adapter.collate_fn,
            multiprocessing_context=_MP_CONTEXT if num_workers > 0 else None,
        )

    def _get_num_items_in_batch(self, batch_samples: list[Any], device: torch.device) -> int | None:
        """Skip HF's per-batch item counting for gradient-accumulation loss scaling.

        ``Trainer`` peeks at ``"labels" in batch_samples[0]`` to rescale the
        loss under gradient accumulation, assuming a dict-like batch —
        ``SampleBatch`` isn't one. It's also unnecessary here: our vision
        models each return a batch-mean loss already, not a per-token loss
        that needs rescaling by item count the way causal LM losses do.
        """
        return None

    def _prepare_inputs(self, inputs: SampleBatch) -> SampleBatch:  # pyrefly: ignore[bad-override]
        """Bypass the base implementation's dict/``Mapping`` assumptions.

        The base ``_prepare_inputs`` checks things like ``len(inputs)`` and
        recurses through ``Mapping``/``list``/``tuple`` to move tensors to
        device — none of which applies to a ``SampleBatch`` dataclass. The
        device move (and any GPU augmentation) happens explicitly in
        ``compute_loss`` instead, so this is a no-op.
        """
        return inputs

    def floating_point_ops(self, inputs: SampleBatch) -> int:  # pyrefly: ignore[bad-override]
        """Skip FLOPs accounting.

        The base implementation inspects ``inputs`` like a dict to estimate
        FLOPs for the ``total_flos`` logging field. Not worth reimplementing
        for ``SampleBatch`` just to populate an informational metric no Geti
        consumer reads.
        """
        return 0

    def prediction_step(  # pyrefly: ignore[bad-override]
        self,
        model: torch.nn.Module,
        inputs: SampleBatch,
        prediction_loss_only: bool,
        ignore_keys: list[str] | None = None,
    ) -> tuple[torch.Tensor | None, None, None]:
        """Compute only the evaluation loss.

        The base implementation inspects ``inputs`` like a dict (``inputs.get(k)``)
        to decide whether labels are present, and otherwise builds
        ``(loss, logits, labels)`` for ``compute_metrics``. Geti's own metric
        callables are wired in through ``HFEngine.test()``, not through
        ``Trainer``'s ``compute_metrics``, so eval here only needs the
        loss — for the training-time metrics CSV and early stopping.
        """
        with torch.no_grad():
            loss = self.compute_loss(model, inputs)
        if prediction_loss_only:
            return loss, None, None
        return loss, None, None

    def compute_loss(  # pyrefly: ignore[bad-override]
        self,
        model: torch.nn.Module,
        inputs: SampleBatch,
        return_outputs: bool = False,
        **kwargs: Any,  # noqa: ANN401
    ) -> Any:  # noqa: ANN401
        """Move the batch to the model's device, augment, convert, and forward.

        *inputs* is the raw ``SampleBatch`` our own collate function
        returns — ``Trainer._prepare_inputs`` only recurses into
        ``Mapping``/``list``/``tuple``/``Tensor``, so it leaves a dataclass
        like ``SampleBatch`` untouched. The device move that would normally
        happen there happens explicitly here instead.
        """
        pipeline = self._train_gpu_pipeline if model.training else self._eval_gpu_pipeline
        batch = self._prepare_batch(inputs, pipeline)
        targets = self.model_wrapper.build_targets(batch)
        outputs = model(**targets)
        return (outputs.loss, outputs) if return_outputs else outputs.loss

    def evaluate_with_metric(self, metric: Metric | MetricCollection) -> dict[str, Any]:
        """Run the test split through the model and accumulate *metric*.

        Bypasses ``transformers.Trainer``'s own evaluation loop on purpose:
        that loop is built around a fixed-shape ``EvalPrediction`` /
        ``compute_metrics`` contract, which does not fit detection's or
        instance segmentation's variable number of predictions per image.
        Iterating the test dataloader directly and calling
        ``HFModel.to_metric_inputs`` per batch sidesteps that mismatch
        entirely, at the cost of not being able to reuse ``Trainer.evaluate()``.

        Args:
            metric: A metric or metric collection, already constructed for
                this model's ``label_info`` (e.g. via
                ``HFModel.build_default_metric()``).

        Returns:
            The result of ``metric.compute()`` after seeing every batch in
            the test split.
        """
        model = self.model_wrapper.hf_model
        self.model_wrapper.ensure_predict_ready()
        with torch.no_grad():
            for inputs in self.get_test_dataloader():
                batch = self._prepare_batch(inputs, self._test_gpu_pipeline)
                targets = self.model_wrapper.build_targets(batch)
                outputs = model(**targets)
                metric.update(**self.model_wrapper.to_metric_inputs(outputs, batch))
        return metric.compute()

    def _prepare_batch(self, batch: SampleBatch, pipeline: GPUAugmentationPipeline | None) -> SampleBatch:
        """Move a batch to the model's device and apply GPU augmentation, if configured.

        Shared by ``compute_loss`` and ``evaluate_with_metric`` so the two
        don't drift into subtly different device-handling paths.
        """
        batch = self._move_batch_to_device(batch, self.args.device)
        if pipeline is not None:
            batch = self._apply_gpu_augmentation(pipeline, batch)
        return batch

    def predict_batches(self) -> list[PredictionBatch]:
        """Run the test split through the model and postprocess every batch.

        Like ``evaluate_with_metric``, this iterates the test dataloader
        directly instead of going through ``Trainer.predict()``, whose
        ``EvalLoopOutput``/``compute_metrics`` contract assumes fixed-shape
        per-sample outputs. Confidence thresholding is deliberately not
        applied here — it belongs to whichever caller decides what to do
        with these predictions (``HFEngine.predict()``).

        Returns:
            One :class:`~getitune.data.entity.sample.PredictionBatch` per
            batch in the test split, in dataloader order.
        """
        model = self.model_wrapper.hf_model
        self.model_wrapper.ensure_predict_ready()
        batches: list[PredictionBatch] = []
        with torch.no_grad():
            for inputs in self.get_test_dataloader():
                batch = self._prepare_batch(inputs, self._test_gpu_pipeline)
                targets = self.model_wrapper.build_targets(batch)
                outputs = model(**targets)
                batches.append(self.model_wrapper.postprocess(outputs, batch))
        return batches

    @staticmethod
    def _move_batch_to_device(batch: SampleBatch, device: torch.device) -> SampleBatch:
        if not isinstance(batch.images, torch.Tensor):
            msg = f"Expected a stacked image tensor, got {type(batch.images)}"
            raise TypeError(msg)

        def move(items: Sequence[torch.Tensor] | None) -> list[torch.Tensor] | None:
            return None if items is None else [item.to(device) for item in items]

        return batch.wrap(
            images=batch.images.to(device),
            labels=move(batch.labels),
            bboxes=move(batch.bboxes),
            masks=move(batch.masks),
            keypoints=move(batch.keypoints),
        )

    def _apply_gpu_augmentation(self, pipeline: GPUAugmentationPipeline, batch: SampleBatch) -> SampleBatch:
        """Run the Kornia pipeline and re-wrap its output as Geti tv_tensors.

        A trimmed version of ``GPUAugmentationCallback._apply_pipeline``: the
        same re-wrapping logic, minus tiling and keypoints, since neither
        applies to the five tasks this backend supports.
        """
        result = pipeline(batch.images, labels=batch.labels, bboxes=batch.bboxes, masks=batch.masks)

        bboxes = batch.bboxes
        if result.get("bboxes") is not None and batch.bboxes is not None:
            bboxes = [
                box
                if isinstance(box, tv_tensors.BoundingBoxes)
                else tv_tensors.BoundingBoxes(  # pyrefly: ignore[no-matching-overload]
                    box, format=tv_tensors.BoundingBoxFormat.XYXY, canvas_size=batch.bboxes[i].canvas_size
                )
                for i, box in enumerate(result["bboxes"])
            ]

        masks = batch.masks
        if result.get("masks") is not None:
            masks = [mask if isinstance(mask, tv_tensors.Mask) else tv_tensors.Mask(mask) for mask in result["masks"]]

        return batch.wrap(
            images=result["images"],
            labels=result["labels"] if result.get("labels") is not None else batch.labels,
            bboxes=bboxes,
            masks=masks,
        )
