# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

import numpy as np
import pytest


def _make_mock_httpclient():
    """Create a mock tritonclient.http module."""
    mock_module = MagicMock()
    mock_infer_input = MagicMock()
    mock_module.InferInput.return_value = mock_infer_input
    return mock_module


def _make_mock_client(model_ready=True):
    """Create a mock Triton HTTP client."""
    client = MagicMock()
    client.is_model_ready.return_value = model_ready
    client.get_model_metadata.return_value = {
        "inputs": [
            {"name": "input", "shape": [1, 3, 224, 224], "datatype": "FP32"},
        ],
        "outputs": [
            {"name": "output", "shape": [1, 1000], "datatype": "FP32"},
        ],
        "rt_info": {"model_info": {"task": "classification"}},
    }
    return client


@pytest.fixture
def ovms_adapter():
    """Create an OVMSAdapter with mocked tritonclient."""
    mock_httpclient = _make_mock_httpclient()
    mock_client = _make_mock_client()
    mock_httpclient.InferenceServerClient.return_value = mock_client

    mock_tritonclient = MagicMock()
    mock_tritonclient.http = mock_httpclient

    patcher = patch.dict(
        sys.modules,
        {"tritonclient": mock_tritonclient, "tritonclient.http": mock_httpclient},
    )
    patcher.start()

    from model_api.adapters.ovms_adapter import OVMSAdapter

    adapter = OVMSAdapter("localhost:9000/v2/models/test_model/versions/1")
    adapter._mock_client = mock_client  # noqa: SLF001
    adapter._mock_httpclient = mock_httpclient  # noqa: SLF001
    yield adapter
    patcher.stop()


class TestOVMSAdapterInit:
    def test_init_success(self, ovms_adapter):
        assert ovms_adapter.model_name == "test_model"
        assert ovms_adapter.model_version == "1"

    def test_init_model_not_ready(self):
        mock_httpclient = _make_mock_httpclient()
        mock_client = _make_mock_client(model_ready=False)
        mock_httpclient.InferenceServerClient.return_value = mock_client

        mock_tritonclient = MagicMock()
        mock_tritonclient.http = mock_httpclient

        with patch.dict(sys.modules, {"tritonclient": mock_tritonclient, "tritonclient.http": mock_httpclient}):
            from model_api.adapters.ovms_adapter import OVMSAdapter

            with pytest.raises(RuntimeError, match="not accessible"):
                OVMSAdapter("localhost:9000/v2/models/bad_model")


class TestOVMSAdapterLayers:
    def test_get_input_layers(self, ovms_adapter):
        inputs = ovms_adapter.get_input_layers()
        assert "input" in inputs
        assert inputs["input"].precision == "FP32"
        assert inputs["input"].shape == [1, 3, 224, 224]

    def test_get_output_layers(self, ovms_adapter):
        outputs = ovms_adapter.get_output_layers()
        assert "output" in outputs
        assert outputs["output"].precision == "FP32"


class TestOVMSAdapterInference:
    def test_infer_sync(self, ovms_adapter):
        mock_result = MagicMock()
        mock_result.as_numpy.return_value = np.zeros((1, 1000), dtype=np.float32)
        ovms_adapter._mock_client.infer.return_value = mock_result  # noqa: SLF001

        result = ovms_adapter.infer_sync(
            {"input": np.zeros((1, 3, 224, 224), dtype=np.float32)},
        )
        assert "output" in result

    def test_infer_sync_dtype_cast(self, ovms_adapter):
        """Test input data type casting."""
        mock_result = MagicMock()
        mock_result.as_numpy.return_value = np.zeros((1, 1000), dtype=np.float32)
        ovms_adapter._mock_client.infer.return_value = mock_result  # noqa: SLF001

        result = ovms_adapter.infer_sync(
            {"input": np.zeros((1, 3, 224, 224), dtype=np.float64)},
        )
        assert "output" in result

    def test_infer_sync_list_input(self, ovms_adapter):
        """Test list input conversion to numpy array."""
        mock_result = MagicMock()
        mock_result.as_numpy.return_value = np.zeros((1, 1000), dtype=np.float32)
        ovms_adapter._mock_client.infer.return_value = mock_result  # noqa: SLF001

        result = ovms_adapter.infer_sync(
            {"input": [[[[0.0] * 224] * 224] * 3]},
        )
        assert "output" in result

    def test_infer_sync_unknown_input_raises(self, ovms_adapter):
        with pytest.raises(ValueError, match="Input data does not match"):
            ovms_adapter.infer_sync({"unknown_input": np.zeros((1, 3, 224, 224))})

    def test_infer_sync_unsupported_precision_raises(self, ovms_adapter):
        ovms_adapter.inputs["input"].precision = "UNSUPPORTED_TYPE"
        with pytest.raises(ValueError, match="Unsupported input precision"):
            ovms_adapter.infer_sync(
                {"input": np.zeros((1, 3, 224, 224), dtype=np.float32)},
            )

    def test_infer_async(self, ovms_adapter):
        mock_result = MagicMock()
        mock_result.as_numpy.return_value = np.zeros((1, 1000), dtype=np.float32)
        ovms_adapter._mock_client.infer.return_value = mock_result  # noqa: SLF001

        cb = MagicMock()
        ovms_adapter.set_callback(cb)

        ovms_adapter.infer_async(
            {"input": np.zeros((1, 3, 224, 224), dtype=np.float32)},
            "callback_data",
        )
        cb.assert_called_once()


class TestOVMSAdapterMethods:
    def test_set_callback(self, ovms_adapter):
        cb = MagicMock()
        ovms_adapter.set_callback(cb)
        assert ovms_adapter.callback_fn is cb

    def test_is_ready(self, ovms_adapter):
        assert ovms_adapter.is_ready() is True

    def test_load_model(self, ovms_adapter):
        ovms_adapter.load_model()

    def test_get_model(self, ovms_adapter):
        result = ovms_adapter.get_model()
        assert result is ovms_adapter.client

    def test_await_all(self, ovms_adapter):
        ovms_adapter.await_all()

    def test_await_any(self, ovms_adapter):
        ovms_adapter.await_any()

    def test_get_raw_result(self, ovms_adapter):
        result = ovms_adapter.get_raw_result({})
        assert result is None

    def test_embed_preprocessing(self, ovms_adapter):
        ovms_adapter.embed_preprocessing(
            layout="NCHW",
            resize_mode="standard",
            interpolation_mode="LINEAR",
            target_shape=(224, 224),
            pad_value=0,
        )

    def test_reshape_model_raises(self, ovms_adapter):
        with pytest.raises(NotImplementedError, match="does not support model reshaping"):
            ovms_adapter.reshape_model({"input": [1, 3, 128, 128]})

    def test_get_rt_info(self, ovms_adapter):
        result = ovms_adapter.get_rt_info(["model_info", "task"])
        assert result.astype(str) == "classification"

    def test_update_model_info_raises(self, ovms_adapter):
        with pytest.raises(NotImplementedError, match="does not support updating"):
            ovms_adapter.update_model_info({"task": "detection"})

    def test_save_model_raises(self, ovms_adapter):
        with pytest.raises(NotImplementedError, match="does not support saving"):
            ovms_adapter.save_model("output.xml")
