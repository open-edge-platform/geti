#
# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#

"""Unit tests for AnomalyDetection model."""

from __future__ import annotations

from dataclasses import dataclass, field
from unittest.mock import MagicMock

import numpy as np
import pytest
from model_api.adapters.inference_adapter import InferenceAdapter
from model_api.models.anomaly import AnomalyDetection
from model_api.models.model import WrapperError

rng = np.random.default_rng(0)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_RT_INFO_ERROR = RuntimeError(
    "Cannot get runtime attribute. Path to runtime attribute is incorrect.",
)


@dataclass
class FakeMetadata:
    names: set = field(default_factory=set)
    shape: list = field(default_factory=list)
    layout: str = ""
    precision: str = ""
    type: str = ""
    meta: dict = field(default_factory=dict)


def _make_adapter(
    input_shape=(1, 3, 224, 224),
    output_shape=(1, 1),
    layout="NCHW",
    extra_outputs=None,
    rt_info=None,
):
    adapter = MagicMock(spec=InferenceAdapter)
    image_meta = FakeMetadata(shape=list(input_shape), layout=layout)
    inputs = {"image": image_meta}

    out_meta = FakeMetadata(shape=list(output_shape))
    outputs = {"output": out_meta}
    if extra_outputs:
        outputs.update(extra_outputs)

    adapter.get_input_layers.return_value = inputs
    adapter.get_output_layers.return_value = outputs
    adapter.get_rt_info.side_effect = rt_info or _RT_INFO_ERROR
    adapter.embed_preprocessing = MagicMock()
    adapter.load_model.return_value = None
    adapter.infer_sync.return_value = {"output": np.zeros(output_shape)}
    return adapter


def _make_anomaly_model(output_shape=(1, 1), extra_outputs=None, task="classification", **kwargs):
    adapter = _make_adapter(output_shape=output_shape, extra_outputs=extra_outputs)
    config = {
        "labels": ["Normal", "Anomaly"],
        "image_threshold": 0.5,
        "pixel_threshold": 0.5,
        "normalization_scale": 1.0,
        "task": task,
    }
    config.update(kwargs)
    return AnomalyDetection(adapter, configuration=config)


# ---------------------------------------------------------------------------
# Constructor
# ---------------------------------------------------------------------------


class TestAnomalyDetectionInit:
    def test_single_output(self):
        model = _make_anomaly_model(output_shape=(1, 1))
        assert model is not None

    def test_four_outputs(self):
        extra = {
            "pred_score": FakeMetadata(shape=[1]),
            "pred_label": FakeMetadata(shape=[1]),
            "pred_mask": FakeMetadata(shape=[1, 224, 224]),
        }
        model = _make_anomaly_model(output_shape=(1, 224, 224), extra_outputs=extra)
        assert model is not None

    def test_invalid_output_count_raises(self):
        extra = {f"out{i}": FakeMetadata(shape=[1]) for i in range(5)}
        with pytest.raises(WrapperError):
            _make_anomaly_model(output_shape=(1, 1), extra_outputs=extra)


# ---------------------------------------------------------------------------
# _resize_image (NPU dynamic shape path)
# ---------------------------------------------------------------------------


class TestResizeImage:
    def test_npu_dynamic_shape(self):
        model = _make_anomaly_model()
        model._is_dynamic = True  # noqa: SLF001
        model.inference_adapter.device = "NPU"

        compiled_model = MagicMock()
        input_mock = MagicMock()
        input_mock.get_shape.return_value = [1, 3, 256, 256]
        compiled_model.inputs = [input_mock]
        model.inference_adapter.compiled_model = compiled_model

        image = np.zeros((100, 100, 3), dtype=np.uint8)
        model._resize_image(image)  # noqa: SLF001
        assert not model._is_dynamic  # noqa: SLF001
        assert model.h == 256
        assert model.w == 256

    def test_default_resize(self):
        model = _make_anomaly_model()
        model._is_dynamic = False  # noqa: SLF001
        image = np.zeros((100, 100, 3), dtype=np.uint8)
        resized, _ = model._resize_image(image)  # noqa: SLF001
        assert resized is not None


# ---------------------------------------------------------------------------
# _input_transform
# ---------------------------------------------------------------------------


class TestInputTransform:
    def test_uint8_to_float32(self):
        model = _make_anomaly_model()
        image = np.array([0, 128, 255], dtype=np.uint8)
        result = model._input_transform(image)  # noqa: SLF001
        assert result.dtype == np.float32
        np.testing.assert_allclose(result[0], 0.0, atol=1e-6)
        np.testing.assert_allclose(result[2], 1.0, atol=1e-6)

    def test_float32_passthrough(self):
        model = _make_anomaly_model()
        image = np.array([0.0, 0.5, 1.0], dtype=np.float32)
        result = model._input_transform(image)  # noqa: SLF001
        assert result.dtype == np.float32
        np.testing.assert_array_equal(result, image)


# ---------------------------------------------------------------------------
# postprocess - without anomalib keys
# ---------------------------------------------------------------------------


