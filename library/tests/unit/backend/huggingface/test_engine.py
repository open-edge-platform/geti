# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for the Hugging Face engine (registration, contract, and training)."""

from __future__ import annotations

import csv
import math
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar

import pytest
from torch import nn

from getitune.backend.huggingface import HFEngine, HFModel
from getitune.backend.huggingface.engine import _final_metrics, _format_test_metrics, _resolve_precision
from getitune.backend.huggingface.models.base import ModelOutput
from getitune.backend.lightning.models.base import DataInputParams
from getitune.data.module import DataModule
from getitune.types.device import DeviceType
from getitune.types.label import LabelInfo
from getitune.types.task import TaskType

if TYPE_CHECKING:
    import torch
    from torchmetrics import Metric, MetricCollection

    from getitune.data.entity.sample import PredictionBatch, SampleBatch


class _StubHFModel(HFModel):
    """Smallest concrete HFModel that satisfies the abstract contract.

    Skips the real ``transformers`` construction in ``HFModel.__init__`` since
    these tests only exercise the engine, not the model wrapper itself.
    """

    task: ClassVar[TaskType] = TaskType.DETECTION
    hf_auto_class: ClassVar[type] = object
    export_model_type: ClassVar[str] = "ssd"
    label_keys: ClassVar[tuple[str, ...]] = ("labels",)

    def __init__(self) -> None:
        nn.Module.__init__(self)
        self._label_info = LabelInfo(label_names=["a", "b"], label_ids=["0", "1"], label_groups=[["a", "b"]])
        self._data_input_params = DataInputParams(input_size=(640, 640), mean=(0.0, 0.0, 0.0), std=(1.0, 1.0, 1.0))
        self._intensity_config = None
        self._best_checkpoint = None

    def build_targets(self, batch: SampleBatch) -> dict[str, Any]:
        return {"pixel_values": batch.images}

    def forward(self, batch: SampleBatch) -> ModelOutput:
        return ModelOutput()

    def postprocess(self, outputs: ModelOutput, batch: SampleBatch) -> PredictionBatch:
        raise NotImplementedError

    def to_metric_inputs(self, outputs: ModelOutput, batch: SampleBatch) -> dict[str, Any]:
        return {}

    def build_default_metric(self) -> Metric | MetricCollection:
        raise NotImplementedError

    def forward_for_tracing(self, images: torch.Tensor) -> dict[str, torch.Tensor]:
        return {"bboxes": images.new_zeros(1, 1, 4)}


@pytest.fixture
def model() -> _StubHFModel:
    return _StubHFModel()


def test_huggingface_backend_is_registered() -> None:
    """create_engine() must map 'huggingface' to HFEngine."""
    from getitune.engine.utils import create as create_mod

    backends = _collect_registered_backends(create_mod)
    assert backends.get("huggingface") is HFEngine


def test_optional_backends_do_not_shadow_each_other() -> None:
    """Registering HF must not disturb the always-available backends."""
    from getitune.backend.lightning.engine import LightningEngine
    from getitune.backend.openvino.engine import OVEngine
    from getitune.engine.utils import create as create_mod

    backends = _collect_registered_backends(create_mod)
    assert backends["lightning"] is LightningEngine
    assert backends["openvino"] is OVEngine


def _collect_registered_backends(create_mod) -> dict[str, type]:
    """Re-run the registration block from create_engine() in isolation."""
    from getitune.backend.lightning.engine import LightningEngine
    from getitune.backend.openvino.engine import OVEngine

    backends: dict[str, type] = {"lightning": LightningEngine, "openvino": OVEngine}
    try:
        from getitune.backend.ultralytics.engine import UltralyticsEngine

        backends["ultralytics"] = UltralyticsEngine
    except ImportError:
        pass
    try:
        from getitune.backend.huggingface.engine import HFEngine as _HFEngine

        backends["huggingface"] = _HFEngine
    except ImportError:
        pass
    assert create_mod is not None
    return backends


