# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Hugging Face engine implementation."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar

import torch
from torchvision import tv_tensors
from transformers import EarlyStoppingCallback, TrainerCallback, TrainingArguments

from getitune.data.entity.sample import Prediction
from getitune.data.module import DataModule
from getitune.engine.engine import Engine
from getitune.types.device import DeviceType
from getitune.types.export import ExportFormat
from getitune.types.precision import Precision
from getitune.utils.device import is_xpu_available

from ._deps import ACCELERATE_VERSION, TRANSFORMERS_VERSION
from .callbacks.progress import HFProgressCallback, extract_progress_fn
from .models.base import HFModel
from .plugins.xpu import XPUMemoryCallback
from .tools.configurator import Configurator
from .trainers import GetiTuneHFTrainer, write_metrics_csv
from .trainers.metrics_csv import remap_log_key

if TYPE_CHECKING:
    from lightning_fabric.plugins.precision.precision import _PRECISION_INPUT

    from getitune.data.entity.sample import PredictionBatch
    from getitune.metrics import MetricCallable
    from getitune.types import PathLike
    from getitune.types.types import ANNOTATIONS, DATA, METRICS, MODEL

logger = logging.getLogger(__name__)
logger.debug("Hugging Face backend: transformers=%s accelerate=%s", TRANSFORMERS_VERSION, ACCELERATE_VERSION)


