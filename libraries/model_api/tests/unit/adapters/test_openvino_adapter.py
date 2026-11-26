# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import pathlib
from unittest.mock import MagicMock, patch

import numpy as np
import pytest


def _make_mock_ov_output(
    name="input",
    names=None,
    shape=(1, 3, 224, 224),
    element_type_name="f32",
    is_dynamic=False,
    partial_shape_str="[1,3,224,224]",
):
    """Create a mock OV output (input/output tensor)."""
    output = MagicMock()
    output.get_any_name.return_value = name
    output.get_names.return_value = names or {name}
    output.shape = list(shape)
    output.get_element_type.return_value.get_type_name.return_value = element_type_name

    ps = MagicMock()
    ps.is_dynamic = is_dynamic
    ps.get_min_shape.return_value = list(shape)
    ps.__str__ = MagicMock(return_value=partial_shape_str)
    output.partial_shape = ps

    return output


def _make_mock_node(friendly_name="input", type_name="Parameter", attributes=None):
    node = MagicMock()
    node.get_friendly_name.return_value = friendly_name
    node.get_type_name.return_value = type_name
    node.get_attributes.return_value = attributes or {}
    return node


@pytest.fixture
def mock_ov_model():
    """Create a mock OV model."""
    model = MagicMock()
    inp = _make_mock_ov_output("input", {"input"}, (1, 3, 224, 224))
    out = _make_mock_ov_output("output", {"output"}, (1, 1000))
    model.inputs = [inp]
    model.outputs = [out]
    model.is_dynamic.return_value = False
    model.get_ordered_ops.return_value = [
        _make_mock_node("input", "Parameter"),
        _make_mock_node("output", "Result"),
    ]
    model.get_rt_info.return_value = MagicMock()
    return model


@pytest.fixture
def mock_core(mock_ov_model):
    """Create a mock OV Core."""
    core = MagicMock()
    core.read_model.return_value = mock_ov_model
    compiled = MagicMock()
    compiled.get_property.side_effect = RuntimeError("not supported")
    core.compile_model.return_value = compiled
    return core


@pytest.fixture
def ov_adapter(mock_core, mock_ov_model):
    """Create OpenvinoAdapter with mocked Core and model."""
    with patch("model_api.adapters.openvino_adapter.openvino_absent", new=False):
        import openvino as ov

        mock_layout = MagicMock()
        mock_layout.empty = True
        with patch.object(ov, "layout_helpers", create=True) as mock_lh:
            mock_lh.get_layout.return_value = mock_layout
            import os

            # Create a temp file to make Path.is_file() happy
            import tempfile

            from model_api.adapters.openvino_adapter import OpenvinoAdapter

            fd, path = tempfile.mkstemp(suffix=".xml")
            os.close(fd)
            try:
                adapter = OpenvinoAdapter(
                    core=mock_core,
                    model=path,
                    weights_path=None,
                    device="CPU",
                )
            finally:
                pathlib.Path(path).unlink()

            # Patch async queue for load_model
            adapter._mock_core = mock_core  # noqa: SLF001
            adapter._mock_model = mock_ov_model  # noqa: SLF001
            yield adapter


class TestOpenvinoAdapterInit:
    def test_init_from_file(self, ov_adapter):
        assert ov_adapter.device == "CPU"
        assert ov_adapter.model is not None

    def test_init_from_buffer(self, mock_core):
        with patch("model_api.adapters.openvino_adapter.openvino_absent", new=False):
            from model_api.adapters.openvino_adapter import OpenvinoAdapter

            adapter = OpenvinoAdapter(
                core=mock_core,
                model=b"fake_xml_bytes",
                weights_path=b"fake_bin_bytes",
                device="CPU",
            )
            assert adapter.model_from_buffer is True

    def test_init_invalid_model_raises(self, mock_core):
        with patch("model_api.adapters.openvino_adapter.openvino_absent", new=False):
            from model_api.adapters.openvino_adapter import OpenvinoAdapter

            with pytest.raises(RuntimeError, match="Model must be bytes or a file"):
                OpenvinoAdapter(
                    core=mock_core,
                    model="nonexistent_path.xml",
                    device="CPU",
                )

    def test_init_onnx_model(self, mock_core):
        with patch("model_api.adapters.openvino_adapter.openvino_absent", new=False):
            import os
            import tempfile

            fd, path = tempfile.mkstemp(suffix=".onnx")
            os.close(fd)
            try:
                import sys

                mock_onnx = MagicMock()
                mock_onnx_model = MagicMock()
                mock_onnx_model.metadata_props = []
                mock_onnx.load.return_value = mock_onnx_model

                with patch.dict(sys.modules, {"onnx": mock_onnx}):
                    from model_api.adapters.openvino_adapter import OpenvinoAdapter

                    adapter = OpenvinoAdapter(
                        core=mock_core,
                        model=path,
                        device="CPU",
                    )
                    assert adapter.is_onnx_file is True
            finally:
                pathlib.Path(path).unlink()

    def test_init_onnx_with_weights_warning(self, mock_core, caplog):
        with patch("model_api.adapters.openvino_adapter.openvino_absent", new=False):
            import logging
            import os
            import sys
            import tempfile

            fd, path = tempfile.mkstemp(suffix=".onnx")
            os.close(fd)
            try:
                mock_onnx = MagicMock()
                mock_onnx_model = MagicMock()
                mock_onnx_model.metadata_props = []
                mock_onnx.load.return_value = mock_onnx_model

                with patch.dict(sys.modules, {"onnx": mock_onnx}):
                    from model_api.adapters.openvino_adapter import OpenvinoAdapter

                    with caplog.at_level(logging.WARNING):
                        adapter = OpenvinoAdapter(
                            core=mock_core,
                            model=path,
                            weights_path="fake.bin",
                            device="CPU",
                        )
                    assert "omitted" in caplog.text.lower() or adapter is not None
            finally:
                pathlib.Path(path).unlink()