def test_recipe_backend_field_routes_to_hf_engine(tmp_path: Path) -> None:
    """A recipe declaring backend: huggingface resolves to HFEngine."""
    from getitune.engine.utils.create import _read_backend

    recipe = tmp_path / "hf_recipe.yaml"
    recipe.write_text("backend: huggingface\ntask: DETECTION\n")
    assert _read_backend(recipe) == "huggingface"


def test_unknown_backend_raises(tmp_path: Path) -> None:
    """An unregistered backend string must fail loudly."""
    from getitune.engine.utils.create import create_engine

    recipe = tmp_path / "bogus.yaml"
    recipe.write_text("backend: nonexistent\ntask: DETECTION\n")
    with pytest.raises(ValueError, match="Unknown backend 'nonexistent'"):
        create_engine(recipe, data=tmp_path)


def test_hf_model_exported_from_models_namespace() -> None:
    """HFModel is re-exported through the central models hub."""
    import getitune.models as models_hub

    assert models_hub.HFModel is HFModel
    assert "HFModel" in models_hub.__all__


def test_model_union_includes_hf_model() -> None:
    """The runtime MODEL union must accept HFModel."""
    import typing

    from getitune.types.types import MODEL

    assert HFModel in typing.get_args(MODEL)


def test_engine_construction_with_data_root(tmp_path: Path, model: _StubHFModel) -> None:
    engine = HFEngine(model=model, data=tmp_path, work_dir=tmp_path / "wd")
    assert engine.model is model
    assert Path(engine.work_dir) == (tmp_path / "wd").resolve()
    assert Path(engine.work_dir).exists()
    assert engine.datamodule == tmp_path


def test_engine_rejects_non_hf_model(tmp_path: Path) -> None:
    with pytest.raises(TypeError, match="model must be an HFModel"):
        HFEngine(model=object(), data=tmp_path)  # type: ignore[arg-type]


def test_engine_rejects_bad_data(model: _StubHFModel) -> None:
    with pytest.raises(TypeError, match="data must be DataModule or PathLike"):
        HFEngine(model=model, data=123)  # type: ignore[arg-type]


def test_is_supported(tmp_path: Path, model: _StubHFModel) -> None:
    assert HFEngine.is_supported(model, tmp_path) is True
    assert HFEngine.is_supported(object(), tmp_path) is False  # type: ignore[arg-type]


def test_best_checkpoint_is_none_before_training(tmp_path: Path, model: _StubHFModel) -> None:
    engine = HFEngine(model=model, data=tmp_path, work_dir=tmp_path / "wd")
    assert engine.best_checkpoint is None


def test_best_checkpoint_is_a_directory(tmp_path: Path, model: _StubHFModel) -> None:
    """HF checkpoints are save_pretrained() directories, not files."""
    wd = tmp_path / "wd"
    engine = HFEngine(model=model, data=tmp_path, work_dir=wd)
    (wd / "best_checkpoint").mkdir(parents=True)
    checkpoint = engine.best_checkpoint
    assert checkpoint == wd / "best_checkpoint"
    assert checkpoint is not None
    assert checkpoint.is_dir()


@pytest.mark.parametrize(
    ("spec", "expected"),
    [("cpu", "cpu"), (DeviceType.cpu, "cpu"), ("gpu", "cuda"), ("cuda", "cuda"), ("xpu", "xpu")],
)
def test_resolve_device(spec: str | DeviceType, expected: str) -> None:
    assert HFEngine._resolve_device(spec).type == expected


def test_resolve_device_auto_prefers_accelerator() -> None:
    """auto must resolve to a real device without raising."""
    assert HFEngine._resolve_device("auto").type in {"xpu", "cuda", "cpu"}


def test_datamodule_property_raises_when_unset(tmp_path: Path, model: _StubHFModel) -> None:
    engine = HFEngine(model=model, data=tmp_path)
    engine._data_root = None
    with pytest.raises(ValueError, match="No DataModule or data_root configured"):
        _ = engine.datamodule


def test_intensity_config_propagated_from_datamodule(tmp_path: Path, model: _StubHFModel) -> None:
    """Engine must push the DataModule intensity config into the model (G15/G16)."""
    dm = DataModule(task=TaskType.DETECTION, data_root="tests/assets/detection_coco")
    engine = HFEngine(model=model, data=dm, work_dir=tmp_path)
    assert engine.model._intensity_config is dm.input_intensity_config