class HFEngine(Engine):
    """Engine backed by ``transformers``.

    Wraps an :class:`HFModel` and a :class:`~getitune.data.module.DataModule`
    (or data-root path). Selected by ``backend: huggingface`` in a recipe.
    """

    _EXPORTED_MODEL_BASE_NAME: ClassVar[str] = "exported_model"
    _CHECKPOINT_DIR_NAME: ClassVar[str] = "best_checkpoint"

    def __init__(
        self,
        model: HFModel,
        data: DataModule | PathLike,
        work_dir: PathLike | None = None,
        device: str | DeviceType = "auto",
        checkpoint: PathLike | None = None,
        training: dict[str, Any] | None = None,
        **kwargs,
    ) -> None:
        """Initialize the engine.

        Args:
            model: Hugging Face model wrapper.
            data: DataModule or filesystem data-root path.
            work_dir: Directory for checkpoints, exports and logs.
                Defaults to ``"./getitune-workspace"``.
            device: Device string or :class:`DeviceType`
                (``"auto"``, ``"xpu"``, ``"cpu"``, ``"gpu"``).
            checkpoint: Optional ``save_pretrained()`` directory to load
                weights from before training.
            training: Default training hyperparameters (``max_epochs``,
                ``batch``, ``learning_rate``, ``patience``, ``precision``),
                normally supplied by :class:`~getitune.backend.huggingface.tools.configurator.Configurator`
                from a recipe's ``training:`` block. Only used to fill in
                whichever of :meth:`train`'s parameters are left as ``None``
                — explicit call-site arguments always win.
            **kwargs: Extra keyword arguments accepted for parity with other
                engines' constructors (e.g. ``task=`` forwarded by
                ``create_engine``); unused by this backend.

        Raises:
            TypeError: If *model* is not an :class:`HFModel`, or *data* is
                neither a :class:`DataModule` nor a path.
        """
        if not isinstance(model, HFModel):
            msg = f"model must be an HFModel instance, got {type(model)}"
            raise TypeError(msg)

        self._model = model
        self._work_dir = Path(work_dir or "./getitune-workspace").resolve()
        self._work_dir.mkdir(parents=True, exist_ok=True)
        self._device = self._resolve_device(device)
        self._training_defaults = dict(training or {})

        if isinstance(data, DataModule):
            self._datamodule: DataModule | None = data
            self._data_root: Path | None = None
        elif isinstance(data, (str, os.PathLike)):
            self._datamodule = None
            self._data_root = Path(data)
        else:
            msg = f"data must be DataModule or PathLike, got {type(data)}"
            raise TypeError(msg)

        if checkpoint is not None:
            self._model.load_checkpoint(checkpoint)

        # The exporter reads preprocessing metadata off the model, so the
        # DataModule's intensity settings have to reach it before export.
        if self._datamodule is not None:
            intensity_cfg = getattr(self._datamodule, "input_intensity_config", None)
            if intensity_cfg is not None:
                self._model.set_intensity_config(intensity_cfg)

    def train(
        self,
        max_epochs: int | None = None,
        batch: int | None = None,
        learning_rate: float | None = None,
        patience: int | None = None,
        precision: _PRECISION_INPUT | None = None,
        callbacks: list | None = None,
        checkpoint: PathLike | None = None,
        **kwargs,
    ) -> METRICS:
        """Train the model.

        The signature intentionally mirrors ``LightningEngine.train()`` (same
        names for ``max_epochs``, ``precision``, ``callbacks``, ``checkpoint``)
        so switching a recipe's ``backend:`` field does not also mean
        relearning the call site. See "Unified engine interface" in
        ``docs/design/huggingface-backend-integration.md`` for the rationale
        and the current gaps between backends.

        Args:
            max_epochs: Maximum number of epochs. Falls back to the recipe's
                ``training.max_epochs`` (see *training* in
                :meth:`HFEngine.__init__`), then to 100.
            batch: Batch size override. Falls back to the recipe's
                ``training.batch``, then to each subset's configured
                ``batch_size``.
            learning_rate: Initial learning rate. Falls back to the recipe's
                ``training.learning_rate``, then to 5e-5.
            patience: Early-stopping patience, in evaluation rounds. Falls
                back to the recipe's ``training.patience``. Only takes effect
                when a non-empty validation split is attached; selection is
                by evaluation loss, since Geti's own metric callables are
                only computed in :meth:`test`, not during training.
            precision: Same value space as Lightning's ``_PRECISION_INPUT``
                (``16``, ``32``, ``"bf16-mixed"``, etc.). Falls back to the
                recipe's ``training.precision``, then to ``"bf16-mixed"``
                since XPU is the primary accelerator.
            callbacks: Training callbacks. Objects with
                ``_on_progress_update``/``_min_p``/``_max_p`` are consumed for
                progress reporting (G18); genuine
                ``transformers.TrainerCallback`` instances are passed through
                to ``Trainer`` unchanged; anything else is dropped.
            checkpoint: Optional checkpoint to resume or warm-start from.
            **kwargs: Additional ``transformers.TrainingArguments`` overrides.

        Returns:
            The final logged metrics, keyed with the same ``train/`` /
            ``val/`` convention as the metrics CSV.

        Raises:
            ValueError: If the engine was built from a bare data-root path
                rather than a :class:`DataModule`.
        """
        if self._datamodule is None:
            msg = (
                "HFEngine.train() requires a DataModule to build dataloaders from; "
                "got a bare data-root path. Build a DataModule first, e.g. via "
                "DataModule(...) directly, or by resolving a recipe through "
                "HFEngine.from_config() / create_engine()."
            )
            raise ValueError(msg)

        defaults = self._training_defaults
        max_epochs = max_epochs if max_epochs is not None else defaults.get("max_epochs")
        batch = batch if batch is not None else defaults.get("batch")
        learning_rate = learning_rate if learning_rate is not None else defaults.get("learning_rate")
        patience = patience if patience is not None else defaults.get("patience")
        precision = precision if precision is not None else defaults.get("precision", "bf16-mixed")

        if checkpoint is not None:
            self._model.load_checkpoint(checkpoint)

        fp16, bf16 = _resolve_precision(precision)
        progress_fn, min_p, max_p = extract_progress_fn(callbacks)

        trainer_callbacks: list[Any] = [cb for cb in (callbacks or []) if isinstance(cb, TrainerCallback)]
        if progress_fn is not None:
            trainer_callbacks.append(HFProgressCallback(progress_fn, min_p, max_p))
        if is_xpu_available():
            trainer_callbacks.append(XPUMemoryCallback())

        val_subset = self._datamodule.subsets.get("val")
        has_eval = bool(val_subset) and len(val_subset) > 0

        training_args_kwargs: dict[str, Any] = {
            "output_dir": str(self._work_dir / "train"),
            "num_train_epochs": max_epochs if max_epochs is not None else 100,
            "per_device_train_batch_size": batch or self._datamodule.train_subset.batch_size,
            "per_device_eval_batch_size": batch or self._datamodule.val_subset.batch_size,
            "learning_rate": learning_rate if learning_rate is not None else 5e-5,
            "fp16": fp16,
            "bf16": bf16,
            "remove_unused_columns": False,
            "report_to": [],
            "label_names": list(self._model.label_keys),
            "use_cpu": self._device.type == "cpu",
            "eval_strategy": "epoch" if has_eval else "no",
            "save_strategy": "epoch" if has_eval else "no",
            "logging_strategy": "epoch",
        }
        if has_eval and patience is not None:
            training_args_kwargs.update(
                load_best_model_at_end=True,
                metric_for_best_model="eval_loss",
                greater_is_better=False,
            )
            trainer_callbacks.append(EarlyStoppingCallback(early_stopping_patience=patience))
        training_args_kwargs.update(kwargs)

        args = TrainingArguments(**training_args_kwargs)
        trainer = GetiTuneHFTrainer(
            self._model,
            self._datamodule,
            model=self._model.hf_model,
            args=args,
            # get_train_dataloader/get_eval_dataloader build the real loaders
            # via HFDatasetAdapter; these are only here so Trainer's own
            # startup validation (which checks for an eval_dataset whenever
            # eval_strategy != "no") doesn't reject a valid configuration.
            train_dataset=self._datamodule.subsets["train"],
            eval_dataset=val_subset if has_eval else None,
            callbacks=trainer_callbacks,
        )
        trainer.train()

        best_dir = self._work_dir / self._CHECKPOINT_DIR_NAME
        trainer.save_model(str(best_dir))
        self._model.record_checkpoint(best_dir)

        write_metrics_csv(trainer.state.log_history, self._work_dir)

        return _final_metrics(trainer.state.log_history)

    def test(
        self,
        metric: MetricCallable | None = None,
        batch: int | None = None,
        checkpoint: PathLike | None = None,
        **kwargs,
    ) -> METRICS:
        """Evaluate the model on the test split.

        Bypasses ``transformers.Trainer.evaluate()``: see
        ``GetiTuneHFTrainer.evaluate_with_metric`` for why. Results are
        computed by the model's own :meth:`HFModel.build_default_metric`
        (or an override), then flattened to ``test/`` scalar keys, matching
        the naming convention ``LightningEngine.test()`` uses.

        Args:
            metric: A callable taking ``label_info`` and returning a
                ``torchmetrics`` ``Metric``/``MetricCollection``, used
                instead of the model's default metric.
            batch: Batch size override. Defaults to the test subset's
                configured ``batch_size``.
            checkpoint: Optional checkpoint to load before evaluating.
            **kwargs: Additional ``transformers.TrainingArguments`` overrides.

        Returns:
            Scalar metrics keyed with the ``test/`` prefix.

        Raises:
            ValueError: If the engine was built from a bare data-root path,
                or the attached DataModule has no (non-empty) test split.
        """
        if self._datamodule is None:
            msg = "HFEngine.test() requires a DataModule to build a dataloader from; got a bare data-root path."
            raise ValueError(msg)

        if checkpoint is not None:
            self._model.load_checkpoint(checkpoint)

        trainer = self._build_test_scoped_trainer("test", batch, kwargs)

        metric_obj = metric(self._model.label_info) if metric is not None else self._model.build_default_metric()
        metric_obj = metric_obj.to(self._device)
        results = trainer.evaluate_with_metric(metric_obj)
        return _format_test_metrics(results)

    def predict(
        self,
        confidence_threshold: float = 0.5,
        batch: int | None = None,
        checkpoint: PathLike | None = None,
        **kwargs,
    ) -> ANNOTATIONS:
        """Run inference on the test split.

        Like ``test()``, this always runs over the attached DataModule's
        test split rather than an arbitrary source path — the same
        convention ``LightningEngine.predict()`` and
        ``DataModule.predict_dataloader()`` use (predicting is "run over the
        test images", ground truth simply unused). A bare data-root path
        (no attached source-image loader) is not supported.

        Args:
            confidence_threshold: Minimum score for a detection / instance
                segmentation prediction to be kept. Not applied to
                classification (whose scores are per-class probabilities,
                not a filtering signal) or semantic segmentation (which has
                no per-prediction score at all).
            batch: Batch size override. Defaults to the test subset's
                configured ``batch_size``.
            checkpoint: Optional checkpoint to load before predicting.
            **kwargs: Additional ``transformers.TrainingArguments`` overrides.

        Returns:
            One prediction per test-split image.

        Raises:
            ValueError: If the engine was built from a bare data-root path,
                or the attached DataModule has no (non-empty) test split.
        """
        if self._datamodule is None:
            msg = "HFEngine.predict() requires a DataModule to build a dataloader from; got a bare data-root path."
            raise ValueError(msg)

        if checkpoint is not None:
            self._model.load_checkpoint(checkpoint)

        trainer = self._build_test_scoped_trainer("predict", batch, kwargs)

        predictions: list[Prediction] = []
        for pred_batch in trainer.predict_batches():
            predictions.extend(_unbatch_predictions(pred_batch, confidence_threshold))
        return predictions  # pyrefly: ignore[bad-return]

    def _build_test_scoped_trainer(self, subdir: str, batch: int | None, kwargs: dict[str, Any]) -> GetiTuneHFTrainer:
        """Build a :class:`GetiTuneHFTrainer` scoped to the test split, shared by ``test()``/``predict()``.

        Both callers need the identical setup (test-split guard, output dir,
        eval batch size, device flag), so it lives here once rather than
        twice. No ``train_dataset`` is passed — ``Trainer.__init__`` doesn't
        validate its presence at construction time, only ``.train()`` does.

        Args:
            subdir: Sub-directory of ``work_dir`` used as this run's
                ``output_dir`` (``"test"`` or ``"predict"``).
            batch: Batch size override, or ``None`` to use the test subset's
                configured ``batch_size``.
            kwargs: Additional ``transformers.TrainingArguments`` overrides.

        Returns:
            A trainer whose ``get_test_dataloader()`` is ready to use.

        Raises:
            ValueError: If the attached DataModule has no (non-empty) test split.
        """
        if self._datamodule is None:
            msg = "HFEngine._build_test_scoped_trainer() requires a DataModule; got a bare data-root path."
            raise ValueError(msg)

        test_subset = self._datamodule.subsets.get("test")
        if not test_subset:
            msg = "The attached DataModule has no (non-empty) test split."
            raise ValueError(msg)

        training_args_kwargs: dict[str, Any] = {
            "output_dir": str(self._work_dir / subdir),
            "per_device_eval_batch_size": batch or self._datamodule.test_subset.batch_size,
            "report_to": [],
            "use_cpu": self._device.type == "cpu",
        }
        training_args_kwargs.update(kwargs)
        args = TrainingArguments(**training_args_kwargs)

        return GetiTuneHFTrainer(
            self._model,
            self._datamodule,
            model=self._model.hf_model,
            args=args,
            eval_dataset=test_subset,
        )

    def export(
        self,
        checkpoint: PathLike | None = None,
        export_format: ExportFormat = ExportFormat.OPENVINO,
        export_precision: Precision = Precision.FP32,
        **kwargs,
    ) -> Path:
        """Export the model to OpenVINO IR or ONNX.

        Mirrors ``UltralyticsEngine.export()``/``LightningModel.export()``:
        metadata embedding, preprocessing parameters, and FP16 compression
        are handled by the model's own ``_exporter``, not here.

        Args:
            checkpoint: Optional checkpoint to load before exporting. When
                omitted, the currently loaded weights are used — typically
                ``best_checkpoint`` right after ``train()``.
            export_format: Target format.
            export_precision: Precision of the exported weights (FP32 or FP16).
            **kwargs: Reserved for future use; currently ignored.

        Returns:
            Path to the exported model file (``.xml`` for OpenVINO, ``.onnx``
            for ONNX).
        """
        if checkpoint is not None:
            self._model.load_checkpoint(checkpoint)
        elif self.best_checkpoint is not None:
            self._model.load_checkpoint(self.best_checkpoint)

        return self._model.export(
            output_dir=self._work_dir,
            base_name=self._EXPORTED_MODEL_BASE_NAME,
            export_format=export_format,
            precision=export_precision,
        )

    @classmethod
    def from_config(
        cls,
        config_path: PathLike,
        data: DataModule | PathLike | None = None,
        work_dir: PathLike | None = None,
        device: str | None = None,
        checkpoint: str | None = None,
        task: str | None = None,
        **kwargs,
    ) -> HFEngine:
        """Build an engine from a Hugging Face recipe.

        Args:
            config_path: Recipe YAML containing ``backend: huggingface``.
            data: A pre-built :class:`DataModule` or a data-root path.
                Required.
            work_dir: Working directory for checkpoints and exports.
            device: Device to use.
            checkpoint: Optional warm-start checkpoint directory.
            task: Task type for disambiguation. Read from the recipe's
                top-level ``task`` field if not given here.
            **kwargs: Backend-specific keyword arguments forwarded to
                :class:`HFEngine`.

        Returns:
            A fully configured :class:`HFEngine`.

        Raises:
            ValueError: If *data* is ``None``.
        """
        if data is None:
            msg = "data (a DataModule or data-root path) is required for HFEngine.from_config."
            raise ValueError(msg)

        configurator = Configurator(data=data, model=Path(str(config_path)), task=task)

        datamodule = configurator.build_datamodule()
        label_info = datamodule.label_info
        model = configurator.create_model(label_info)

        engine_kwargs: dict[str, Any] = {**kwargs}
        if device is not None:
            engine_kwargs["device"] = device
        if checkpoint is not None:
            engine_kwargs["checkpoint"] = checkpoint

        return configurator.create_engine(model=model, data=datamodule, work_dir=work_dir, **engine_kwargs)

    @staticmethod
    def is_supported(model: MODEL, data: DATA) -> bool:
        """Return ``True`` when *model* is an :class:`HFModel`."""
        return bool(isinstance(model, HFModel) and isinstance(data, (DataModule, str, os.PathLike)))

    @property
    def work_dir(self) -> Path:
        """Working directory."""
        return self._work_dir

    @property
    def model(self) -> HFModel:
        """The wrapped :class:`HFModel`."""
        return self._model

    @property
    def datamodule(self) -> DATA:
        """The attached DataModule, or the data-root path.

        Raises:
            ValueError: If neither was configured.
        """
        if self._datamodule is not None:
            return self._datamodule
        if self._data_root is not None:
            return self._data_root
        msg = "No DataModule or data_root configured"
        raise ValueError(msg)

    @property
    def device(self) -> torch.device:
        """Resolved compute device."""
        return self._device

    @property
    def best_checkpoint(self) -> Path | None:
        """Canonical checkpoint after training.

        Unlike Lightning and Ultralytics, a Hugging Face checkpoint is a
        ``save_pretrained()`` directory rather than a file.
        """
        canonical = self._work_dir / self._CHECKPOINT_DIR_NAME
        return canonical if canonical.exists() else None

    @staticmethod
    def _resolve_device(device: str | DeviceType) -> torch.device:
        """Resolve a device spec to a :class:`torch.device`.

        ``"auto"`` prefers XPU, then CUDA, then CPU, matching the rest of
        getitune.

        Args:
            device: ``"auto"``, ``"xpu"``, ``"cuda"``, ``"gpu"``, ``"cpu"``,
                or a :class:`DeviceType`.

        Returns:
            The resolved device.
        """
        if isinstance(device, DeviceType):
            device = {
                DeviceType.auto: "auto",
                DeviceType.xpu: "xpu",
                DeviceType.gpu: "cuda",
                DeviceType.cpu: "cpu",
            }.get(device, str(device.value))

        name = str(device).strip().lower()

        if name == "auto":
            if is_xpu_available():
                return torch.device("xpu")
            if torch.cuda.is_available():
                return torch.device("cuda")
            return torch.device("cpu")
        if name in ("cuda", "gpu"):
            return torch.device("cuda")
        return torch.device(name)

    def __repr__(self) -> str:
        """Return a concise engine summary."""
        return (
            f"{type(self).__name__}(model={type(self._model).__name__}, "
            f"device={self._device}, work_dir={self._work_dir})"
        )


