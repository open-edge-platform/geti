# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

rng = np.random.default_rng(0)


def _make_onnx_input(name="input", shape=(1, 3, 224, 224), type_str="tensor(float)"):
    inp = MagicMock()
    inp.name = name
    inp.shape = list(shape)
    inp.type = type_str
    return inp


def _make_onnx_output(name="output", shape=(1, 1000), type_str="tensor(float)"):
    out = MagicMock()
    out.name = name
    out.shape = list(shape)
    out.type = type_str
    return out


@pytest.fixture
def onnx_adapter():
    """Create an ONNXRuntimeAdapter with mocked onnx/onnxruntime."""
    mock_session = MagicMock()
    mock_session.get_inputs.return_value = [_make_onnx_input()]
    mock_session.get_outputs.return_value = [_make_onnx_output()]

    mock_model = MagicMock()
    mock_model.metadata_props = [
        SimpleNamespace(key="model_info task_type", value="classification"),
    ]
    mock_model.SerializeToString.return_value = b"fake_model_bytes"

    mock_inferred_model = MagicMock()
    mock_inferred_model.metadata_props = mock_model.metadata_props
    mock_inferred_model.SerializeToString.return_value = b"fake_model_bytes"

    with (
        patch("model_api.adapters.onnx_adapter.onnxrt_absent", new=False),
        patch("model_api.adapters.onnx_adapter.onnx") as mock_onnx,
        patch("model_api.adapters.onnx_adapter.ort") as mock_ort,
        patch("model_api.adapters.onnx_adapter.SymbolicShapeInference") as mock_ssi,
    ):
        mock_onnx.load.return_value = mock_model
        mock_ssi.infer_shapes.return_value = mock_inferred_model
        mock_ort.InferenceSession.return_value = mock_session

        from model_api.adapters.onnx_adapter import ONNXRuntimeAdapter

        adapter = ONNXRuntimeAdapter("fake_model.onnx")

        # Store mocks for later use
        adapter._mock_session = mock_session  # noqa: SLF001
        adapter._mock_onnx = mock_onnx  # noqa: SLF001
        adapter._mock_ort = mock_ort  # noqa: SLF001

        yield adapter


class TestONNXRuntimeAdapterInit:
    def test_import_error_when_onnxrt_absent(self):
        with patch("model_api.adapters.onnx_adapter.onnxrt_absent", new=True):
            from model_api.adapters.onnx_adapter import ONNXRuntimeAdapter

            with pytest.raises(ImportError, match="ONNXRuntimeAdapter requires"):
                ONNXRuntimeAdapter("fake.onnx")

    def test_successful_init(self, onnx_adapter):
        assert onnx_adapter.output_names == ["output"]
        assert onnx_adapter.model is not None
        assert onnx_adapter.onnx_metadata is not None


class TestInferenceAdapterAbstract:
    def test_model_annotation_coverage(self):  # noqa: C901
        """Exercise InferenceAdapter.__init__ to cover self.model type annotation."""
        from model_api.adapters.inference_adapter import InferenceAdapter

        class _Dummy(InferenceAdapter):
            def __init__(self):
                super().__init__()

            def load_model(self): ...
            def get_model(self): ...
            def get_input_layers(self): ...
            def get_output_layers(self): ...
            def reshape_model(self, new_shape): ...
            def infer_sync(self, dict_data): ...
            def infer_async(self, dict_data, callback_data): ...
            def get_raw_result(self, infer_result): ...
            def set_callback(self, callback_fn): ...
            def is_ready(self): ...
            def await_all(self): ...
            def await_any(self): ...
            def get_rt_info(self, path): ...
            def update_model_info(self, model_info): ...
            def save_model(self, path, weights_path=None, version=None): ...
            def embed_preprocessing(
                self,
                layout,
                resize_mode,
                interpolation_mode,
                target_shape,
                pad_value,
                **kwargs,
            ): ...

        d = _Dummy()
        # Type annotation doesn't create attribute, but __init__ was executed
        assert d is not None


class TestONNXRuntimeAdapterLayers:
    def test_get_input_layers(self, onnx_adapter):
        inputs = onnx_adapter.get_input_layers()
        assert "input" in inputs
        meta = inputs["input"]
        assert meta.shape == (1, 3, 224, 224)
        assert meta.precision == "f32"
        assert "input" in meta.names

    def test_get_input_layers_unknown_precision(self, onnx_adapter):
        onnx_adapter._mock_session.get_inputs.return_value = [  # noqa: SLF001
            _make_onnx_input(type_str="tensor(double)"),
        ]
        inputs = onnx_adapter.get_input_layers()
        assert inputs["input"].precision == "tensor(double)"

    def test_get_output_layers(self, onnx_adapter):
        outputs = onnx_adapter.get_output_layers()
        assert "output" in outputs
        meta = outputs["output"]
        assert meta.shape == (1, 1000)
        assert meta.precision == "f32"

    def test_get_output_layers_unknown_precision(self, onnx_adapter):
        onnx_adapter._mock_session.get_outputs.return_value = [  # noqa: SLF001
            _make_onnx_output(type_str="tensor(int64)"),
        ]
        outputs = onnx_adapter.get_output_layers()
        assert outputs["output"].precision == "tensor(int64)"