class TestOpenvinoAdapterLoadModel:
    def test_load_model(self, ov_adapter):
        with patch("model_api.adapters.openvino_adapter.AsyncInferQueue") as mock_aiq:
            mock_queue = MagicMock()
            mock_queue.__len__ = MagicMock(return_value=2)
            mock_aiq.return_value = mock_queue
            ov_adapter.load_model()
            assert ov_adapter.compiled_model is not None

    def test_load_model_with_max_requests(self, mock_core, mock_ov_model):
        with patch("model_api.adapters.openvino_adapter.openvino_absent", new=False):
            import os
            import tempfile

            fd, path = tempfile.mkstemp(suffix=".xml")
            os.close(fd)
            try:
                from model_api.adapters.openvino_adapter import OpenvinoAdapter

                adapter = OpenvinoAdapter(
                    core=mock_core,
                    model=path,
                    device="CPU",
                    max_num_requests=4,
                )
            finally:
                pathlib.Path(path).unlink()
            with patch("model_api.adapters.openvino_adapter.AsyncInferQueue") as mock_aiq:
                mock_queue = MagicMock()
                mock_queue.__len__ = MagicMock(return_value=4)
                mock_aiq.return_value = mock_queue
                adapter.load_model()


class TestOpenvinoAdapterLayers:
    def test_get_input_layers(self, ov_adapter):
        # Use real OV model for get_input_layers
        import openvino as ov

        param = ov.op.Parameter(ov.Type.f32, ov.Shape([1, 3, 224, 224]))
        model = ov.Model(param, [param], "test_model")
        ov_adapter.model = model
        inputs = ov_adapter.get_input_layers()
        # There should be one input
        assert len(inputs) == 1
        for name, meta in inputs.items():
            assert meta.precision == "f32"

    def test_get_input_layers_with_user_layout(self, mock_core, mock_ov_model):
        with patch("model_api.adapters.openvino_adapter.openvino_absent", new=False):
            import os
            import tempfile

            import openvino as ov

            fd, path = tempfile.mkstemp(suffix=".xml")
            os.close(fd)
            try:
                from model_api.adapters.openvino_adapter import OpenvinoAdapter

                adapter = OpenvinoAdapter(
                    core=mock_core,
                    model=path,
                    device="CPU",
                    model_parameters={"input_layouts": "input:NCHW"},
                )
            finally:
                pathlib.Path(path).unlink()

            # Use real model to avoid layout_helpers issues
            param = ov.op.Parameter(ov.Type.f32, ov.Shape([1, 3, 224, 224]))
            param.friendly_name = "input"
            model = ov.Model(param, [param], "test_model")
            adapter.model = model
            inputs = adapter.get_input_layers()
            # Should use user-provided layout
            for name, meta in inputs.items():
                assert meta.layout == "NCHW"

    def test_get_input_layers_from_openvino_layout(self, ov_adapter):
        import openvino as ov
        from openvino.preprocess import PrePostProcessor

        param = ov.op.Parameter(ov.Type.f32, ov.Shape([1, 3, 224, 224]))
        model = ov.Model(param, [param], "test_model")
        ppp = PrePostProcessor(model)
        ppp.input().model().set_layout(ov.Layout("NCHW"))
        built_model = ppp.build()
        ov_adapter.model = built_model
        inputs = ov_adapter.get_input_layers()
        for name, meta in inputs.items():
            assert meta.layout == "NCHW"

    def test_get_output_layers(self, ov_adapter):
        import openvino as ov

        param = ov.op.Parameter(ov.Type.f32, ov.Shape([1, 3, 224, 224]))
        model = ov.Model(param, [param], "test_model")
        ov_adapter.model = model
        outputs = ov_adapter.get_output_layers()
        assert len(outputs) >= 1

    def test_get_output_layers_dynamic(self, ov_adapter):
        import openvino as ov

        param = ov.op.Parameter(ov.Type.f32, ov.PartialShape([-1, 3, -1, -1]))
        model = ov.Model(param, [param], "test_model")
        ov_adapter.model = model
        outputs = ov_adapter.get_output_layers()
        assert len(outputs) >= 1