def _resolve_precision(precision: str | int | None) -> tuple[bool, bool]:
    """Map a Lightning-style precision value to ``TrainingArguments(fp16=, bf16=)``.

    Args:
        precision: ``None``, an int (``16``/``32``/``64``), or a string such
            as ``"bf16-mixed"``, matching Lightning's ``_PRECISION_INPUT``.

    Returns:
        ``(fp16, bf16)``. Both ``False`` for 32/64-bit precision, since
        ``Trainer`` trains in fp32 by default when neither flag is set.

    Raises:
        ValueError: If *precision* isn't a recognised value.
    """
    if precision is None:
        return False, False

    value = str(precision).strip().lower()
    if value in {"bf16", "bf16-mixed", "bf16-true"}:
        return False, True
    if value in {"16", "16-mixed", "16-true", "fp16"}:
        return True, False
    if value in {"32", "32-true", "fp32", "64", "64-true", "fp64"}:
        return False, False

    msg = f"Unsupported precision value for the Hugging Face backend: {precision!r}"
    raise ValueError(msg)


def _final_metrics(log_history: list[dict[str, Any]]) -> METRICS:
    """Collapse ``Trainer.state.log_history`` into one flat metrics dict.

    Later entries win, so the result holds the most recent value logged for
    each key, with the same ``train/`` / ``val/`` naming the metrics CSV uses.
    """
    metrics: dict[str, float] = {}
    for entry in log_history:
        for key, value in entry.items():
            if key in ("epoch", "step") or not isinstance(value, (int, float)):
                continue
            metrics[remap_log_key(key)] = float(value)
    return metrics