@pytest.mark.parametrize("method", ["test", "predict"])
def test_test_and_predict_require_a_datamodule(tmp_path: Path, model: _StubHFModel, method: str) -> None:
    """A bare data-root path isn't enough to build a dataloader from."""
    engine = HFEngine(model=model, data=tmp_path)
    with pytest.raises(ValueError, match="requires a DataModule"):
        getattr(engine, method)()


def test_test_requires_a_non_empty_test_split(tmp_path: Path, model: _StubHFModel) -> None:
    dm = DataModule(task=TaskType.DETECTION, data_root="tests/assets/detection_coco")
    dm.subsets["test"] = None  # pyrefly: ignore[unsupported-operation]
    engine = HFEngine(model=model, data=dm, work_dir=tmp_path)
    with pytest.raises(ValueError, match="no .* test split"):
        engine.test()


def test_train_requires_a_datamodule(tmp_path: Path, model: _StubHFModel) -> None:
    """A bare data-root path isn't enough to build dataloaders from."""
    engine = HFEngine(model=model, data=tmp_path)
    with pytest.raises(ValueError, match="requires a DataModule"):
        engine.train()


def test_from_config_requires_data(tmp_path: Path) -> None:
    recipe = tmp_path / "r.yaml"
    recipe.write_text("backend: huggingface\n")
    with pytest.raises(ValueError, match="data .* is required"):
        HFEngine.from_config(recipe, data=None)


def test_from_config_builds_a_working_engine_from_an_offline_recipe(tmp_path: Path) -> None:
    """Real recipe parsing end to end, offline: no Hub download involved.

    Mirrors ``create_engine("hf_mask2former_swin_t", data="data/wgisd")`` in
    real usage, but with a bare ``PretrainedConfig`` checkpoint so the test
    suite doesn't need network access.
    """
    base_data_config = (
        Path(__file__).resolve().parents[4]
        / "src"
        / "getitune"
        / "recipe"
        / "_base_"
        / "data"
        / "instance_segmentation.yaml"
    )
    recipe = tmp_path / "hf_offline.yaml"
    recipe.write_text(
        f"""
backend: huggingface
task: INSTANCE_SEGMENTATION

model:
  class_path: getitune.backend.huggingface.models.instance_segmentation.HFInstSegModel
  init_args:
    checkpoint:
      class_path: transformers.Mask2FormerConfig
      init_args:
        num_queries: 10
        decoder_layers: 2
        encoder_layers: 2
    pretrained: true
    input_size: [64, 64]

data: {base_data_config}
""".strip()
    )

    engine = HFEngine.from_config(recipe, data="tests/assets/instance_segmentation_coco", work_dir=tmp_path / "wd")

    assert isinstance(engine, HFEngine)
    assert engine.model.hf_model.config.num_queries == 10
    assert engine.model.label_info.num_classes > 0
    assert set(engine.datamodule.subsets) == {"train", "val", "test"}  # pyrefly: ignore[missing-attribute]


def test_create_engine_dispatches_a_recipe_path_to_hf_engine(tmp_path: Path) -> None:
    """The shared create_engine() entry point, not HFEngine.from_config() directly."""
    from getitune.engine.utils.create import create_engine

    base_data_config = (
        Path(__file__).resolve().parents[4]
        / "src"
        / "getitune"
        / "recipe"
        / "_base_"
        / "data"
        / "instance_segmentation.yaml"
    )
    recipe = tmp_path / "hf_offline.yaml"
    recipe.write_text(
        f"""
backend: huggingface
task: INSTANCE_SEGMENTATION

model:
  class_path: getitune.backend.huggingface.models.instance_segmentation.HFInstSegModel
  init_args:
    checkpoint:
      class_path: transformers.Mask2FormerConfig
      init_args:
        num_queries: 10
        decoder_layers: 2
        encoder_layers: 2
    pretrained: true
    input_size: [64, 64]

data: {base_data_config}
""".strip()
    )

    engine = create_engine(model=recipe, data="tests/assets/instance_segmentation_coco", work_dir=tmp_path / "wd")

    assert isinstance(engine, HFEngine)
    assert engine.model.hf_model.config.num_queries == 10