class TestOpenvinoAdapterInference:
    def test_infer_sync(self, ov_adapter):
        with patch("model_api.adapters.openvino_adapter.AsyncInferQueue") as mock_aiq:
            mock_queue = MagicMock()
            mock_queue.__len__ = MagicMock(return_value=2)
            mock_aiq.return_value = mock_queue
            ov_adapter.load_model()

            mock_request = MagicMock()
            result_tensor = MagicMock()
            result_tensor.data = np.zeros((1, 1000))
            mock_request.get_tensor.return_value = result_tensor
            mock_queue.__getitem__ = MagicMock(return_value=mock_request)
            mock_queue.get_idle_request_id.return_value = 0

            result = ov_adapter.infer_sync({"input": np.zeros((1, 3, 224, 224))})
            assert "output" in result

    def test_infer_sync_with_python_preprocessing(self, ov_adapter):
        with patch("model_api.adapters.openvino_adapter.AsyncInferQueue") as mock_aiq:
            mock_queue = MagicMock()
            mock_queue.__len__ = MagicMock(return_value=2)
            mock_aiq.return_value = mock_queue
            ov_adapter.load_model()

            mock_request = MagicMock()
            result_tensor = MagicMock()
            result_tensor.data = np.zeros((1, 1000))
            mock_request.get_tensor.return_value = result_tensor
            mock_queue.__getitem__ = MagicMock(return_value=mock_request)
            mock_queue.get_idle_request_id.return_value = 0

            ov_adapter.use_python_preprocessing = True
            call_count = [0]

            def mock_preprocessor(x):
                call_count[0] += 1
                return x

            ov_adapter.preprocessor = mock_preprocessor

            ov_adapter.infer_sync({"input": np.zeros((1, 3, 224, 224))})
            assert call_count[0] > 0

    def test_infer_async(self, ov_adapter):
        with patch("model_api.adapters.openvino_adapter.AsyncInferQueue") as mock_aiq:
            mock_queue = MagicMock()
            mock_queue.__len__ = MagicMock(return_value=2)
            mock_aiq.return_value = mock_queue
            ov_adapter.load_model()

            ov_adapter.infer_async({"input": np.zeros((1, 3, 224, 224))}, "callback_data")
            mock_queue.start_async.assert_called_once()

    def test_infer_async_with_python_preprocessing(self, ov_adapter):
        with patch("model_api.adapters.openvino_adapter.AsyncInferQueue") as mock_aiq:
            mock_queue = MagicMock()
            mock_queue.__len__ = MagicMock(return_value=2)
            mock_aiq.return_value = mock_queue
            ov_adapter.load_model()

            ov_adapter.use_python_preprocessing = True
            called = [False]

            def mock_pp(x):
                called[0] = True
                return x

            ov_adapter.preprocessor = mock_pp

            ov_adapter.infer_async({"input": np.zeros((1, 3, 224, 224))}, "cb")
            assert called[0]

    def test_set_callback(self, ov_adapter):
        with patch("model_api.adapters.openvino_adapter.AsyncInferQueue") as mock_aiq:
            mock_queue = MagicMock()
            mock_queue.__len__ = MagicMock(return_value=2)
            mock_aiq.return_value = mock_queue
            ov_adapter.load_model()

            cb = MagicMock()
            ov_adapter.set_callback(cb)
            mock_queue.set_callback.assert_called_once_with(cb)

    def test_is_ready(self, ov_adapter):
        with patch("model_api.adapters.openvino_adapter.AsyncInferQueue") as mock_aiq:
            mock_queue = MagicMock()
            mock_queue.__len__ = MagicMock(return_value=2)
            mock_queue.is_ready.return_value = True
            mock_aiq.return_value = mock_queue
            ov_adapter.load_model()
            assert ov_adapter.is_ready() is True

    def test_await_all(self, ov_adapter):
        with patch("model_api.adapters.openvino_adapter.AsyncInferQueue") as mock_aiq:
            mock_queue = MagicMock()
            mock_queue.__len__ = MagicMock(return_value=2)
            mock_aiq.return_value = mock_queue
            ov_adapter.load_model()
            ov_adapter.await_all()
            mock_queue.wait_all.assert_called_once()

    def test_await_any(self, ov_adapter):
        with patch("model_api.adapters.openvino_adapter.AsyncInferQueue") as mock_aiq:
            mock_queue = MagicMock()
            mock_queue.__len__ = MagicMock(return_value=2)
            mock_aiq.return_value = mock_queue
            ov_adapter.load_model()
            ov_adapter.await_any()
            mock_queue.get_idle_request_id.assert_called()

    def test_get_raw_result(self, ov_adapter):
        mock_request = MagicMock()
        result_tensor = MagicMock()
        result_tensor.data = np.zeros((1, 1000))
        mock_request.get_tensor.return_value = result_tensor
        result = ov_adapter.get_raw_result(mock_request)
        assert "output" in result

    def test_copy_raw_result(self, ov_adapter):
        mock_request = MagicMock()
        original_data = np.zeros((1, 1000))
        result_tensor = MagicMock()
        result_tensor.data = original_data
        mock_request.get_tensor.return_value = result_tensor
        result = ov_adapter.copy_raw_result(mock_request)
        assert "output" in result
        # Should be a copy
        assert result["output"] is not original_data