_NON_SCALAR_METRIC_KEYS = {"classes", "map_per_class", "mar_100_per_class", "ious"}


def _format_test_metrics(results: dict[str, Any]) -> METRICS:
    """Convert a ``torchmetrics`` ``compute()`` output to a flat ``test/``-prefixed dict.

    Mirrors ``LightningModel._log_metrics`` and
    ``UltralyticsEngine._format_torchmetrics_results``: only scalar values
    are kept; auxiliary keys (``classes``, ``map_per_class``,
    ``mar_100_per_class``, ``ious``) are skipped, and nested dicts (as
    returned by a ``MetricCollection``) are flattened recursively.

    Args:
        results: Dict returned by ``metric.compute()``.

    Returns:
        Flat dict, e.g. ``{"test/map": 0.75, "test/map_50": 0.90}``.
    """
    formatted: dict[str, float] = {}

    def _add(prefix: str, value: Any) -> None:  # noqa: ANN401
        if isinstance(value, dict):
            for key, nested in value.items():
                _add(prefix if prefix.endswith(f"/{key}") else f"{prefix}/{key}", nested)
            return
        if prefix.rsplit("/", 1)[-1] in _NON_SCALAR_METRIC_KEYS:
            return
        if isinstance(value, torch.Tensor):
            if value.numel() == 1:
                formatted[prefix] = value.item()
            else:
                logger.debug("Skipping non-scalar torchmetric '%s' with %d elements", prefix, value.numel())
        elif isinstance(value, (int, float)):
            formatted[prefix] = float(value)

    for name, value in results.items():
        _add(f"test/{name}", value)
    return formatted