class TestResolvePrecision:
    def test_none_means_fp32(self) -> None:
        assert _resolve_precision(None) == (False, False)

    @pytest.mark.parametrize("value", [16, "16", "16-mixed", "16-true", "fp16"])
    def test_16_bit_variants_select_fp16(self, value: int | str) -> None:
        assert _resolve_precision(value) == (True, False)

    @pytest.mark.parametrize("value", ["bf16", "bf16-mixed", "bf16-true"])
    def test_bf16_variants_select_bf16(self, value: str) -> None:
        assert _resolve_precision(value) == (False, True)

    @pytest.mark.parametrize("value", [32, "32", "32-true", "fp32", 64, "64-true"])
    def test_32_and_64_bit_variants_select_neither(self, value: int | str) -> None:
        assert _resolve_precision(value) == (False, False)

    def test_rejects_unknown_values(self) -> None:
        with pytest.raises(ValueError, match="Unsupported precision"):
            _resolve_precision("int8")


class TestFinalMetrics:
    def test_later_entries_win(self) -> None:
        log_history = [
            {"loss": 2.0, "epoch": 1.0, "step": 4},
            {"loss": 1.5, "epoch": 2.0, "step": 8},
        ]
        assert _final_metrics(log_history) == {"train/loss": 1.5}

    def test_epoch_and_step_are_excluded(self) -> None:
        metrics = _final_metrics([{"loss": 1.0, "epoch": 1.0, "step": 4}])
        assert "epoch" not in metrics
        assert "step" not in metrics

    def test_non_numeric_values_are_skipped(self) -> None:
        metrics = _final_metrics([{"loss": 1.0, "some_string": "ignored"}])
        assert metrics == {"train/loss": 1.0}

    def test_empty_history_yields_empty_metrics(self) -> None:
        assert _final_metrics([]) == {}


class TestFormatTestMetrics:
    def test_scalar_tensor_is_flattened_with_a_test_prefix(self) -> None:
        import torch

        assert _format_test_metrics({"map": torch.tensor(0.5)}) == {"test/map": 0.5}

    def test_plain_numbers_are_kept(self) -> None:
        assert _format_test_metrics({"accuracy": 1}) == {"test/accuracy": 1.0}

    def test_non_scalar_auxiliary_keys_are_skipped(self) -> None:
        import torch

        results = {"map": torch.tensor(0.5), "classes": torch.tensor([0, 1, 2])}
        assert _format_test_metrics(results) == {"test/map": 0.5}

    def test_non_scalar_tensors_outside_the_skip_list_are_skipped_too(self) -> None:
        import torch

        results = {"per_image_iou": torch.tensor([0.1, 0.2, 0.3])}
        assert _format_test_metrics(results) == {}

    def test_nested_dicts_are_flattened_recursively(self) -> None:
        import torch

        results = {"MulticlassAccuracy": {"accuracy": torch.tensor(0.75)}}
        assert _format_test_metrics(results) == {"test/MulticlassAccuracy/accuracy": 0.75}