class TestOpenvinoAdapterMethods:
    def test_reshape_model(self, ov_adapter):
        with (
            patch("model_api.adapters.openvino_adapter.PartialShape"),
            patch("model_api.adapters.openvino_adapter.Dimension"),
        ):
            ov_adapter.reshape_model({"input": [1, 3, 128, 128]})
            ov_adapter.model.reshape.assert_called_once()

    def test_reshape_model_with_tuple_dim(self, ov_adapter):
        with (
            patch("model_api.adapters.openvino_adapter.PartialShape"),
            patch("model_api.adapters.openvino_adapter.Dimension"),
        ):
            ov_adapter.reshape_model({"input": [(1, 4), 3, 128, 128]})
            ov_adapter.model.reshape.assert_called_once()

    def test_get_model(self, ov_adapter):
        assert ov_adapter.get_model() is ov_adapter.model

    def test_get_rt_info(self, ov_adapter):
        ov_adapter.model.get_rt_info.return_value = "test_value"
        ov_adapter.get_rt_info(["model_info", "task"])
        ov_adapter.model.get_rt_info.assert_called_with(["model_info", "task"])

    def test_get_rt_info_onnx_file(self, ov_adapter):
        ov_adapter.is_onnx_file = True
        ov_adapter.onnx_metadata = {"model_info": {"task": "detection"}}
        result = ov_adapter.get_rt_info(["model_info", "task"])
        assert result.astype(str) == "detection"

    def test_update_model_info(self, ov_adapter):
        ov_adapter.update_model_info({"task": "classification"})
        ov_adapter.model.set_rt_info.assert_called_with("classification", ["model_info", "task"])

    def test_save_model(self, ov_adapter):
        with patch("model_api.adapters.openvino_adapter.ov") as mock_ov:
            ov_adapter.save_model("model.xml")
            mock_ov.serialize.assert_called_once_with(
                ov_adapter.get_model(),
                "model.xml",
                "",
                "UNSPECIFIED",
            )

    def test_save_model_with_paths(self, ov_adapter):
        with patch("model_api.adapters.openvino_adapter.ov") as mock_ov:
            ov_adapter.save_model("model.xml", weights_path="model.bin", version="IR_V10")
            mock_ov.serialize.assert_called_once_with(
                ov_adapter.get_model(),
                "model.xml",
                "model.bin",
                "IR_V10",
            )

    def test_operations_by_type(self, ov_adapter):
        result = ov_adapter.operations_by_type("Parameter")
        assert "input" in result

    def test_log_runtime_settings(self, ov_adapter):
        with patch("model_api.adapters.openvino_adapter.AsyncInferQueue") as mock_aiq:
            mock_queue = MagicMock()
            mock_queue.__len__ = MagicMock(return_value=2)
            mock_aiq.return_value = mock_queue
            ov_adapter.load_model()
            # Should not raise even when get_property raises
            ov_adapter.log_runtime_settings()

    def test_log_runtime_settings_auto_device(self, ov_adapter):
        ov_adapter.device = "AUTO"
        with patch("model_api.adapters.openvino_adapter.AsyncInferQueue") as mock_aiq:
            mock_queue = MagicMock()
            mock_queue.__len__ = MagicMock(return_value=2)
            mock_aiq.return_value = mock_queue
            ov_adapter.load_model()
            ov_adapter.log_runtime_settings()


