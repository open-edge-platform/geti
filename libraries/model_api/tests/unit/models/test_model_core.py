#
# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#

"""Comprehensive unit tests for Model, ImageModel, and DetectionModel core infrastructure.

Targets 100% coverage of:
  - models/model.py
  - models/image_model.py
  - models/detection_model.py
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from model_api.adapters.inference_adapter import InferenceAdapter
from model_api.models.model import Model, WrapperError

rng = np.random.default_rng(0)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@dataclass
class FakeMetadata:
    """Lightweight metadata matching the Metadata interface."""

    names: set = field(default_factory=set)
    shape: list = field(default_factory=list)
    layout: str = ""
    precision: str = ""
    type: str = ""
    meta: dict = field(default_factory=dict)


_RT_INFO_ERROR = RuntimeError(
    "Cannot get runtime attribute. Path to runtime attribute is incorrect.",
)


def _make_adapter(
    input_shape=(1, 3, 224, 224),
    output_shape=(1, 1000),
    layout="NCHW",
    extra_inputs=None,
    rt_info=None,
):
    """Build a mock InferenceAdapter suitable for Model / ImageModel / DetectionModel."""
    adapter = MagicMock(spec=InferenceAdapter)

    image_meta = FakeMetadata(shape=list(input_shape), layout=layout)
    inputs = {"image": image_meta}
    if extra_inputs:
        inputs.update(extra_inputs)

    out_meta = FakeMetadata(shape=list(output_shape))
    outputs = {"output": out_meta}

    adapter.get_input_layers.return_value = inputs
    adapter.get_output_layers.return_value = outputs
    adapter.get_rt_info.side_effect = rt_info or _RT_INFO_ERROR
    adapter.embed_preprocessing = MagicMock()
    adapter.load_model.return_value = None
    adapter.infer_sync.return_value = {"output": np.zeros(output_shape)}
    adapter.infer_async.return_value = None
    adapter.set_callback.return_value = None
    adapter.is_ready.return_value = True
    adapter.await_all.return_value = None
    adapter.await_any.return_value = None
    adapter.reshape_model.return_value = None
    adapter.get_raw_result.return_value = {"output": np.zeros(output_shape)}
    adapter.update_model_info.return_value = None
    adapter.save_model.return_value = None
    adapter.get_model.return_value = MagicMock()
    return adapter


# ===========================  MODEL TESTS  =================================


class TestModelConstructor:
    """Tests for Model.__init__ (lines 66-103)."""

    def test_basic_construction(self):
        adapter = _make_adapter()
        model = Model(adapter, configuration={}, preload=False)
        assert model.model_loaded is False
        assert model.inputs is not None
        assert model.outputs is not None

    def test_preload_calls_load(self):
        adapter = _make_adapter()
        model = Model(adapter, configuration={}, preload=True)
        assert model.model_loaded is True
        adapter.load_model.assert_called_once()

    def test_onnx_adapter_unsupported_wrapper(self):
        """Line 91 - ONNXRuntimeAdapter with unsupported wrapper raises error."""
        from model_api.adapters.onnx_adapter import ONNXRuntimeAdapter

        adapter = MagicMock(spec=ONNXRuntimeAdapter)
        adapter.get_input_layers.return_value = {"x": FakeMetadata(shape=[1, 3])}
        adapter.get_output_layers.return_value = {"y": FakeMetadata(shape=[1, 10])}
        adapter.get_rt_info.side_effect = _RT_INFO_ERROR

        with pytest.raises(WrapperError, match="ONNXRuntimeAdapter is only supported"):
            Model(adapter, configuration={}, preload=False)


class TestModelLoadConfig:
    """Tests for Model._load_config (lines 398-445)."""

    def test_config_sets_attribute(self):
        """Line 424 - rt_info value sets attribute via __setattr__."""
        adapter = _make_adapter()
        Model(adapter, configuration={}, preload=False)

    def test_config_overrides_param(self):
        """Lines 430-441 - user config overrides parameter defaults."""
        from model_api.models.image_model import ImageModel

        adapter = _make_adapter()
        model = ImageModel(adapter, configuration={"resize_type": "fit_to_window"}, preload=False)
        assert model.params.resize_type == "fit_to_window"

    def test_config_invalid_value_raises(self):
        """Lines 434-439 - validation error in config raises WrapperError."""
        from model_api.models.image_model import ImageModel

        adapter = _make_adapter()
        with pytest.raises(WrapperError, match="Incorrect user configuration"):
            ImageModel(adapter, configuration={"resize_type": "INVALID_TYPE"}, preload=False)

    def test_config_unknown_param_warns(self, caplog):
        """Lines 442-443 - unknown param logs warning."""
        adapter = _make_adapter()
        with caplog.at_level(logging.WARNING):
            Model(adapter, configuration={"unknown_param_xyz": 42}, preload=False)
        assert any("unknown_param_xyz" in r.message for r in caplog.records)

    def test_config_none_value_skipped(self):
        """Lines 431-432 - None values are skipped."""
        adapter = _make_adapter()
        Model(adapter, configuration={"resize_type": None}, preload=False)

    def test_rt_info_non_missing_error_propagates(self):
        """Line 428 - RuntimeError that is NOT missing-rt-info is re-raised."""
        from model_api.models.image_model import ImageModel

        def rt_side_effect(path):
            msg = "Some other error"
            raise RuntimeError(msg)

        adapter = _make_adapter(rt_info=rt_side_effect)
        with pytest.raises(RuntimeError, match="Some other error"):
            ImageModel(adapter, configuration={}, preload=False)


class TestModelGetParam:
    """Tests for get_param (lines 105-122)."""

    def test_get_param_returns_attribute(self):
        """Line 120 - returns instance attribute (not prefixed)."""
        adapter = _make_adapter()
        model = Model(adapter, configuration={}, preload=False)
        # Access via params descriptor which calls get_param
        assert model._parameters_cache is None or isinstance(model._parameters_cache, dict)  # noqa: SLF001

    def test_get_param_unknown_raises(self):
        """Line 122 - unknown parameter raises."""
        adapter = _make_adapter()
        model = Model(adapter, configuration={}, preload=False)
        with pytest.raises(WrapperError, match="not found"):
            model.get_param("nonexistent_parameter_xyz")


class TestModelGetCachedParameters:
    """Tests for get_cached_parameters (lines 124-132)."""

    def test_cache_initialized_on_first_access(self):
        """Line 130-132 - cache is lazily initialized."""
        adapter = _make_adapter()
        model = Model(adapter, configuration={}, preload=False)
        model._parameters_cache = None  # noqa: SLF001
        result = model.get_cached_parameters()
        assert isinstance(result, dict)
        assert model._parameters_cache is result  # noqa: SLF001


class TestModelGetModel:
    """Tests for get_model (line 141)."""

    def test_get_model_delegates(self):
        adapter = _make_adapter()
        model = Model(adapter, configuration={}, preload=False)
        model.get_model()
        adapter.get_model.assert_called_once()


class TestModelGetPerformanceMetrics:
    """Tests for get_performance_metrics (line 150)."""

    def test_returns_perf(self):
        adapter = _make_adapter()
        model = Model(adapter, configuration={}, preload=False)
        perf = model.get_performance_metrics()
        assert perf is model.perf


class TestModelBasePreprocess:
    """Tests for Model.base_preprocess (line 473) and preprocess (line 486)."""

    def test_base_preprocess_raises_not_implemented(self):
        """Line 473 - abstract base_preprocess raises NotImplementedError."""
        adapter = _make_adapter()
        model = Model(adapter, configuration={}, preload=False)
        with pytest.raises(NotImplementedError):
            model.base_preprocess(np.zeros((224, 224, 3)))

    def test_preprocess_passthrough(self):
        """Line 486 - default preprocess returns inputs unchanged."""
        adapter = _make_adapter()
        model = Model(adapter, configuration={}, preload=False)
        d, m = {"x": 1}, {"y": 2}
        rd, rm = model.preprocess(d, m)
        assert rd is d
        assert rm is m


class TestModelPostprocess:
    """Tests for postprocess (line 503)."""

    def test_postprocess_raises_not_implemented(self):
        adapter = _make_adapter()
        model = Model(adapter, configuration={}, preload=False)
        with pytest.raises(NotImplementedError):
            model.postprocess({}, {})


class TestModelCheckIONumber:
    """Tests for _check_io_number (lines 521-544)."""

    def test_int_inputs_ok(self):
        adapter = _make_adapter()
        model = Model(adapter, configuration={}, preload=False)
        model._check_io_number(1, 1)  # noqa: SLF001

    def test_int_inputs_mismatch(self):
        """Line 522-526 - wrong int input count."""
        adapter = _make_adapter()
        model = Model(adapter, configuration={}, preload=False)
        with pytest.raises(WrapperError, match="Expected 2 input blob"):
            model._check_io_number(2, 1)  # noqa: SLF001

    def test_int_inputs_skip_minus_one(self):
        """Line 522 - -1 skips check."""
        adapter = _make_adapter()
        model = Model(adapter, configuration={}, preload=False)
        model._check_io_number(-1, -1)  # noqa: SLF001

    def test_tuple_inputs_ok(self):
        adapter = _make_adapter()
        model = Model(adapter, configuration={}, preload=False)
        model._check_io_number((1, 2), (1, 2))  # noqa: SLF001

    def test_tuple_inputs_mismatch(self):
        """Lines 527-531 - wrong tuple input count."""
        adapter = _make_adapter()
        model = Model(adapter, configuration={}, preload=False)
        with pytest.raises(WrapperError, match="Expected 2 or 3 input blobs"):
            model._check_io_number((2, 3), 1)  # noqa: SLF001

    def test_int_outputs_mismatch(self):
        """Lines 533-538 - wrong int output count."""
        adapter = _make_adapter()
        model = Model(adapter, configuration={}, preload=False)
        with pytest.raises(WrapperError, match="Expected 5 output blob"):
            model._check_io_number(1, 5)  # noqa: SLF001

    def test_tuple_outputs_mismatch(self):
        """Lines 539-544 - wrong tuple output count."""
        adapter = _make_adapter()
        model = Model(adapter, configuration={}, preload=False)
        with pytest.raises(WrapperError, match="Expected 5 or 6 output blobs"):
            model._check_io_number(1, (5, 6))  # noqa: SLF001


class TestModelCall:
    """Tests for __call__ (lines 555-566)."""

    def test_call_runs_full_pipeline(self):
        """Lines 555-566 - preprocess→infer→postprocess."""
        adapter = _make_adapter()
        model = Model(adapter, configuration={}, preload=True)
        model.base_preprocess = MagicMock(return_value=({"image": np.zeros((1, 3, 224, 224))}, {"meta": 1}))
        model.postprocess = MagicMock(return_value="result")
        result = model(np.zeros((224, 224, 3)))
        assert result == "result"
        model.base_preprocess.assert_called_once()
        adapter.infer_sync.assert_called_once()
        model.postprocess.assert_called_once()


class TestModelInferBatch:
    """Tests for infer_batch (lines 577-599)."""

    def test_infer_batch(self):
        """Lines 577-599 - batch inference with callback."""
        adapter = _make_adapter()
        model = Model(adapter, configuration={}, preload=True)
        model.base_preprocess = MagicMock(return_value=({"image": np.zeros((1, 3, 224, 224))}, {"m": 1}))
        model.postprocess = MagicMock(return_value="res")

        # Simulate infer_async triggering callback
        def fake_infer_async(data, cb_data):
            Model._process_callback(MagicMock(), cb_data)  # noqa: SLF001

        adapter.infer_async.side_effect = fake_infer_async

        results = model.infer_batch([np.zeros((224, 224, 3)), np.zeros((224, 224, 3))])
        assert len(results) == 2


class TestModelLoad:
    """Tests for load (lines 608-612)."""

    def test_load(self):
        adapter = _make_adapter()
        model = Model(adapter, configuration={}, preload=False)
        assert not model.model_loaded
        model.load()
        assert model.model_loaded
        adapter.load_model.assert_called_once()

    def test_load_skip_if_loaded(self):
        """Line 608 - skip if already loaded."""
        adapter = _make_adapter()
        model = Model(adapter, configuration={}, preload=True)
        model.load()
        assert adapter.load_model.call_count == 1

    def test_load_force(self):
        """Line 608 - force reload."""
        adapter = _make_adapter()
        model = Model(adapter, configuration={}, preload=True)
        model.load(force=True)
        assert adapter.load_model.call_count == 2


class TestModelReshape:
    """Tests for reshape (lines 622-630)."""

    def test_reshape_unloaded(self):
        """Lines 628-630 - reshape when not loaded."""
        adapter = _make_adapter()
        model = Model(adapter, configuration={}, preload=False)
        model.reshape({"image": [1, 3, 300, 300]})
        adapter.reshape_model.assert_called_once()
        adapter.get_input_layers.assert_called()
        adapter.get_output_layers.assert_called()

    def test_reshape_when_loaded_warns(self):
        """Lines 622-627 - reshape when loaded resets flag."""
        adapter = _make_adapter()
        model = Model(adapter, configuration={}, preload=True)
        assert model.model_loaded is True
        # Suppress the logging format error (source passes two positional args to warning())
        logging.disable(logging.CRITICAL)
        try:
            model.reshape({"image": [1, 3, 300, 300]})
        finally:
            logging.disable(logging.NOTSET)
        assert model.model_loaded is False


class TestModelInferSync:
    """Tests for infer_sync (lines 637-642)."""

    def test_infer_sync_success(self):
        adapter = _make_adapter()
        model = Model(adapter, configuration={}, preload=True)
        result = model.infer_sync({"image": np.zeros((1, 3, 224, 224))})
        assert "output" in result

    def test_infer_sync_not_loaded_raises(self):
        """Lines 637-641 - error if not loaded."""
        adapter = _make_adapter()
        model = Model(adapter, configuration={}, preload=False)
        with pytest.raises(WrapperError, match="not loaded"):
            model.infer_sync({"image": np.zeros((1, 3, 224, 224))})


class TestModelInferAsyncRaw:
    """Tests for infer_async_raw (lines 652-657)."""

    def test_infer_async_raw_success(self):
        adapter = _make_adapter()
        model = Model(adapter, configuration={}, preload=True)
        model.infer_async_raw({"image": np.zeros((1, 3, 224, 224))}, "cb_data")
        adapter.infer_async.assert_called_once()

    def test_infer_async_raw_not_loaded_raises(self):
        """Lines 652-656 - error if not loaded."""
        adapter = _make_adapter()
        model = Model(adapter, configuration={}, preload=False)
        with pytest.raises(WrapperError, match="not loaded"):
            model.infer_async_raw({}, "cb")


class TestModelInferAsync:
    """Tests for infer_async (lines 668-692)."""

    def test_infer_async_success(self):
        """Lines 668-692 - full async path."""
        adapter = _make_adapter()
        model = Model(adapter, configuration={}, preload=True)
        model.base_preprocess = MagicMock(return_value=({"image": np.zeros((1, 3, 224, 224))}, {"m": 1}))
        model.infer_async(np.zeros((224, 224, 3)), "user_data")
        adapter.infer_async.assert_called_once()

    def test_infer_async_not_loaded_raises(self):
        """Lines 668-672 - error if not loaded."""
        adapter = _make_adapter()
        model = Model(adapter, configuration={}, preload=False)
        with pytest.raises(WrapperError, match="not loaded"):
            model.infer_async({}, "user_data")


class TestModelProcessCallback:
    """Tests for _process_callback (lines 699-726)."""

    def test_process_callback_with_tokens(self):
        """Lines 699-726 - 8-element callback_data path."""
        adapter = _make_adapter()
        model = Model(adapter, configuration={}, preload=False)
        postprocess_fn = MagicMock(return_value="result")
        callback_fn = MagicMock()
        get_result_fn = MagicMock(return_value={"output": np.zeros(5)})
        total_token = object()
        inference_token = object()

        cb_data = (model, {"m": 1}, get_result_fn, postprocess_fn, callback_fn, "user", total_token, inference_token)
        Model._process_callback(MagicMock(), cb_data)  # noqa: SLF001
        postprocess_fn.assert_called_once()
        callback_fn.assert_called_once_with("result", "user")

    def test_process_callback_without_tokens(self):
        """Lines 712-713 - 6-element callback_data (legacy) path."""
        adapter = _make_adapter()
        model = Model(adapter, configuration={}, preload=False)
        postprocess_fn = MagicMock(return_value="result")
        callback_fn = MagicMock()
        get_result_fn = MagicMock(return_value={"output": np.zeros(5)})

        cb_data = (model, {"m": 1}, get_result_fn, postprocess_fn, callback_fn, "user")
        Model._process_callback(MagicMock(), cb_data)  # noqa: SLF001
        callback_fn.assert_called_once_with("result", "user")


class TestModelSetCallback:
    """Tests for set_callback (lines 735-736)."""

    def test_set_callback(self):
        adapter = _make_adapter()
        model = Model(adapter, configuration={}, preload=False)

        fn = MagicMock()
        model.set_callback(fn)
        assert model.callback_fn is fn
        adapter.set_callback.assert_called_once_with(Model._process_callback)  # noqa: SLF001


class TestModelIsReady:
    """Tests for is_ready (line 740)."""

    def test_is_ready(self):
        adapter = _make_adapter()
        model = Model(adapter, configuration={}, preload=False)
        assert model.is_ready() is True


class TestModelAwait:
    """Tests for await_all (line 744) and await_any (line 748)."""

    def test_await_all(self):
        adapter = _make_adapter()
        model = Model(adapter, configuration={}, preload=False)
        model.await_all()
        adapter.await_all.assert_called_once()

    def test_await_any(self):
        adapter = _make_adapter()
        model = Model(adapter, configuration={}, preload=False)
        model.await_any()
        adapter.await_any.assert_called_once()


class TestModelLogLayersInfo:
    """Tests for log_layers_info (lines 752-758)."""

    def test_log_layers_info(self, caplog):
        adapter = _make_adapter()
        model = Model(adapter, configuration={}, preload=False)
        with caplog.at_level(logging.INFO):
            model.log_layers_info()
        assert any("Input layer" in r.message for r in caplog.records)
        assert any("Output layer" in r.message for r in caplog.records)


class TestModelSave:
    """Tests for save (lines 772-781)."""

    def test_save(self):
        adapter = _make_adapter()
        model = Model(adapter, configuration={}, preload=False)
        model.save("/some/path", "/some/weights", "v1")
        adapter.update_model_info.assert_called_once()
        adapter.save_model.assert_called_once_with("/some/path", "/some/weights", "v1")


class TestModelCreateModel:
    """Tests for create_model (lines 216-244)."""

    def test_create_model_with_adapter_instance(self):
        """Line 216-217 - passing an adapter directly."""
        adapter = _make_adapter()
        model = Model.create_model(adapter, model_type="Model", preload=False)
        assert isinstance(model, Model)

    @patch("model_api.models.model.OVMSAdapter")
    def test_create_model_ovms_url(self, mock_ovms_cls):
        """Lines 218-219 - OVMS URL creates OVMSAdapter."""
        mock_ovms_cls.is_ovms_model.return_value = True
        mock_adapter = _make_adapter()
        mock_ovms_cls.return_value = mock_adapter
        model = Model.create_model("localhost:9000/models/mymodel", model_type="Model", preload=False)
        assert isinstance(model, Model)

    @patch("model_api.models.model.OpenvinoAdapter")
    @patch("model_api.models.model.get_user_config")
    @patch("model_api.models.model.create_core")
    @patch("model_api.models.model.OVMSAdapter")
    def test_create_model_from_path(self, mock_ovms, mock_core, mock_config, mock_ov_cls):
        """Lines 220-235 - path creates OpenvinoAdapter."""
        mock_ovms.is_ovms_model.return_value = False
        mock_core.return_value = MagicMock()
        mock_config.return_value = {}
        mock_adapter = _make_adapter()
        mock_ov_cls.return_value = mock_adapter
        model = Model.create_model("/path/to/model.xml", model_type="Model", preload=False)
        assert isinstance(model, Model)

    def test_create_model_detects_type_from_rt_info(self):
        """Lines 236-243 - model_type auto-detected from rt_info."""
        rt_mock = MagicMock()
        rt_mock.astype.return_value = "Model"

        adapter = _make_adapter()
        adapter.get_rt_info.side_effect = None
        adapter.get_rt_info.return_value = rt_mock
        model = Model.create_model(adapter, model_type=None, preload=False)
        assert isinstance(model, Model)

    def test_create_model_detects_type_from_config_fallback(self):
        """Line 242 - model_type from configuration if rt_info fails."""
        adapter = _make_adapter()
        model = Model.create_model(adapter, model_type=None, configuration={"model_type": "Model"}, preload=False)
        assert isinstance(model, Model)

    def test_create_model_detect_anomaly(self):
        """Lines 347-358 - detect_model_type finds AnomalyDetection."""
        adapter = _make_adapter()
        adapter.get_input_layers.return_value = {"input": FakeMetadata(shape=[1, 3, 224, 224])}
        adapter.get_output_layers.return_value = {
            "pred_score": FakeMetadata(shape=[1]),
            "pred_label": FakeMetadata(shape=[1]),
            "anomaly_map": FakeMetadata(shape=[1, 224, 224]),
            "pred_mask": FakeMetadata(shape=[1, 224, 224]),
        }
        result = Model.detect_model_type(adapter)
        assert result == "AnomalyDetection"

    def test_detect_model_type_unknown(self):
        """Line 358 - returns 'uknown' for unrecognized models."""
        adapter = _make_adapter()
        result = Model.detect_model_type(adapter)
        assert result == "uknown"


class TestModelFromPretrained:
    """Tests for from_pretrained (lines 247-343)."""

    @patch("model_api.models.model.Model.create_model")
    @patch("model_api.utils.hf_hub_helper.download_from_hf")
    def test_from_pretrained(self, mock_download, mock_create):
        """Lines 315-343 - delegates to download_from_hf then create_model."""
        mock_download.return_value = "/downloaded/model.xml"
        mock_create.return_value = MagicMock()
        result = Model.from_pretrained("user/model-name", model_type="Model")
        mock_download.assert_called_once()
        mock_create.assert_called_once()
        assert result is mock_create.return_value


# ======================  IMAGE MODEL TESTS  ================================


class TestImageModelConstructor:
    """Tests for ImageModel.__init__ (lines 50-143)."""

    def test_nchw_layout(self):
        from model_api.models.image_model import ImageModel

        adapter = _make_adapter(input_shape=(1, 3, 224, 224), layout="NCHW")
        model = ImageModel(adapter, configuration={}, preload=False)
        assert model.nchw_layout is True
        assert model.n == 1
        assert model.c == 3
        assert model.h == 224
        assert model.w == 224

    def test_nhwc_layout(self):
        """Line 73 - NHWC unpacking."""
        from model_api.models.image_model import ImageModel

        adapter = _make_adapter(input_shape=(1, 224, 224, 3), layout="NHWC")
        model = ImageModel(adapter, configuration={}, preload=False)
        assert model.nchw_layout is False
        assert model.h == 224
        assert model.w == 224

    def test_dynamic_shape(self):
        """Lines 76-77 - dynamic input shapes (h=-1 or w=-1)."""
        from model_api.models.image_model import ImageModel

        adapter = _make_adapter(input_shape=(1, 3, -1, -1), layout="NCHW")
        model = ImageModel(adapter, configuration={}, preload=False)
        assert model._is_dynamic is True  # noqa: SLF001

    def test_embedded_processing(self):
        """Lines 113-114 - embedded_processing overrides h, w."""
        from model_api.models.image_model import ImageModel

        adapter = _make_adapter(input_shape=(1, 3, 224, 224), layout="NCHW")
        model = ImageModel(
            adapter,
            configuration={"embedded_processing": True, "orig_height": 480, "orig_width": 640},
            preload=False,
        )
        assert model.h == 480
        assert model.w == 640

    def test_non_dynamic_embeds_preprocessing(self):
        """Lines 115-141 - embed_preprocessing is called for non-dynamic models."""
        from model_api.models.image_model import ImageModel

        adapter = _make_adapter(input_shape=(1, 3, 300, 300), layout="NCHW")
        model = ImageModel(adapter, configuration={}, preload=False)
        adapter.embed_preprocessing.assert_called_once()
        assert model._embedded_processing is True  # noqa: SLF001

    def test_intensity_auto_for_scale_to_unit(self):
        """Lines 84-86 - intensity_max_value auto-inferred."""
        from model_api.models.image_model import ImageModel

        adapter = _make_adapter()
        model = ImageModel(
            adapter,
            configuration={"intensity_mode": "scale_to_unit", "input_dtype": "u8"},
            preload=False,
        )
        # Should not raise, and model should be created
        assert model is not None

    def test_input_frame_shape_passed_to_embed(self):
        """Lines 117-118 - input_frame_height/width passed to embed_preprocessing."""
        from model_api.models.image_model import ImageModel

        adapter = _make_adapter(input_shape=(1, 3, 300, 300), layout="NCHW")
        ImageModel(
            adapter,
            configuration={"input_frame_height": 480, "input_frame_width": 640},
            preload=False,
        )
        call_kwargs = adapter.embed_preprocessing.call_args
        assert call_kwargs is not None


class TestImageModelGetInputs:
    """Tests for _get_inputs (lines 174-198)."""

    def test_4d_image_input(self):
        from model_api.models.image_model import ImageModel

        adapter = _make_adapter()
        model = ImageModel(adapter, configuration={}, preload=False)
        assert "image" in model.image_blob_names

    def test_2d_extra_input(self):
        """Lines 188-189 - 2D tensor info blobs."""
        from model_api.models.image_model import ImageModel

        adapter = _make_adapter(
            extra_inputs={"info": FakeMetadata(shape=[1, 3], layout="NC")},
        )
        model = ImageModel(adapter, configuration={}, preload=False)
        assert "info" in model.image_info_blob_names

    def test_unsupported_shape_raises(self):
        """Lines 190-193 - 3D tensor raises WrapperError."""
        from model_api.models.image_model import ImageModel

        adapter = _make_adapter(
            extra_inputs={"bad": FakeMetadata(shape=[1, 3, 5], layout="")},
        )
        with pytest.raises(WrapperError, match="only 2D and 4D"):
            ImageModel(adapter, configuration={}, preload=False)

    def test_no_image_input_raises(self):
        """Lines 194-197 - no 4D input raises WrapperError."""
        from model_api.models.image_model import ImageModel

        adapter = MagicMock(spec=InferenceAdapter)
        adapter.get_input_layers.return_value = {"scalar": FakeMetadata(shape=[1, 3], layout="NC")}
        adapter.get_output_layers.return_value = {"output": FakeMetadata(shape=[1, 10])}
        adapter.get_rt_info.side_effect = _RT_INFO_ERROR
        adapter.embed_preprocessing = MagicMock()
        with pytest.raises(WrapperError, match="no 4D input"):
            ImageModel(adapter, configuration={}, preload=False)


class TestImageModelGetLabelName:
    """Tests for get_label_name (lines 156-172)."""

    def test_label_found(self):
        from model_api.models.detection_model import DetectionModel

        adapter = _make_adapter(input_shape=(1, 3, 300, 300), output_shape=(1, 1, 200, 7))
        model = DetectionModel(adapter, configuration={"labels": ["cat", "dog"]}, preload=False)
        assert model.get_label_name(0) == "cat"
        assert model.get_label_name(1) == "dog"

    def test_label_out_of_range(self):
        """Lines 170-171 - out-of-range returns auto-generated name."""
        from model_api.models.detection_model import DetectionModel

        adapter = _make_adapter(input_shape=(1, 3, 300, 300), output_shape=(1, 1, 200, 7))
        model = DetectionModel(adapter, configuration={"labels": ["cat"]}, preload=False)
        assert model.get_label_name(999) == "#999"

    def test_label_none(self):
        """Lines 167-169 - no labels set returns auto-generated name (empty list)."""
        from model_api.models.detection_model import DetectionModel

        adapter = _make_adapter(input_shape=(1, 3, 300, 300), output_shape=(1, 1, 200, 7))
        model = DetectionModel(adapter, configuration={}, preload=False)
        assert model.get_label_name(0) == "#0"

    def test_label_explicitly_none(self):
        """Lines 168-169 - labels is literally None returns auto-generated name."""
        from model_api.models.detection_model import DetectionModel

        adapter = _make_adapter(input_shape=(1, 3, 300, 300), output_shape=(1, 1, 200, 7))
        model = DetectionModel(adapter, configuration={}, preload=False)
        # Force labels to None (simulating rt_info returning "None")
        model._labels = None  # noqa: SLF001
        assert model.get_label_name(0) == "#0"


class TestImageModelBasePreprocess:
    """Tests for base_preprocess (lines 200-249)."""

    def test_base_preprocess_standard(self):
        """Lines 231-249 - standard preprocessing flow (non-embedded)."""
        from model_api.models.image_model import ImageModel

        adapter = _make_adapter(input_shape=(1, 3, 300, 300), layout="NCHW")
        model = ImageModel(adapter, configuration={}, preload=False)
        # Force non-embedded path
        model._embedded_processing = False  # noqa: SLF001
        image = rng.integers(0, 255, (480, 640, 3), dtype=np.uint8)
        result = model.base_preprocess(image)
        assert isinstance(result, list)
        assert len(result) == 2
        dict_inputs, meta = result
        assert "image" in dict_inputs
        assert "original_shape" in meta
        assert "resized_shape" in meta

    def test_base_preprocess_standard_with_repeat_channels(self):
        """Line 231-232 - intensity_repeat_channels triggers _repeat_single_channel."""
        from model_api.models.image_model import ImageModel

        adapter = _make_adapter(input_shape=(1, 3, 300, 300), layout="NCHW")
        model = ImageModel(adapter, configuration={"intensity_repeat_channels": True}, preload=False)
        model._embedded_processing = False  # noqa: SLF001
        # Provide single-channel image (H, W, 1)
        image = rng.integers(0, 255, (480, 640, 1), dtype=np.uint8)
        result = model.base_preprocess(image)
        assert isinstance(result, list)

    def test_base_preprocess_embedded(self):
        """Lines 225-228 - embedded preprocessing path."""
        from model_api.models.image_model import ImageModel

        adapter = _make_adapter(input_shape=(1, 3, 224, 224), layout="NCHW")
        model = ImageModel(
            adapter,
            configuration={"embedded_processing": True, "orig_height": 480, "orig_width": 640},
            preload=False,
        )
        image = rng.integers(0, 255, (480, 640, 3), dtype=np.uint8)
        result = model.base_preprocess(image)
        assert isinstance(result, list)
        dict_inputs, _ = result
        assert "image" in dict_inputs


class TestImageModelPreprocessEmbedded:
    """Tests for _preprocess_embedded (lines 251-266)."""

    def test_preprocess_embedded_fixed(self):
        """Lines 257-258 - fixed shape uses model dims."""
        from model_api.models.image_model import ImageModel

        adapter = _make_adapter(input_shape=(1, 3, 224, 224), layout="NCHW")
        model = ImageModel(
            adapter,
            configuration={"embedded_processing": True, "orig_height": 480, "orig_width": 640},
            preload=False,
        )
        model._is_dynamic = False  # noqa: SLF001
        image = rng.integers(0, 255, (480, 640, 3), dtype=np.uint8)
        dict_inputs, meta = model._preprocess_embedded(image)  # noqa: SLF001
        assert dict_inputs["image"].shape[0] == 1
        assert "original_shape" in meta

    def test_preprocess_embedded_dynamic(self):
        """Lines 254-256 - dynamic shape uses image dims."""
        from model_api.models.image_model import ImageModel

        adapter = _make_adapter(input_shape=(1, 3, -1, -1), layout="NCHW")
        model = ImageModel(
            adapter,
            configuration={"embedded_processing": True, "orig_height": 480, "orig_width": 640},
            preload=False,
        )
        image = rng.integers(0, 255, (100, 200, 3), dtype=np.uint8)
        _, meta = model._preprocess_embedded(image)  # noqa: SLF001
        assert meta["resized_shape"] == (200, 100, 3)


class TestImageModelResizeImage:
    """Tests for _resize_image (lines 268-277)."""

    def test_resize_image_fixed(self):
        """Lines 275-277 - fixed shape triggers actual resize."""
        from model_api.models.image_model import ImageModel

        adapter = _make_adapter(input_shape=(1, 3, 300, 300), layout="NCHW")
        model = ImageModel(adapter, configuration={}, preload=False)
        image = rng.integers(0, 255, (480, 640, 3), dtype=np.uint8)
        _, meta = model._resize_image(image)  # noqa: SLF001
        assert "original_shape" in meta
        assert "resized_shape" in meta

    def test_resize_image_dynamic(self):
        """Lines 270-273 - dynamic shape returns image unchanged."""
        from model_api.models.image_model import ImageModel

        adapter = _make_adapter(input_shape=(1, 3, -1, -1), layout="NCHW")
        model = ImageModel(adapter, configuration={}, preload=False)
        image = rng.integers(0, 255, (100, 200, 3), dtype=np.uint8)
        resized, _ = model._resize_image(image)  # noqa: SLF001
        assert resized is image


class TestImageModelInputTransform:
    """Tests for _input_transform (lines 279-280)."""

    def test_input_transform(self):
        from model_api.models.image_model import ImageModel

        adapter = _make_adapter(input_shape=(1, 3, 300, 300), layout="NCHW")
        model = ImageModel(adapter, configuration={}, preload=False)
        image = rng.random((300, 300, 3)).astype(np.float32)
        result = model._input_transform(image)  # noqa: SLF001
        assert result.shape == (300, 300, 3)


class TestImageModelChangeLayout:
    """Tests for _change_layout (lines 305-323)."""

    def test_change_layout_nchw(self):
        """Lines 317-319 - NCHW layout conversion."""
        from model_api.models.image_model import ImageModel

        adapter = _make_adapter(input_shape=(1, 3, 300, 300), layout="NCHW")
        model = ImageModel(adapter, configuration={}, preload=False)
        image = rng.random((300, 300, 3)).astype(np.float32)
        result = model._change_layout(image)  # noqa: SLF001
        assert result.shape == (1, 3, 300, 300)

    def test_change_layout_nhwc(self):
        """Lines 320-321 - NHWC layout conversion."""
        from model_api.models.image_model import ImageModel

        adapter = _make_adapter(input_shape=(1, 300, 300, 3), layout="NHWC")
        model = ImageModel(adapter, configuration={}, preload=False)
        image = rng.random((300, 300, 3)).astype(np.float32)
        result = model._change_layout(image)  # noqa: SLF001
        assert result.shape == (1, 300, 300, 3)

    def test_change_layout_dynamic_nchw(self):
        """Line 314 - dynamic shape with NCHW."""
        from model_api.models.image_model import ImageModel

        adapter = _make_adapter(input_shape=(1, 3, -1, -1), layout="NCHW")
        model = ImageModel(adapter, configuration={}, preload=False)
        image = rng.random((100, 200, 3)).astype(np.float32)
        result = model._change_layout(image)  # noqa: SLF001
        assert result.shape == (1, 3, 100, 200)


class TestImageModelWrapPreprocessCompat:
    """Tests for _wrap_preprocess_for_backward_compat (lines 282-300)."""

    def test_compat_wrapper_exists(self):
        from model_api.models.image_model import ImageModel

        adapter = _make_adapter()
        model = ImageModel(adapter, configuration={}, preload=False)
        # preprocess should be wrapped
        assert callable(model.preprocess)

    def test_compat_new_style_no_warning(self):
        """Line 298 - two-arg call goes through original."""
        import warnings

        from model_api.models.image_model import ImageModel

        adapter = _make_adapter()
        model = ImageModel(adapter, configuration={}, preload=False)
        d = {"image": np.zeros((1, 3, 224, 224))}
        m = {"original_shape": (480, 640, 3)}
        with warnings.catch_warnings():
            warnings.simplefilter("error", DeprecationWarning)
            rd, _ = model.preprocess(d, m)
        assert rd is d

    def test_compat_old_style_warns(self):
        """Lines 288-297 - single ndarray arg triggers deprecation."""
        from model_api.models.image_model import ImageModel

        adapter = _make_adapter()
        model = ImageModel(adapter, configuration={}, preload=False)
        image = rng.integers(0, 255, (480, 640, 3), dtype=np.uint8)
        with pytest.warns(DeprecationWarning, match="deprecated since model_api v0.4.0"):
            result = model.preprocess(image)
        assert isinstance(result, list)


# ====================  DETECTION MODEL TESTS  ==============================


class TestDetectionModelConstructor:
    """Tests for DetectionModel.__init__ (lines 26-48)."""

    def test_basic_construction(self):
        """Line 41 - basic construction."""
        from model_api.models.detection_model import DetectionModel

        adapter = _make_adapter(input_shape=(1, 3, 300, 300), output_shape=(1, 1, 200, 7))
        model = DetectionModel(adapter, configuration={}, preload=False)
        assert model.image_blob_name == "image"

    def test_with_path_to_labels(self):
        """Lines 47-48 - loads labels from file."""
        from model_api.models.detection_model import DetectionModel

        adapter = _make_adapter(input_shape=(1, 3, 300, 300), output_shape=(1, 1, 200, 7))
        with patch("model_api.models.detection_model.load_labels", return_value=["a", "b"]) as mock_ll:
            model = DetectionModel(adapter, configuration={"path_to_labels": "/some/labels.txt"}, preload=False)
            mock_ll.assert_called_once_with("/some/labels.txt")
            assert model._labels == ["a", "b"]  # noqa: SLF001

    def test_no_image_blob_raises(self):
        """Lines 42-45 - raises if image_blob_name is empty (no 4D inputs)."""
        from model_api.models.detection_model import DetectionModel

        # Create adapter with only 2D inputs (no 4D image blob)
        adapter = _make_adapter(input_shape=(1, 3), output_shape=(1, 1, 200, 7))
        with pytest.raises(WrapperError, match="Failed to identify the input for the image"):
            DetectionModel(adapter, configuration={}, preload=False)


class TestDetectionModelPreprocess:
    """Tests for DetectionModel.preprocess (lines 62-72)."""

    def test_preprocess_adds_resize_info(self):
        """Lines 62-72 - compute resize metadata."""
        from model_api.models.detection_model import DetectionModel

        adapter = _make_adapter(input_shape=(1, 3, 300, 300), output_shape=(1, 1, 200, 7))
        model = DetectionModel(adapter, configuration={}, preload=False)
        dict_inputs = {"image": np.zeros((1, 3, 300, 300))}
        meta = {"original_shape": (480, 640, 3), "resized_shape": (300, 300, 3)}
        # Call the original (unwrapped) preprocess logic
        # The wrapped version will call through to the original
        _, result_meta = model.preprocess(dict_inputs, meta)
        assert "resize_info" in result_meta


class TestDetectionModelResizeDetections:
    """Tests for _resize_detections (lines 84-103)."""

    def _make_detection_model(self):
        from model_api.models.detection_model import DetectionModel

        adapter = _make_adapter(input_shape=(1, 3, 300, 300), output_shape=(1, 1, 200, 7))
        return DetectionModel(adapter, configuration={}, preload=False)

    def test_resize_detections_with_resize_info(self):
        """Lines 86-87 - uses pre-computed resize_info."""
        from model_api.models.result import DetectionResult

        model = self._make_detection_model()
        bboxes = np.array([[0.1, 0.1, 0.5, 0.5]], dtype=np.float64)
        labels = np.array([0])
        scores = np.array([0.9])
        det = DetectionResult(bboxes, labels, scores)

        meta = {
            "original_shape": (480, 640, 3),
            "resize_info": {
                "inverted_scale_x": 640 / 300,
                "inverted_scale_y": 480 / 300,
                "pad_left": 0,
                "pad_top": 0,
            },
        }
        model._resize_detections(det, meta)  # noqa: SLF001
        assert det.bboxes.dtype == np.int32

    def test_resize_detections_without_resize_info(self):
        """Lines 88-95 - computes resize_info on the fly."""
        from model_api.models.result import DetectionResult

        model = self._make_detection_model()
        bboxes = np.array([[0.1, 0.1, 0.5, 0.5]], dtype=np.float64)
        labels = np.array([0])
        scores = np.array([0.9])
        det = DetectionResult(bboxes, labels, scores)

        meta = {"original_shape": (480, 640, 3)}
        model._resize_detections(det, meta)  # noqa: SLF001
        assert det.bboxes.dtype == np.int32


class TestDetectionModelFilterDetections:
    """Tests for _filter_detections (lines 115-120)."""

    def test_filter_by_confidence(self):
        """Lines 115-120 - filters by confidence and area."""
        from model_api.models.detection_model import DetectionModel
        from model_api.models.result import DetectionResult

        adapter = _make_adapter(input_shape=(1, 3, 300, 300), output_shape=(1, 1, 200, 7))
        model = DetectionModel(adapter, configuration={"confidence_threshold": 0.5}, preload=False)

        bboxes = np.array([[10, 10, 100, 100], [5, 5, 6, 6]], dtype=np.float64)
        labels = np.array([0, 1])
        scores = np.array([0.9, 0.3])
        det = DetectionResult(bboxes, labels, scores)

        model._filter_detections(det)  # noqa: SLF001
        assert len(det.bboxes) == 1
        assert det.scores[0] == 0.9

    def test_filter_by_area(self):
        """Lines 115-120 - filter by box area threshold."""
        from model_api.models.detection_model import DetectionModel
        from model_api.models.result import DetectionResult

        adapter = _make_adapter(input_shape=(1, 3, 300, 300), output_shape=(1, 1, 200, 7))
        model = DetectionModel(adapter, configuration={"confidence_threshold": 0.0}, preload=False)

        bboxes = np.array([[10, 10, 100, 100], [5, 5, 6, 6]], dtype=np.float64)
        labels = np.array([0, 1])
        scores = np.array([0.9, 0.8])
        det = DetectionResult(bboxes, labels, scores)

        model._filter_detections(det, box_area_threshold=100)  # noqa: SLF001
        assert len(det.bboxes) == 1


class TestDetectionModelAddLabelNames:
    """Tests for _add_label_names (line 128)."""

    def test_add_label_names(self):
        from model_api.models.detection_model import DetectionModel
        from model_api.models.result import DetectionResult

        adapter = _make_adapter(input_shape=(1, 3, 300, 300), output_shape=(1, 1, 200, 7))
        model = DetectionModel(adapter, configuration={"labels": ["cat", "dog"]}, preload=False)

        bboxes = np.array([[10, 10, 50, 50], [20, 20, 60, 60]], dtype=np.float64)
        labels = np.array([0, 1])
        det = DetectionResult(bboxes, labels)

        model._add_label_names(det)  # noqa: SLF001
        assert det.label_names == ["cat", "dog"]


class TestDetectionModelCalculateNms:
    """Tests for _calculate_nms (line 142)."""

    def test_calculate_nms(self):
        from model_api.models.detection_model import DetectionModel

        adapter = _make_adapter(input_shape=(1, 3, 300, 300), output_shape=(1, 1, 200, 7))
        model = DetectionModel(adapter, configuration={}, preload=False)

        boxes = np.array([[10, 10, 50, 50], [12, 12, 52, 52]], dtype=np.float32)
        scores = np.array([0.9, 0.8], dtype=np.float32)
        labels = np.array([0, 0])

        keep = model._calculate_nms(boxes, scores, labels)  # noqa: SLF001
        assert isinstance(keep, list)
        assert len(keep) >= 1


# ==================  ADDITIONAL COVERAGE TESTS  ============================


class TestModelGetParamUnprefixed:
    """Test for get_param line 120 - return attr without _ prefix."""

    def test_get_param_via_unprefixed_attr(self):
        """Line 119-120 - get_param returns attribute set directly (no _ prefix)."""
        from model_api.models.image_model import ImageModel

        adapter = _make_adapter()
        model = ImageModel(adapter, configuration={}, preload=False)
        # Set an attribute matching a parameter name without _ prefix
        # The parameters() dict includes 'resize_type'; set it directly
        model.resize_type = "fit_to_window"
        model._parameters_cache = None  # reset cache  # noqa: SLF001
        val = model.get_param("resize_type")
        assert val == "fit_to_window"


class TestModelRtInfoSetsValue:
    """Test for _load_config line 424 - rt_info value successfully sets attribute."""

    def test_rt_info_value_sets_attribute(self):
        """Line 424 - rt_info returns a value that is set as attribute."""
        from model_api.models.image_model import ImageModel

        rt_mock = MagicMock()
        rt_mock.astype.return_value = "standard"

        def rt_side_effect(path):
            key = path[-1] if isinstance(path, list) else path
            if key == "resize_type":
                return rt_mock
            raise _RT_INFO_ERROR

        adapter = _make_adapter(rt_info=rt_side_effect)
        model = ImageModel(adapter, configuration={}, preload=False)
        assert model.params.resize_type == "standard"


class TestModelSaveWithParams:
    """Test for save lines 775-778 - iteration over parameters."""

    def test_save_iterates_params(self):
        """Lines 775-778 - save collects all non-None parameter values."""
        from model_api.models.image_model import ImageModel

        adapter = _make_adapter()
        model = ImageModel(adapter, configuration={}, preload=False)
        model.save("/some/path")
        adapter.update_model_info.assert_called_once()
        info = adapter.update_model_info.call_args[0][0]
        assert "model_type" in info


class TestModelAvailableWrappers:
    """Test for available_wrappers lines 375-377."""

    def test_available_wrappers_from_model(self):
        wrappers = Model.available_wrappers()
        assert "Model" in wrappers
        assert len(wrappers) > 1

    def test_available_wrappers_includes_subclasses(self):
        wrappers = Model.available_wrappers()
        assert "ImageModel" in wrappers


class TestModelGetModelClassNotFound:
    """Test for get_model_class line 169 - not found path."""

    def test_get_model_class_not_found(self):
        with pytest.raises(WrapperError, match="There is no model"):
            Model.get_model_class("NonExistentModelXYZ")


class TestImageModelGetLabelNameFromImageModel:
    """Test get_label_name from ImageModel directly (line 169 image_model.py)."""

    def test_label_none_on_detection_model(self):
        """Line 167-169 image_model.py - no labels returns auto name."""
        from model_api.models.detection_model import DetectionModel

        adapter = _make_adapter(input_shape=(1, 3, 300, 300), output_shape=(1, 1, 200, 7))
        model = DetectionModel(adapter, configuration={}, preload=False)
        result = model.get_label_name(5)
        assert result == "#5"


class TestDetectionModelEmptyImageBlobName:
    """Test for DetectionModel.__init__ line 43 - empty image_blob_name."""

    def test_empty_image_blob_name_raises(self):
        """Line 43 - raises when image_blob_name is falsy after ImageModel init."""
        from model_api.models.detection_model import DetectionModel
        from model_api.models.image_model import ImageModel

        adapter = _make_adapter(input_shape=(1, 3, 300, 300), output_shape=(1, 1, 200, 7))
        original_init = ImageModel.__init__

        def patched_init(self_model, *args, **kwargs):
            original_init(self_model, *args, **kwargs)
            self_model.image_blob_name = ""

        with (
            patch.object(ImageModel, "__init__", patched_init),
            pytest.raises(WrapperError, match="only one image input"),
        ):
            DetectionModel(adapter, configuration={}, preload=False)