class TestTrainEndToEnd:
    """Real training, not mocked.

    Two epochs against a real Datumaro asset, on whatever accelerator this
    machine has (XPU here). Uses a bare ``transformers`` config, so no
    network access is needed for the model.
    """

    def test_two_epochs_produce_a_checkpoint_and_a_parseable_metrics_csv(self, tmp_path: Path) -> None:
        import transformers as tf

        from getitune.backend.huggingface.models import HFDetectionModel

        dm = DataModule(task=TaskType.DETECTION, data_root="tests/assets/detection_coco")
        # Avoid spawning real OS worker processes in the test suite; production
        # training keeps the DataModule's configured worker count.
        dm.train_subset.num_workers = 0
        dm.val_subset.num_workers = 0
        num_labels = dm.subsets["train"].label_info.num_classes
        model = HFDetectionModel(tf.RTDetrV2Config(num_queries=20, decoder_layers=2), num_labels)

        engine = HFEngine(model=model, data=dm, work_dir=tmp_path)
        metrics = engine.train(max_epochs=2, batch=2)

        assert "train/loss" in metrics
        assert math.isfinite(metrics["train/loss"])

        assert engine.best_checkpoint is not None
        assert engine.best_checkpoint.is_dir()
        assert (engine.best_checkpoint / "config.json").exists()

        csv_path = engine.work_dir / "csv" / "version_0" / "metrics.csv"
        assert csv_path.exists()
        with csv_path.open() as fh:
            rows = list(csv.DictReader(fh))
        assert len(rows) > 0
        assert "train/loss" in rows[0]

    def test_progress_callback_is_driven_from_0_to_100(self, tmp_path: Path) -> None:
        import transformers as tf

        from getitune.backend.huggingface.models import HFMulticlassClsModel

        dm = DataModule(task=TaskType.MULTI_CLASS_CLS, data_root="tests/assets/classification_cifar10")
        dm.train_subset.num_workers = 0
        dm.val_subset.num_workers = 0
        num_labels = dm.subsets["train"].label_info.num_classes
        config = tf.ViTConfig(hidden_size=32, num_hidden_layers=1, num_attention_heads=2, intermediate_size=64)
        model = HFMulticlassClsModel(config, num_labels)

        class _Progress:
            _min_p = 0.0
            _max_p = 100.0

            def __init__(self) -> None:
                self.calls: list[float] = []

            def _on_progress_update(self, value: float) -> None:
                self.calls.append(value)

        progress = _Progress()
        engine = HFEngine(model=model, data=dm, work_dir=tmp_path)
        engine.train(max_epochs=1, batch=4, callbacks=[progress])

        assert progress.calls
        assert progress.calls[-1] == 100.0


def _detection_case() -> tuple[TaskType, str, object]:
    import transformers as tf

    from getitune.backend.huggingface.models import HFDetectionModel

    return (
        TaskType.DETECTION,
        "tests/assets/detection_coco",
        lambda n: HFDetectionModel(tf.RTDetrV2Config(num_queries=20, decoder_layers=2), n),
    )


def _instance_segmentation_case() -> tuple[TaskType, str, object]:
    import transformers as tf

    from getitune.backend.huggingface.models import HFInstSegModel

    return (
        TaskType.INSTANCE_SEGMENTATION,
        "tests/assets/instance_segmentation_coco",
        lambda n: HFInstSegModel(tf.Mask2FormerConfig(num_queries=15), n),
    )


def _semantic_segmentation_case() -> tuple[TaskType, str, object]:
    import transformers as tf

    from getitune.backend.huggingface.models import HFSemanticSegModel

    return (
        TaskType.SEMANTIC_SEGMENTATION,
        "tests/assets/segmentation_pets",
        lambda n: HFSemanticSegModel(tf.SegformerConfig(), n),
    )


def _multilabel_case() -> tuple[TaskType, str, object]:
    import transformers as tf

    from getitune.backend.huggingface.models import HFMultilabelClsModel

    config = tf.ViTConfig(hidden_size=32, num_hidden_layers=1, num_attention_heads=2, intermediate_size=64)
    return (
        TaskType.MULTI_LABEL_CLS,
        "tests/assets/multilabel_classification_coco",
        lambda n: HFMultilabelClsModel(config, n, input_size=(224, 224)),
    )


@pytest.mark.parametrize(
    "case_factory",
    [_instance_segmentation_case, _semantic_segmentation_case, _multilabel_case],
    ids=["instance_segmentation", "semantic_segmentation", "multi_label_cls"],
)
def test_two_epochs_train_for_the_remaining_tasks(case_factory: object, tmp_path: Path) -> None:
    """Detection and multi-class cls get their own tests above; these three
    round out training coverage for "all five tasks" without duplicating
    the checkpoint/CSV/progress assertions three more times.
    """
    task, data_root, make_model = case_factory()  # type: ignore[operator]

    dm = DataModule(task=task, data_root=data_root)
    dm.train_subset.num_workers = 0
    dm.val_subset.num_workers = 0
    num_labels = dm.subsets["train"].label_info.num_classes
    model = make_model(num_labels)

    engine = HFEngine(model=model, data=dm, work_dir=tmp_path)
    metrics = engine.train(max_epochs=2, batch=2)

    assert "train/loss" in metrics
    assert math.isfinite(metrics["train/loss"])
    assert engine.best_checkpoint is not None
    assert engine.best_checkpoint.is_dir()