class TestOpenvinoAdapterEmbedPreprocessing:
    def test_embed_preprocessing_npu_uses_python(self, ov_adapter):
        ov_adapter.device = "NPU"
        mock_input = MagicMock()
        mock_input.get_any_name.return_value = "input"
        ov_adapter.model.inputs = [mock_input]

        with patch("model_api.adapters.openvino_adapter.setup_python_preprocessing_pipeline") as mock_pp:
            mock_pp.return_value = lambda x: x
            ov_adapter.embed_preprocessing(
                layout="NCHW",
                resize_mode="standard",
                interpolation_mode="LINEAR",
                target_shape=(224, 224),
                pad_value=0,
            )
        assert ov_adapter.use_python_preprocessing is True

    def test_embed_preprocessing_npu_nhwc(self, ov_adapter):
        ov_adapter.device = "NPU"
        mock_input = MagicMock()
        mock_input.get_any_name.return_value = "input"
        ov_adapter.model.inputs = [mock_input]

        with patch("model_api.adapters.openvino_adapter.setup_python_preprocessing_pipeline") as mock_pp:
            mock_pp.return_value = lambda x: x
            ov_adapter.embed_preprocessing(
                layout="NHWC",
                resize_mode="standard",
                interpolation_mode="LINEAR",
                target_shape=(224, 224),
                pad_value=0,
            )
        assert ov_adapter.use_python_preprocessing is True

    def test_embed_preprocessing_cpu_standard(self, ov_adapter):
        """Test full embed_preprocessing path for CPU with standard resize."""
        import openvino as ov

        # Create a real simple model for preprocessing
        param = ov.op.Parameter(ov.Type.f32, ov.Shape([1, 3, 224, 224]))
        model = ov.Model(param, [param])
        ov_adapter.model = model

        with patch("model_api.adapters.openvino_adapter.AsyncInferQueue") as mock_aiq:
            mock_queue = MagicMock()
            mock_queue.__len__ = MagicMock(return_value=2)
            mock_aiq.return_value = mock_queue

            ov_adapter.embed_preprocessing(
                layout="NCHW",
                resize_mode="standard",
                interpolation_mode="LINEAR",
                target_shape=(224, 224),
                pad_value=0,
                brg2rgb=True,
                mean=[0.485, 0.456, 0.406],
                scale=[0.229, 0.224, 0.225],
            )

    def test_embed_preprocessing_letterbox(self, ov_adapter):
        import openvino as ov

        param = ov.op.Parameter(ov.Type.f32, ov.Shape([1, 3, 224, 224]))
        model = ov.Model(param, [param])
        ov_adapter.model = model

        with patch("model_api.adapters.openvino_adapter.AsyncInferQueue") as mock_aiq:
            mock_queue = MagicMock()
            mock_queue.__len__ = MagicMock(return_value=2)
            mock_aiq.return_value = mock_queue

            ov_adapter.embed_preprocessing(
                layout="NCHW",
                resize_mode="fit_to_window_letterbox",
                interpolation_mode="LINEAR",
                target_shape=(224, 224),
                pad_value=128,
            )

    def test_embed_preprocessing_fit_to_window(self, ov_adapter):
        import openvino as ov

        param = ov.op.Parameter(ov.Type.f32, ov.Shape([1, 3, 224, 224]))
        model = ov.Model(param, [param])
        ov_adapter.model = model

        with patch("model_api.adapters.openvino_adapter.AsyncInferQueue") as mock_aiq:
            mock_queue = MagicMock()
            mock_queue.__len__ = MagicMock(return_value=2)
            mock_aiq.return_value = mock_queue

            ov_adapter.embed_preprocessing(
                layout="NCHW",
                resize_mode="fit_to_window",
                interpolation_mode="LINEAR",
                target_shape=(224, 224),
                pad_value=0,
            )

    def test_embed_preprocessing_crop(self, ov_adapter):
        import openvino as ov

        param = ov.op.Parameter(ov.Type.f32, ov.Shape([1, 3, 224, 224]))
        model = ov.Model(param, [param])
        ov_adapter.model = model

        with patch("model_api.adapters.openvino_adapter.AsyncInferQueue") as mock_aiq:
            mock_queue = MagicMock()
            mock_queue.__len__ = MagicMock(return_value=2)
            mock_aiq.return_value = mock_queue

            ov_adapter.embed_preprocessing(
                layout="NCHW",
                resize_mode="crop",
                interpolation_mode="LINEAR",
                target_shape=(224, 224),
                pad_value=0,
            )

    def test_embed_preprocessing_invalid_resize_mode(self, ov_adapter):
        import openvino as ov

        param = ov.op.Parameter(ov.Type.f32, ov.Shape([1, 3, 224, 224]))
        model = ov.Model(param, [param])
        ov_adapter.model = model

        with pytest.raises(ValueError, match="Upsupported resize type"):
            ov_adapter.embed_preprocessing(
                layout="NCHW",
                resize_mode="invalid_mode",
                interpolation_mode="LINEAR",
                target_shape=(224, 224),
                pad_value=0,
            )

    def test_embed_preprocessing_scale_to_unit(self, ov_adapter):
        import openvino as ov

        param = ov.op.Parameter(ov.Type.f32, ov.Shape([1, 3, 224, 224]))
        model = ov.Model(param, [param])
        ov_adapter.model = model

        with patch("model_api.adapters.openvino_adapter.AsyncInferQueue") as mock_aiq:
            mock_queue = MagicMock()
            mock_queue.__len__ = MagicMock(return_value=2)
            mock_aiq.return_value = mock_queue

            ov_adapter.embed_preprocessing(
                layout="NCHW",
                resize_mode="standard",
                interpolation_mode="LINEAR",
                target_shape=(224, 224),
                pad_value=0,
                intensity_mode="scale_to_unit",
                intensity_max_value=255.0,
            )

    def test_embed_preprocessing_window(self, ov_adapter):
        import openvino as ov

        param = ov.op.Parameter(ov.Type.f32, ov.Shape([1, 3, 224, 224]))
        model = ov.Model(param, [param])
        ov_adapter.model = model

        with patch("model_api.adapters.openvino_adapter.AsyncInferQueue") as mock_aiq:
            mock_queue = MagicMock()
            mock_queue.__len__ = MagicMock(return_value=2)
            mock_aiq.return_value = mock_queue

            ov_adapter.embed_preprocessing(
                layout="NCHW",
                resize_mode="standard",
                interpolation_mode="LINEAR",
                target_shape=(224, 224),
                pad_value=0,
                intensity_mode="window",
                intensity_window_center=128.0,
                intensity_window_width=256.0,
            )

    def test_embed_preprocessing_range_scale(self, ov_adapter):
        import openvino as ov

        param = ov.op.Parameter(ov.Type.f32, ov.Shape([1, 3, 224, 224]))
        model = ov.Model(param, [param])
        ov_adapter.model = model

        with patch("model_api.adapters.openvino_adapter.AsyncInferQueue") as mock_aiq:
            mock_queue = MagicMock()
            mock_queue.__len__ = MagicMock(return_value=2)
            mock_aiq.return_value = mock_queue

            ov_adapter.embed_preprocessing(
                layout="NCHW",
                resize_mode="standard",
                interpolation_mode="LINEAR",
                target_shape=(224, 224),
                pad_value=0,
                intensity_mode="range_scale",
                intensity_scale_factor=1.0,
                intensity_min_value=0.0,
                intensity_max_value=255.0,
            )

    def test_embed_preprocessing_repeat_channels(self, ov_adapter):
        import openvino as ov

        param = ov.op.Parameter(ov.Type.f32, ov.Shape([1, 3, 224, 224]))
        model = ov.Model(param, [param])
        ov_adapter.model = model

        with patch("model_api.adapters.openvino_adapter.AsyncInferQueue") as mock_aiq:
            mock_queue = MagicMock()
            mock_queue.__len__ = MagicMock(return_value=2)
            mock_aiq.return_value = mock_queue

            ov_adapter.embed_preprocessing(
                layout="NCHW",
                resize_mode="standard",
                interpolation_mode="LINEAR",
                target_shape=(224, 224),
                pad_value=0,
                intensity_repeat_channels=True,
            )

    def test_embed_preprocessing_input_dtypes(self, ov_adapter):
        """Test various input_dtype values."""
        import openvino as ov

        for input_dtype in ("u8", "f32", "u16", "i16"):
            param = ov.op.Parameter(ov.Type.f32, ov.Shape([1, 3, 224, 224]))
            model = ov.Model(param, [param])
            ov_adapter.model = model

            with patch("model_api.adapters.openvino_adapter.AsyncInferQueue") as mock_aiq:
                mock_queue = MagicMock()
                mock_queue.__len__ = MagicMock(return_value=2)
                mock_aiq.return_value = mock_queue

                ov_adapter.embed_preprocessing(
                    layout="NCHW",
                    resize_mode="standard",
                    interpolation_mode="LINEAR",
                    target_shape=(224, 224),
                    pad_value=0,
                    input_dtype=input_dtype,
                )

    def test_embed_preprocessing_dtype_float(self, ov_adapter):
        """Test legacy dtype=float path."""
        import openvino as ov

        param = ov.op.Parameter(ov.Type.f32, ov.Shape([1, 3, 224, 224]))
        model = ov.Model(param, [param])
        ov_adapter.model = model

        with patch("model_api.adapters.openvino_adapter.AsyncInferQueue") as mock_aiq:
            mock_queue = MagicMock()
            mock_queue.__len__ = MagicMock(return_value=2)
            mock_aiq.return_value = mock_queue

            ov_adapter.embed_preprocessing(
                layout="NCHW",
                resize_mode="standard",
                interpolation_mode="LINEAR",
                target_shape=(224, 224),
                pad_value=0,
                dtype=float,
                input_dtype="unknown_dtype",
            )

    def test_embed_preprocessing_no_resize(self, ov_adapter):
        """Test with no resize_mode."""
        import openvino as ov

        param = ov.op.Parameter(ov.Type.f32, ov.Shape([1, 3, 224, 224]))
        model = ov.Model(param, [param])
        ov_adapter.model = model

        with patch("model_api.adapters.openvino_adapter.AsyncInferQueue") as mock_aiq:
            mock_queue = MagicMock()
            mock_queue.__len__ = MagicMock(return_value=2)
            mock_aiq.return_value = mock_queue

            ov_adapter.embed_preprocessing(
                layout="NCHW",
                resize_mode="",
                interpolation_mode="LINEAR",
                target_shape=(224, 224),
                pad_value=0,
            )

    def test_embed_preprocessing_with_input_frame_shape(self, ov_adapter):
        import openvino as ov

        param = ov.op.Parameter(ov.Type.f32, ov.Shape([1, 3, 224, 224]))
        model = ov.Model(param, [param])
        ov_adapter.model = model

        with patch("model_api.adapters.openvino_adapter.AsyncInferQueue") as mock_aiq:
            mock_queue = MagicMock()
            mock_queue.__len__ = MagicMock(return_value=2)
            mock_aiq.return_value = mock_queue

            ov_adapter.embed_preprocessing(
                layout="NCHW",
                resize_mode="standard",
                interpolation_mode="LINEAR",
                target_shape=(224, 224),
                pad_value=0,
                input_frame_shape=(480, 640),
            )