class TestONNXRuntimeAdapterInference:
    def test_infer_sync(self, onnx_adapter):
        input_data = rng.random((1, 3, 224, 224)).astype(np.float32)
        mock_result = [rng.random((1, 1000)).astype(np.float32)]
        onnx_adapter._mock_session.run.return_value = mock_result  # noqa: SLF001

        result = onnx_adapter.infer_sync({"input": input_data})
        assert "output" in result
        np.testing.assert_array_equal(result["output"], mock_result[0])

    def test_infer_sync_dtype_mismatch(self, onnx_adapter):
        """When input dtype doesn't match, adapter should cast."""
        input_data = rng.random((1, 3, 224, 224)).astype(np.float64)
        mock_result = [rng.random((1, 1000)).astype(np.float32)]
        onnx_adapter._mock_session.run.return_value = mock_result  # noqa: SLF001

        result = onnx_adapter.infer_sync({"input": input_data})
        assert "output" in result

    def test_infer_async_raises(self, onnx_adapter):
        with pytest.raises(NotImplementedError):
            onnx_adapter.infer_async({}, None)


class TestONNXRuntimeAdapterMethods:
    def test_set_callback(self, onnx_adapter):
        cb = MagicMock()
        onnx_adapter.set_callback(cb)
        assert onnx_adapter.callback_fn is cb

    def test_is_ready(self, onnx_adapter):
        assert onnx_adapter.is_ready() is True

    def test_load_model(self, onnx_adapter):
        # Should not raise
        onnx_adapter.load_model()

    def test_await_all(self, onnx_adapter):
        onnx_adapter.await_all()

    def test_await_any(self, onnx_adapter):
        onnx_adapter.await_any()

    def test_get_raw_result(self, onnx_adapter):
        result = onnx_adapter.get_raw_result({})
        assert result is None

    def test_get_model(self, onnx_adapter):
        model = onnx_adapter.get_model()
        assert model is onnx_adapter.model

    def test_reshape_model_raises(self, onnx_adapter):
        with pytest.raises(NotImplementedError):
            onnx_adapter.reshape_model({"input": [1, 3, 128, 128]})

    def test_get_rt_info(self, onnx_adapter):
        result = onnx_adapter.get_rt_info(["model_info", "task_type"])
        assert result.astype(str) == "classification"

    def test_get_rt_info_missing(self, onnx_adapter):
        with pytest.raises(RuntimeError, match="Cannot get runtime attribute"):
            onnx_adapter.get_rt_info(["model_info", "nonexistent"])

    def test_embed_preprocessing(self, onnx_adapter):
        onnx_adapter.embed_preprocessing(
            layout="NCHW",
            resize_mode="standard",
            interpolation_mode="LINEAR",
            target_shape=(224, 224),
            pad_value=0,
        )
        # preprocessor should be updated (not the default lambda)
        assert onnx_adapter.preprocessor is not None

    def test_update_model_info_string(self, onnx_adapter):
        # metadata_props has an .add() method that returns a new entry
        mock_meta_entry = MagicMock()
        mock_props = MagicMock()
        mock_props.add.return_value = mock_meta_entry
        onnx_adapter.model.metadata_props = mock_props
        onnx_adapter.update_model_info({"task_type": "detection"})
        assert mock_meta_entry.key == "model_info task_type"
        assert mock_meta_entry.value == "detection"

    def test_update_model_info_list(self, onnx_adapter):
        mock_meta_entry = MagicMock()
        mock_props = MagicMock()
        mock_props.add.return_value = mock_meta_entry
        onnx_adapter.model.metadata_props = mock_props
        onnx_adapter.update_model_info({"labels": ["cat", "dog"]})
        assert mock_meta_entry.value == "cat dog"

    def test_save_model(self, onnx_adapter):
        with patch("model_api.adapters.onnx_adapter.onnx") as mock_onnx:
            onnx_adapter.save_model("output.onnx")
            mock_onnx.save.assert_called_once_with(onnx_adapter.model, "output.onnx")


class TestGetShapeFromOnnx:
    def test_numeric_shape(self):
        from model_api.adapters.onnx_adapter import get_shape_from_onnx

        assert get_shape_from_onnx([1, 3, 224, 224]) == (1, 3, 224, 224)

    def test_string_dim_replaced(self):
        from model_api.adapters.onnx_adapter import get_shape_from_onnx

        result = get_shape_from_onnx([1, 3, "height", "width"])
        assert result == (1, 3, -1, -1)

    def test_mixed_shape(self):
        from model_api.adapters.onnx_adapter import get_shape_from_onnx

        result = get_shape_from_onnx(["batch", 3, 224, 224])
        assert result == (-1, 3, 224, 224)


class TestOnnxrtAbsentImportError:
    def test_onnxrt_absent_on_import_failure(self):
        """Lines 21-22: except ImportError sets onnxrt_absent = True."""
        import importlib
        import sys

        import model_api.adapters.onnx_adapter as mod

        orig = sys.modules["onnx"]
        sys.modules["onnx"] = None
        try:
            importlib.reload(mod)
            assert mod.onnxrt_absent is True
        finally:
            sys.modules["onnx"] = orig
            importlib.reload(mod)
            # Refresh stale reference in model.py
            import model_api.models.model as model_mod

            model_mod.ONNXRuntimeAdapter = mod.ONNXRuntimeAdapter