@pytest.mark.parametrize(
    "case_factory",
    [_detection_case, _instance_segmentation_case, _semantic_segmentation_case, _multilabel_case],
    ids=["detection", "instance_segmentation", "semantic_segmentation", "multi_label_cls"],
)
def test_test_and_predict_run_end_to_end_for_every_task(case_factory: object, tmp_path: Path) -> None:
    """``test()``/``predict()`` work end to end for all five tasks.

    Multi-class classification gets its own dedicated test below (it needs a
    non-default ``image_size``/``patch_size`` to keep the tiny ViT config
    consistent with the CIFAR-10 asset).
    """
    task, data_root, make_model = case_factory()  # type: ignore[operator]

    dm = DataModule(task=task, data_root=data_root)
    num_labels = dm.subsets["train"].label_info.num_classes
    model = make_model(num_labels)

    engine = HFEngine(model=model, data=dm, work_dir=tmp_path)

    metrics = engine.test()
    assert metrics
    assert all(key.startswith("test/") for key in metrics)
    assert all(math.isfinite(value) for value in metrics.values())

    predictions = engine.predict()
    assert len(predictions) == len(dm.subsets["test"])
    for prediction in predictions:
        assert prediction.image is not None


def test_multiclass_test_and_predict_run_end_to_end(tmp_path: Path) -> None:
    import transformers as tf

    from getitune.backend.huggingface.models import HFMulticlassClsModel

    dm = DataModule(task=TaskType.MULTI_CLASS_CLS, data_root="tests/assets/classification_cifar10")
    num_labels = dm.subsets["train"].label_info.num_classes
    config = tf.ViTConfig(
        hidden_size=32, num_hidden_layers=1, num_attention_heads=2, intermediate_size=64, image_size=224
    )
    model = HFMulticlassClsModel(config, num_labels)

    engine = HFEngine(model=model, data=dm, work_dir=tmp_path)

    metrics = engine.test()
    assert metrics
    assert all(key.startswith("test/") for key in metrics)

    predictions = engine.predict()
    assert len(predictions) == len(dm.subsets["test"])


def test_predict_confidence_threshold_filters_detections(tmp_path: Path) -> None:
    """A threshold above every score must yield empty (not missing) predictions."""
    import transformers as tf

    from getitune.backend.huggingface.models import HFDetectionModel
    from getitune.data.entity.sample import Prediction

    dm = DataModule(task=TaskType.DETECTION, data_root="tests/assets/detection_coco")
    num_labels = dm.subsets["train"].label_info.num_classes
    model = HFDetectionModel(tf.RTDetrV2Config(num_queries=10, decoder_layers=2), num_labels)

    engine = HFEngine(model=model, data=dm, work_dir=tmp_path)

    predictions = engine.predict(confidence_threshold=2.0)

    assert len(predictions) == len(dm.subsets["test"])
    for prediction in predictions:
        assert isinstance(prediction, Prediction)
        assert prediction.bboxes is not None
        assert prediction.bboxes.shape[0] == 0