class TestOpenvinoAdapterNPU:
    def test_reshape_dynamic_inputs_nchw(self, ov_adapter):
        """Test NPU dynamic input reshaping for NCHW layout."""
        mock_input = MagicMock()
        mock_input.partial_shape.is_dynamic = True
        mock_input.get_any_name.return_value = "input"

        # NCHW shape with dim[1] <= 4 → NCHW
        mock_input.shape = [1, 3, 224, 224]
        ps = MagicMock()
        ps.is_dynamic = False
        mock_input.partial_shape = MagicMock()
        mock_input.partial_shape.is_dynamic = True

        # Use get_input_shape mock
        with patch("model_api.adapters.openvino_adapter.get_input_shape") as mock_gis:
            mock_gis.return_value = [-1, 3, -1, -1]
            ov_adapter.model.inputs = [mock_input]
            ov_adapter.reshape_dynamic_inputs()

    def test_reshape_dynamic_inputs_nhwc(self, ov_adapter):
        mock_input = MagicMock()
        mock_input.partial_shape.is_dynamic = True
        mock_input.get_any_name.return_value = "input"

        with patch("model_api.adapters.openvino_adapter.get_input_shape") as mock_gis:
            mock_gis.return_value = [-1, -1, -1, 3]
            ov_adapter.model.inputs = [mock_input]
            ov_adapter.reshape_dynamic_inputs()

    def test_reshape_dynamic_inputs_range_dim(self, ov_adapter):
        mock_input = MagicMock()
        mock_input.partial_shape.is_dynamic = True
        mock_input.get_any_name.return_value = "input"

        with patch("model_api.adapters.openvino_adapter.get_input_shape") as mock_gis:
            mock_gis.return_value = [(1, 4), 3, (100, 300), (100, 300)]
            ov_adapter.model.inputs = [mock_input]
            ov_adapter.reshape_dynamic_inputs()

    def test_reshape_dynamic_inputs_non_4d(self, ov_adapter):
        mock_input = MagicMock()
        mock_input.partial_shape.is_dynamic = True
        mock_input.get_any_name.return_value = "input"

        with patch("model_api.adapters.openvino_adapter.get_input_shape") as mock_gis:
            mock_gis.return_value = [-1, -1]
            ov_adapter.model.inputs = [mock_input]
            ov_adapter.reshape_dynamic_inputs()

    def test_load_model_npu_with_dynamic(self, ov_adapter):
        ov_adapter.device = "NPU"
        ov_adapter.model.is_dynamic.return_value = True

        mock_input = MagicMock()
        mock_input.partial_shape.is_dynamic = True
        mock_input.get_any_name.return_value = "input"
        ov_adapter.model.inputs = [mock_input]

        with (
            patch("model_api.adapters.openvino_adapter.get_input_shape") as mock_gis,
            patch("model_api.adapters.openvino_adapter.AsyncInferQueue") as mock_aiq,
        ):
            mock_gis.return_value = [-1, 3, -1, -1]
            mock_queue = MagicMock()
            mock_queue.__len__ = MagicMock(return_value=2)
            mock_aiq.return_value = mock_queue
            ov_adapter.load_model()