def _rewrap(sliced: torch.Tensor, like: tv_tensors.TVTensor) -> torch.Tensor:
    """Re-wrap a boolean-indexed slice as the same ``tv_tensors`` subclass as *like*.

    Plain tensor indexing (``bboxes[keep]``) silently drops the
    ``BoundingBoxes``/``Mask`` subclass, which downstream consumers of
    :class:`Prediction` rely on.
    """
    # pyrefly mis-resolves ``tv_tensors.wrap`` to ``torch._dynamo`` due to a
    # name collision and rejects the valid ``like=`` kwarg; the call is correct.
    return tv_tensors.wrap(sliced, like=like)  # pyrefly: ignore[bad-argument-type, unexpected-keyword, bad-return]


def _unbatch_predictions(batch: PredictionBatch, confidence_threshold: float) -> list[Prediction]:
    """Split a :class:`PredictionBatch` into one :class:`Prediction` per image.

    Detection and instance segmentation results are filtered by
    ``scores > confidence_threshold`` (a per-box/per-instance score);
    classification scores (per-class probabilities) and semantic
    segmentation (no scores at all) pass through unfiltered.

    Args:
        batch: A postprocessed batch, as returned by ``HFModel.postprocess()``.
        confidence_threshold: Minimum score to keep a box/instance.

    Returns:
        One prediction per image in *batch*, in the same order.
    """
    predictions: list[Prediction] = []
    for i in range(batch.batch_size):
        img_info = batch.imgs_info[i] if batch.imgs_info is not None else None
        label = batch.labels[i] if batch.labels is not None else None
        bboxes = batch.bboxes[i] if batch.bboxes is not None else None
        masks = batch.masks[i] if batch.masks is not None else None
        scores = batch.scores[i] if batch.scores is not None else None

        if scores is not None and bboxes is not None:
            keep = scores > confidence_threshold
            bboxes = _rewrap(bboxes[keep], bboxes)
            scores = scores[keep]
            if label is not None:
                label = label[keep]
            if masks is not None:
                masks = _rewrap(masks[keep], masks)

        predictions.append(
            Prediction(
                image=batch.images[i],
                img_info=img_info,
                label=label,
                bboxes=bboxes,  # pyrefly: ignore[bad-argument-type]
                masks=masks,  # pyrefly: ignore[bad-argument-type]
                scores=scores,
            )
        )
    return predictions