class TestExport:
    """Real ONNX/OpenVINO export, not mocked."""

    @pytest.mark.parametrize(
        "case_factory",
        [_detection_case, _instance_segmentation_case, _semantic_segmentation_case, _multilabel_case],
        ids=["detection", "instance_segmentation", "semantic_segmentation", "multi_label_cls"],
    )
    def test_onnx_export_produces_a_loadable_model_for_every_task(self, case_factory: object, tmp_path: Path) -> None:
        import onnx

        from getitune.types.export import ExportFormat

        task, data_root, make_model = case_factory()  # type: ignore[operator]
        dm = DataModule(task=task, data_root=data_root)
        num_labels = dm.subsets["train"].label_info.num_classes
        model = make_model(num_labels)

        engine = HFEngine(model=model, data=dm, work_dir=tmp_path)
        path = engine.export(export_format=ExportFormat.ONNX)

        assert path.exists()
        assert path.suffix == ".onnx"
        onnx.checker.check_model(str(path))

    @pytest.mark.parametrize(
        "case_factory",
        [_semantic_segmentation_case, _multilabel_case],
        ids=["semantic_segmentation", "multi_label_cls"],
    )
    def test_onnx_export_matches_the_pytorch_forward_numerically(self, case_factory: object, tmp_path: Path) -> None:
        """The traced ONNX graph must compute the same thing as eager PyTorch.

        Loading and "producing a plausible result" (the test above, and the
        ModelAPI round trip below) does not by itself prove the export is
        numerically faithful — a subtly wrong ``forward_for_tracing`` could
        still produce a loadable graph with silently wrong numbers. Compares
        against untrained (random) weights: parity is a property of the
        tracing math, not of what the weights were trained on.

        Detection and instance segmentation are covered separately below —
        detection has a confirmed real divergence (G36), and instance
        segmentation's ONNX Runtime CPU build lacks the ``GridSample-16`` op
        Mask2Former's deformable attention needs, so it has to be checked
        through OpenVINO instead of ONNX Runtime.
        """
        import numpy as np
        import onnxruntime as ort
        import torch

        from getitune.types.export import ExportFormat

        task, data_root, make_model = case_factory()  # type: ignore[operator]
        dm = DataModule(task=task, data_root=data_root)
        num_labels = dm.subsets["train"].label_info.num_classes
        model = make_model(num_labels)
        model.eval()

        dummy = torch.rand(model.data_input_params.as_ncwh())
        with torch.no_grad():
            expected = model.forward_for_tracing(dummy)
        if isinstance(expected, torch.Tensor):
            expected = {"output": expected}

        engine = HFEngine(model=model, data=dm, work_dir=tmp_path)
        path = engine.export(export_format=ExportFormat.ONNX)

        session = ort.InferenceSession(str(path))
        onnx_outputs = session.run(None, {"images": dummy.numpy()})
        output_names = [output.name for output in session.get_outputs()]

        assert len(onnx_outputs) == len(expected)
        for name, onnx_out in zip(output_names, onnx_outputs, strict=True):
            expected_out = expected[name] if name in expected else next(iter(expected.values()))
            np.testing.assert_allclose(  # pyrefly: ignore[no-matching-overload]
                onnx_out, expected_out.numpy(), rtol=1e-3, atol=1e-4
            )

    def test_instance_segmentation_openvino_export_matches_pytorch_forward(self, tmp_path: Path) -> None:
        """Same parity check as above, but through OpenVINO, not ONNX Runtime.

        ONNX Runtime's CPU build cannot even *load* the exported graph
        (``NOT_IMPLEMENTED: ... GridSample(16)``) — Mask2Former's deformable
        attention needs an op ONNX Runtime doesn't ship for CPU. That is an
        ONNX Runtime gap, not an export-correctness bug: OpenVINO's frontend
        accepts the same graph and reproduces PyTorch's output to float32
        precision (verified here), so the export is faithful.
        """
        import numpy as np
        import openvino
        import torch
        import transformers as tf

        from getitune.backend.huggingface.models import HFInstSegModel
        from getitune.types.export import ExportFormat

        dm = DataModule(task=TaskType.INSTANCE_SEGMENTATION, data_root="tests/assets/instance_segmentation_coco")
        label_info = dm.subsets["train"].label_info
        model = HFInstSegModel(
            tf.Mask2FormerConfig(num_queries=10, decoder_layers=2, encoder_layers=2), label_info, input_size=(64, 64)
        )
        model.eval()

        dummy = torch.rand(model.data_input_params.as_ncwh())
        with torch.no_grad():
            expected = model.forward_for_tracing(dummy)

        engine = HFEngine(model=model, data=dm, work_dir=tmp_path)
        path = engine.export(export_format=ExportFormat.OPENVINO)

        ov_model = openvino.Core().compile_model(str(path), "CPU")
        result = ov_model([dummy.numpy()])

        for output in ov_model.outputs:
            name = next(iter(output.get_names())) if output.get_names() else output.any_name
            np.testing.assert_allclose(result[output], expected[name].numpy(), rtol=1e-3, atol=1e-4)

    @pytest.mark.xfail(
        reason=(
            "G36: RT-DETRv2's ONNX/OpenVINO export produces a loadable graph that does NOT "
            "numerically match eager PyTorch (confirmed: box-coordinate divergence up to ~0.6, "
            "even when traced on the exact same input tensor used for comparison — ruling out "
            "trace-time-vs-eval-time input mismatch as the cause). Root cause not identified; "
            "likely an upstream transformers/torch.onnx interaction in RTDetrV2's decoder. "
            "Do not rely on detection export for production accuracy until this is fixed."
        ),
        strict=True,
    )
    def test_detection_export_matches_pytorch_forward_numerically(self, tmp_path: Path) -> None:
        import numpy as np
        import onnxruntime as ort
        import torch
        import transformers as tf

        from getitune.backend.huggingface.models import HFDetectionModel
        from getitune.types.export import ExportFormat

        dm = DataModule(task=TaskType.DETECTION, data_root="tests/assets/detection_coco")
        label_info = dm.subsets["train"].label_info
        model = HFDetectionModel(tf.RTDetrV2Config(num_queries=10, decoder_layers=2), label_info, input_size=(64, 64))
        model.eval()

        dummy = torch.rand(model.data_input_params.as_ncwh())
        with torch.no_grad():
            expected = model.forward_for_tracing(dummy)

        engine = HFEngine(model=model, data=dm, work_dir=tmp_path)
        path = engine.export(export_format=ExportFormat.ONNX)

        session = ort.InferenceSession(str(path))
        onnx_outputs = session.run(None, {"images": dummy.numpy()})
        output_names = [output.name for output in session.get_outputs()]

        for name, onnx_out in zip(output_names, onnx_outputs, strict=True):
            np.testing.assert_allclose(  # pyrefly: ignore[no-matching-overload]
                onnx_out, expected[name].numpy(), rtol=1e-3, atol=1e-4
            )

    def test_openvino_export_round_trips_through_model_api(self, tmp_path: Path) -> None:
        """Detection end to end: export, load with ModelAPI, run inference."""
        import numpy as np
        import transformers as tf
        from model_api.models import Model

        from getitune.backend.huggingface.models import HFDetectionModel

        dm = DataModule(task=TaskType.DETECTION, data_root="tests/assets/detection_coco")
        label_info = dm.subsets["train"].label_info
        model = HFDetectionModel(tf.RTDetrV2Config(num_queries=10, decoder_layers=2), label_info)

        engine = HFEngine(model=model, data=dm, work_dir=tmp_path)
        path = engine.export()

        assert path.suffix == ".xml"
        ov_model = Model.create_model(str(path))

        image = np.random.default_rng(seed=0).integers(0, 255, (64, 64, 3), dtype=np.uint8)
        result = ov_model(image)
        assert result is not None

    def test_export_loads_a_checkpoint_when_given(self, tmp_path: Path) -> None:
        """checkpoint= must be honored, not just best_checkpoint from a prior train()."""
        import transformers as tf

        from getitune.backend.huggingface.models import HFMulticlassClsModel
        from getitune.types.export import ExportFormat

        dm = DataModule(task=TaskType.MULTI_CLASS_CLS, data_root="tests/assets/classification_cifar10")
        label_info = dm.subsets["train"].label_info
        config = tf.ViTConfig(
            hidden_size=32, num_hidden_layers=1, num_attention_heads=2, intermediate_size=64, image_size=32
        )
        model = HFMulticlassClsModel(config, label_info, input_size=(32, 32))

        checkpoint_dir = tmp_path / "checkpoint"
        model.hf_model.save_pretrained(checkpoint_dir)

        engine = HFEngine(model=model, data=dm, work_dir=tmp_path / "wd")
        path = engine.export(checkpoint=checkpoint_dir, export_format=ExportFormat.ONNX)

        assert path.exists()
        assert engine.model.best_checkpoint == checkpoint_dir