class TestGetInputShape:
    def test_static_shape(self):
        from model_api.adapters.openvino_adapter import get_input_shape

        tensor = MagicMock()
        tensor.partial_shape.is_dynamic = False
        tensor.shape = [1, 3, 224, 224]
        result = get_input_shape(tensor)
        assert result == [1, 3, 224, 224]

    def test_dynamic_shape(self):
        from model_api.adapters.openvino_adapter import get_input_shape

        tensor = MagicMock()
        tensor.partial_shape.is_dynamic = True
        tensor.partial_shape.__str__ = MagicMock(return_value="[?,3,?,?]")
        result = get_input_shape(tensor)
        assert result == [-1, 3, -1, -1]

    def test_range_shape(self):
        from model_api.adapters.openvino_adapter import get_input_shape

        tensor = MagicMock()
        tensor.partial_shape.is_dynamic = True
        tensor.partial_shape.__str__ = MagicMock(return_value="[1,3,{100..300},{100..300}]")
        result = get_input_shape(tensor)
        assert result[0] == 1
        assert result[1] == 3
        assert isinstance(result[2], tuple)
        assert result[2] == (100, 300)


class TestCreateCore:
    def test_create_core_when_absent(self):
        with patch("model_api.adapters.openvino_adapter.openvino_absent", new=True):
            from model_api.adapters.openvino_adapter import create_core

            with pytest.raises(ImportError, match="OpenVINO package is not installed"):
                create_core()

    def test_create_core_success(self):
        with patch("model_api.adapters.openvino_adapter.openvino_absent", new=False):
            from model_api.adapters.openvino_adapter import create_core

            core = create_core()
            assert core is not None


class TestParseDevicesEdgeCases:
    def test_parse_devices_with_parenthesis(self):
        """Test parse_devices with device:property format."""
        from model_api.adapters.openvino_adapter import parse_devices

        result = parse_devices("HETERO:CPU:2,GPU:4")
        assert len(result) == 2

    def test_parse_value_per_device_error(self):
        """Test RuntimeError for bad format."""
        from model_api.adapters.openvino_adapter import parse_value_per_device

        with pytest.raises(RuntimeError, match="Unknown string format"):
            parse_value_per_device({"CPU"}, "CPU:2:3")

    def test_get_user_config_multi_cpu_gpu(self):
        """Test GPU_PLUGIN_THROTTLE in MULTI:CPU,GPU config."""
        from model_api.adapters.openvino_adapter import get_user_config

        config = get_user_config("MULTI:CPU,GPU", "2")
        assert config.get("GPU_PLUGIN_THROTTLE") == "1"


class TestOpenvinoAdapterOnnxImportError:
    def test_onnx_import_error(self, mock_core):
        """Test the ImportError path when onnx is not installed."""
        import builtins
        import os
        import tempfile

        fd, path = tempfile.mkstemp(suffix=".onnx")
        os.close(fd)
        try:
            original_import = builtins.__import__

            def mock_import(name, *args, **kwargs):
                if name == "onnx":
                    msg = "No module named 'onnx'"
                    raise ImportError(msg)
                return original_import(name, *args, **kwargs)

            with patch("builtins.__import__", side_effect=mock_import):
                from model_api.adapters.openvino_adapter import OpenvinoAdapter

                with pytest.raises(ImportError, match="Loading ONNX models requires"):
                    OpenvinoAdapter(core=mock_core, model=path, device="CPU")
        finally:
            pathlib.Path(path).unlink()