class TestPostprocessWithoutAnomalibKeys:
    def _meta(self, h=100, w=100):
        return {"original_shape": (h, w, 3)}

    def test_scalar_prediction(self):
        model = _make_anomaly_model()
        # shape=1 triggers scalar path; but code does `assert anomaly_map is not None` after,
        # so scalar-only path actually fails at that assert if no spatial map.
        # The model expects spatial output for mask generation. Test the spatial path.
        spatial = rng.random((1, 1, 32, 32)).astype(np.float32)
        outputs = {"output": spatial}
        result = model.postprocess(outputs, self._meta())
        assert result.pred_label in ["Normal", "Anomaly"]
        assert result.anomaly_map is not None
        assert result.pred_mask is not None

    def test_anomaly_label_above_threshold(self):
        model = _make_anomaly_model()
        spatial = np.ones((1, 1, 32, 32), dtype=np.float32) * 0.9
        outputs = {"output": spatial}
        result = model.postprocess(outputs, self._meta())
        assert result.pred_label == "Anomaly"

    def test_normal_label_below_threshold(self):
        model = _make_anomaly_model()
        spatial = np.ones((1, 1, 32, 32), dtype=np.float32) * 0.1
        outputs = {"output": spatial}
        result = model.postprocess(outputs, self._meta())
        assert result.pred_label == "Normal"
        # Normal score is inverted
        assert result.pred_score > 0.0


# ---------------------------------------------------------------------------
# postprocess - with anomalib keys
# ---------------------------------------------------------------------------


class TestPostprocessWithAnomalibKeys:
    def _meta(self, h=100, w=100):
        return {"original_shape": (h, w, 3)}

    def test_anomalib_format(self):
        model = _make_anomaly_model()
        outputs = {
            "output": np.zeros((1, 1)),
            "pred_score": np.array([0.8]),
            "pred_label": np.array([1]),
            "pred_mask": np.zeros((1, 32, 32), dtype=np.float32),
            "anomaly_map": np.ones((1, 32, 32), dtype=np.float32) * 0.5,
        }
        result = model.postprocess(outputs, self._meta())
        assert result.pred_score == 0.8
        assert result.pred_label == "1"
        assert result.anomaly_map.shape == (100, 100)
        assert result.pred_mask.shape == (100, 100)


# ---------------------------------------------------------------------------
# postprocess - detection task
# ---------------------------------------------------------------------------


class TestPostprocessDetection:
    def _meta(self):
        return {"original_shape": (100, 100, 3)}

    def test_detection_boxes(self):
        model = _make_anomaly_model(task="detection")
        mask_small = np.zeros((32, 32), dtype=np.float32)
        mask_small[5:15, 5:15] = 1.0
        spatial = mask_small.reshape(1, 1, 32, 32)
        outputs = {"output": spatial}
        result = model.postprocess(outputs, self._meta())
        assert result.pred_boxes is not None


# ---------------------------------------------------------------------------
# parameters
# ---------------------------------------------------------------------------


class TestParameters:
    def test_contains_anomaly_and_labels(self):
        params = AnomalyDetection.parameters()
        assert "image_threshold" in params
        assert "pixel_threshold" in params
        assert "normalization_scale" in params
        assert "task" in params
        assert "labels" in params


# ---------------------------------------------------------------------------
# _normalize
# ---------------------------------------------------------------------------


class TestNormalize:
    def test_min_max_normalization(self):
        model = _make_anomaly_model()
        tensor = np.array([0.0, 0.5, 1.0])
        result = model._normalize(tensor, threshold=0.5)  # noqa: SLF001
        assert result[1] == 0.5
        assert np.all(result >= 0)
        assert np.all(result <= 1)

    def test_clipping(self):
        model = _make_anomaly_model()
        tensor = np.array([-10.0, 10.0])
        result = model._normalize(tensor, threshold=0.5)  # noqa: SLF001
        assert np.all(result >= 0)
        assert np.all(result <= 1)


# ---------------------------------------------------------------------------
# _get_boxes
# ---------------------------------------------------------------------------


class TestGetBoxes:
    def test_contour_detection(self):
        mask = np.zeros((100, 100), dtype=np.uint8)
        mask[20:40, 30:60] = 1
        boxes = AnomalyDetection._get_boxes(mask)  # noqa: SLF001
        assert boxes.shape[0] >= 1
        assert boxes.shape[1] == 4
        x1, y1, _, _ = boxes[0]
        assert x1 >= 29
        assert x1 <= 31
        assert y1 >= 19
        assert y1 <= 21

    def test_empty_mask(self):
        mask = np.zeros((100, 100), dtype=np.uint8)
        boxes = AnomalyDetection._get_boxes(mask)  # noqa: SLF001
        assert boxes.shape == (0,)

    def test_multiple_contours(self):
        mask = np.zeros((100, 100), dtype=np.uint8)
        mask[10:20, 10:20] = 1
        mask[60:80, 60:80] = 1
        boxes = AnomalyDetection._get_boxes(mask)  # noqa: SLF001
        assert boxes.shape[0] == 2


class TestPostprocess1DPredictions:
    def test_1d_predictions_hits_assertion(self):
        """Line 107: npred_score = predictions for 1D output (no anomaly_map)."""
        model = _make_anomaly_model()
        outputs = {"output": np.array([0.6], dtype=np.float32)}
        with pytest.raises(AssertionError):
            model.postprocess(outputs, {"original_shape": (100, 100, 3)})