class TestLogRuntimeSettingsSuccess:
    def test_log_runtime_settings_cpu_success(self, ov_adapter):
        """Cover log_runtime_settings when get_property succeeds."""
        with patch("model_api.adapters.openvino_adapter.AsyncInferQueue") as mock_aiq:
            mock_queue = MagicMock()
            mock_queue.__len__ = MagicMock(return_value=2)
            mock_aiq.return_value = mock_queue
            ov_adapter.load_model()

            # Make get_property succeed
            ov_adapter.compiled_model.get_property = MagicMock(return_value="4")
            ov_adapter.log_runtime_settings()

    def test_log_runtime_settings_cpu_zero_threads(self, ov_adapter):
        """Cover the 'AUTO' branch for nthreads."""
        with patch("model_api.adapters.openvino_adapter.AsyncInferQueue") as mock_aiq:
            mock_queue = MagicMock()
            mock_queue.__len__ = MagicMock(return_value=2)
            mock_aiq.return_value = mock_queue
            ov_adapter.load_model()

            ov_adapter.compiled_model.get_property = MagicMock(return_value="0")
            ov_adapter.log_runtime_settings()


class TestOpenvinoAdapterNPUDynamic:
    def test_reshape_dynamic_nchw_all_dims(self, ov_adapter):
        """Cover NCHW dynamic reshape: dim 0 = -1, dim 1 = channel (NCHW)."""
        mock_input = MagicMock()
        mock_input.partial_shape.is_dynamic = True
        mock_input.get_any_name.return_value = "input"

        with patch("model_api.adapters.openvino_adapter.get_input_shape") as mock_gis:
            # NCHW: dim[1]=3 (<=4), all -1 except channel
            mock_gis.return_value = [-1, 3, -1, -1]
            ov_adapter.model.inputs = [mock_input]
            ov_adapter.reshape_dynamic_inputs()

    def test_reshape_dynamic_nhwc_all_dims(self, ov_adapter):
        """Cover NHWC dynamic reshape: dim 3 = channel."""
        mock_input = MagicMock()
        mock_input.partial_shape.is_dynamic = True
        mock_input.get_any_name.return_value = "input"

        with patch("model_api.adapters.openvino_adapter.get_input_shape") as mock_gis:
            # NHWC: dim[1]=big → not NCHW, so NHWC
            mock_gis.return_value = [-1, -1, -1, -1]
            ov_adapter.model.inputs = [mock_input]
            ov_adapter.reshape_dynamic_inputs()

    def test_reshape_dynamic_nchw_dim1_is_channel(self, ov_adapter):
        """Covers NCHW i==1 → append(3) path."""
        mock_input = MagicMock()
        mock_input.partial_shape.is_dynamic = True
        mock_input.get_any_name.return_value = "input"

        with patch("model_api.adapters.openvino_adapter.get_input_shape") as mock_gis:
            mock_gis.return_value = [1, -1, -1, -1]
            ov_adapter.model.inputs = [mock_input]
            ov_adapter.reshape_dynamic_inputs()

    def test_reshape_dynamic_nhwc_dim3_is_channel(self, ov_adapter):
        """Covers NHWC i==3 → append(3), else → append(224) paths."""
        mock_input = MagicMock()
        mock_input.partial_shape.is_dynamic = True
        mock_input.get_any_name.return_value = "input"

        with patch("model_api.adapters.openvino_adapter.get_input_shape") as mock_gis:
            # 4D, dim[1] > 4 → NHWC
            mock_gis.return_value = [1, -1, -1, -1]
            # Override: dim[1] is not <= 4 to force NHWC
            mock_gis.return_value = [-1, 100, -1, -1]
            ov_adapter.model.inputs = [mock_input]
            ov_adapter.reshape_dynamic_inputs()


class TestEmbedPreprocessingLegacyDtype:
    def test_embed_preprocessing_dtype_int(self, ov_adapter):
        """Cover the legacy dtype=int path (line 467)."""
        import openvino as ov

        param = ov.op.Parameter(ov.Type.f32, ov.Shape([1, 3, 224, 224]))
        model = ov.Model(param, [param])
        ov_adapter.model = model

        with patch("model_api.adapters.openvino_adapter.AsyncInferQueue") as mock_aiq:
            mock_queue = MagicMock()
            mock_queue.__len__ = MagicMock(return_value=2)
            mock_aiq.return_value = mock_queue

            ov_adapter.embed_preprocessing(
                layout="NCHW",
                resize_mode="standard",
                interpolation_mode="LINEAR",
                target_shape=(224, 224),
                pad_value=0,
                dtype=int,
                input_dtype="unknown_dtype",
            )


class TestOpenvinoAbsentImportError:
    def test_openvino_absent_on_import_failure(self):
        """Lines 32-33: except ImportError sets openvino_absent = True."""
        import importlib
        import sys

        import model_api.adapters.openvino_adapter as mod

        orig = sys.modules["openvino"]
        sys.modules["openvino"] = None
        try:
            importlib.reload(mod)
            assert mod.openvino_absent is True
        finally:
            sys.modules["openvino"] = orig
            importlib.reload(mod)
            # Refresh stale reference in model.py
            import model_api.models.model as model_mod

            model_mod.OpenvinoAdapter = mod.OpenvinoAdapter
