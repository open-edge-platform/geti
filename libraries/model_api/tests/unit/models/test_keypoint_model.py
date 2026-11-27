#
# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#

"""Unit tests for KeypointDetectionModel and related helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from unittest.mock import MagicMock

import numpy as np
import pytest
from model_api.adapters.inference_adapter import InferenceAdapter
from model_api.models.keypoint_detection import (
    KeypointDetectionModel,
    TopDownKeypointDetectionPipeline,
    _decode_simcc,
    _get_simcc_maximum,
)
from model_api.models.model import WrapperError
from model_api.models.result import DetectedKeypoints, DetectionResult

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
    input_shape=(1, 3, 256, 192),
    output_shapes=None,
    layout="NCHW",
    rt_info=None,
):
    adapter = MagicMock(spec=InferenceAdapter)
    image_meta = FakeMetadata(shape=list(input_shape), layout=layout)
    inputs = {"image": image_meta}

    if output_shapes is None:
        output_shapes = {
            "simcc_x": (1, 17, 384),
            "simcc_y": (1, 17, 512),
        }

    outputs = {}
    for name, shape in output_shapes.items():
        outputs[name] = FakeMetadata(shape=list(shape))

    adapter.get_input_layers.return_value = inputs
    adapter.get_output_layers.return_value = outputs
    adapter.get_rt_info.side_effect = rt_info or _RT_INFO_ERROR
    adapter.embed_preprocessing = MagicMock()
    adapter.load_model.return_value = None
    return adapter


# ---------------------------------------------------------------------------
# _get_simcc_maximum
# ---------------------------------------------------------------------------


class TestGetSimccMaximum:
    def test_2d_input(self):
        """K x W input produces K x 2 locs and K vals."""
        K, Wx, Wy = 5, 10, 12
        simcc_x = rng.random((K, Wx)).astype(np.float32)
        simcc_y = rng.random((K, Wy)).astype(np.float32)
        locs, vals = _get_simcc_maximum(simcc_x, simcc_y)
        assert locs.shape == (K, 2)
        assert vals.shape == (K,)

    def test_3d_input_batch(self):
        """N x K x W input produces N x K x 2 locs and N x K vals."""
        N, K, Wx, Wy = 2, 5, 10, 12
        simcc_x = rng.random((N, K, Wx)).astype(np.float32)
        simcc_y = rng.random((N, K, Wy)).astype(np.float32)
        locs, vals = _get_simcc_maximum(simcc_x, simcc_y)
        assert locs.shape == (N, K, 2)
        assert vals.shape == (N, K)

    def test_apply_softmax(self):
        """With apply_softmax=True, values should be in (0, 1)."""
        K, Wx, Wy = 3, 8, 8
        simcc_x = rng.random((K, Wx)).astype(np.float32) * 10
        simcc_y = rng.random((K, Wy)).astype(np.float32) * 10
        locs, vals = _get_simcc_maximum(simcc_x, simcc_y, apply_softmax=True)
        assert locs.shape == (K, 2)
        assert np.all(vals >= 0)
        assert np.all(vals <= 1)

    def test_1d_input_raises(self):
        simcc_x = np.array([1.0, 2.0, 3.0])
        simcc_y = np.array([1.0, 2.0, 3.0])
        with pytest.raises(ValueError, match="Invalid shape"):
            _get_simcc_maximum(simcc_x, simcc_y)

    def test_mismatched_ndim_raises(self):
        simcc_x = rng.random((3, 10)).astype(np.float32)
        simcc_y = rng.random((1, 3, 10)).astype(np.float32)
        with pytest.raises(ValueError, match="Invalid shape"):
            _get_simcc_maximum(simcc_x, simcc_y)

    def test_negative_values_set_to_minus_one(self):
        """When max val <= 0, location should be set to -1."""
        K, W = 2, 5
        simcc_x = np.full((K, W), -1.0, dtype=np.float32)
        simcc_y = np.full((K, W), -1.0, dtype=np.float32)
        locs, _ = _get_simcc_maximum(simcc_x, simcc_y)
        assert np.all(locs == -1)

    def test_argmax_correctness(self):
        """Location should correspond to argmax of the input."""
        simcc_x = np.array([[0.0, 0.0, 5.0, 0.0]], dtype=np.float32)  # argmax=2
        simcc_y = np.array([[0.0, 3.0, 0.0, 0.0]], dtype=np.float32)  # argmax=1
        locs, _ = _get_simcc_maximum(simcc_x, simcc_y)
        assert locs[0, 0] == 2.0
        assert locs[0, 1] == 1.0


# ---------------------------------------------------------------------------
# _decode_simcc
# ---------------------------------------------------------------------------


class TestDecodeSimcc:
    def test_without_softmax(self):
        K, Wx, Wy = 5, 20, 20
        simcc_x = rng.random((K, Wx)).astype(np.float32)
        simcc_y = rng.random((K, Wy)).astype(np.float32)
        kps, scores = _decode_simcc(simcc_x, simcc_y, apply_softmax=False)
        # 2D input → unsqueezed to 3D
        assert kps.ndim == 3
        assert kps.shape == (1, K, 2)
        assert scores.ndim == 2
        assert scores.shape == (1, K)

    def test_with_softmax(self):
        K, Wx, Wy = 5, 20, 20
        simcc_x = rng.random((K, Wx)).astype(np.float32) * 5
        simcc_y = rng.random((K, Wy)).astype(np.float32) * 5
        kps, scores = _decode_simcc(simcc_x, simcc_y, apply_softmax=True)
        assert kps.ndim == 3
        # With softmax, scores should be in [0, 1]
        assert np.all(scores >= 0)
        assert np.all(scores <= 1)

    def test_3d_input_no_unsqueeze(self):
        N, K, Wx, Wy = 2, 5, 20, 20
        simcc_x = rng.random((N, K, Wx)).astype(np.float32)
        simcc_y = rng.random((N, K, Wy)).astype(np.float32)
        kps, scores = _decode_simcc(simcc_x, simcc_y)
        assert kps.shape == (N, K, 2)
        assert scores.shape == (N, K)

    def test_split_ratio_division(self):
        """Keypoints should be divided by simcc_split_ratio."""
        K = 3
        # Create simple inputs with known max positions
        simcc_x = np.zeros((K, 10), dtype=np.float32)
        simcc_y = np.zeros((K, 10), dtype=np.float32)
        simcc_x[:, 4] = 1.0  # argmax at 4
        simcc_y[:, 6] = 1.0  # argmax at 6
        kps, _ = _decode_simcc(simcc_x, simcc_y, simcc_split_ratio=2.0)
        np.testing.assert_allclose(kps[0, :, 0], 2.0)  # 4 / 2.0
        np.testing.assert_allclose(kps[0, :, 1], 3.0)  # 6 / 2.0


# ---------------------------------------------------------------------------
# KeypointDetectionModel.__init__
# ---------------------------------------------------------------------------


class TestKeypointDetectionModelInit:
    def test_init_valid(self):
        adapter = _make_adapter()
        model = KeypointDetectionModel(adapter, configuration={})
        assert model is not None

    def test_wrong_input_count_raises(self):
        adapter = _make_adapter()
        # Add extra input
        inputs = adapter.get_input_layers.return_value
        inputs["extra"] = FakeMetadata(shape=[1, 3, 256, 192], layout="NCHW")
        with pytest.raises(WrapperError):
            KeypointDetectionModel(adapter, configuration={})

    def test_wrong_output_count_raises(self):
        adapter = _make_adapter(
            output_shapes={
                "out1": (1, 17, 384),
            },
        )
        with pytest.raises(WrapperError):
            KeypointDetectionModel(adapter, configuration={})


# ---------------------------------------------------------------------------
# KeypointDetectionModel.preprocess
# ---------------------------------------------------------------------------


class TestKeypointDetectionModelPreprocess:
    def test_stores_resize_metadata(self):
        adapter = _make_adapter()
        model = KeypointDetectionModel(adapter, configuration={})
        dict_inputs = {"image": np.zeros((1, 3, 256, 192))}
        meta = {"original_shape": (480, 640, 3)}
        _, result_meta = model.preprocess(dict_inputs, meta)
        assert "resize_info" in result_meta
        info = result_meta["resize_info"]
        assert "kp_scale_h" in info
        assert "kp_scale_w" in info
        assert "pad_left" in info
        assert "pad_top" in info


# ---------------------------------------------------------------------------
# KeypointDetectionModel.postprocess
# ---------------------------------------------------------------------------


class TestKeypointDetectionModelPostprocess:
    def _build_model(self, **config):
        adapter = _make_adapter()
        return KeypointDetectionModel(adapter, configuration=config)

    def test_with_resize_info(self):
        model = self._build_model()
        K = 17
        simcc_x = np.zeros((1, K, 384), dtype=np.float32)
        simcc_y = np.zeros((1, K, 512), dtype=np.float32)
        simcc_x[:, :, 10] = 1.0
        simcc_y[:, :, 20] = 1.0
        outputs = {"simcc_x": simcc_x, "simcc_y": simcc_y}
        meta = {
            "original_shape": (480, 640, 3),
            "resize_info": {
                "kp_scale_h": 2.0,
                "kp_scale_w": 3.0,
                "pad_left": 0,
                "pad_top": 0,
            },
        }
        result = model.postprocess(outputs, meta)
        assert isinstance(result, DetectedKeypoints)
        assert result.keypoints.shape[-1] == 2

    def test_without_resize_info_fallback(self):
        model = self._build_model()
        K = 17
        simcc_x = np.zeros((1, K, 384), dtype=np.float32)
        simcc_y = np.zeros((1, K, 512), dtype=np.float32)
        simcc_x[:, :, 10] = 1.0
        simcc_y[:, :, 20] = 1.0
        outputs = {"simcc_x": simcc_x, "simcc_y": simcc_y}
        meta = {"original_shape": (480, 640, 3)}
        result = model.postprocess(outputs, meta)
        assert isinstance(result, DetectedKeypoints)

    def test_with_padding_offset(self):
        model = self._build_model()
        K = 17
        simcc_x = np.zeros((1, K, 384), dtype=np.float32)
        simcc_y = np.zeros((1, K, 512), dtype=np.float32)
        simcc_x[:, :, 20] = 1.0
        simcc_y[:, :, 30] = 1.0
        outputs = {"simcc_x": simcc_x, "simcc_y": simcc_y}
        pad_left, pad_top = 5, 10
        meta = {
            "original_shape": (480, 640, 3),
            "resize_info": {
                "kp_scale_h": 1.0,
                "kp_scale_w": 1.0,
                "pad_left": pad_left,
                "pad_top": pad_top,
            },
        }
        result = model.postprocess(outputs, meta)
        # Keypoints should have padding subtracted
        # argmax_x=20, argmax_y=30, split_ratio=2 → kp=(10, 15)
        # subtract pad → (10 - 5, 15 - 10) = (5, 5)
        # multiply scale (1.0) → (5, 5)
        expected_x = (20 / 2.0 - pad_left) * 1.0
        expected_y = (30 / 2.0 - pad_top) * 1.0
        np.testing.assert_allclose(result.keypoints[0, 0], expected_x, atol=0.1)
        np.testing.assert_allclose(result.keypoints[0, 1], expected_y, atol=0.1)

    def test_apply_softmax_param(self):
        model = self._build_model(apply_softmax=True)
        K = 17
        simcc_x = rng.random((1, K, 384)).astype(np.float32) * 5
        simcc_y = rng.random((1, K, 512)).astype(np.float32) * 5
        outputs = {"simcc_x": simcc_x, "simcc_y": simcc_y}
        meta = {
            "original_shape": (480, 640, 3),
            "resize_info": {
                "kp_scale_h": 1.0,
                "kp_scale_w": 1.0,
                "pad_left": 0,
                "pad_top": 0,
            },
        }
        result = model.postprocess(outputs, meta)
        assert isinstance(result, DetectedKeypoints)


# ---------------------------------------------------------------------------
# TopDownKeypointDetectionPipeline
# ---------------------------------------------------------------------------


class TestTopDownKeypointDetectionPipeline:
    def test_predict_crop_and_offset(self):
        base_model = MagicMock(spec=KeypointDetectionModel)
        pipeline = TopDownKeypointDetectionPipeline(base_model)

        # Mock infer_batch to return keypoints per crop
        kp1 = DetectedKeypoints(
            keypoints=np.array([[10.0, 20.0], [30.0, 40.0]]),
            scores=np.array([0.9, 0.8]),
        )
        kp2 = DetectedKeypoints(
            keypoints=np.array([[5.0, 5.0]]),
            scores=np.array([0.7]),
        )
        base_model.infer_batch.return_value = [kp1, kp2]

        image = np.zeros((100, 100, 3), dtype=np.uint8)
        det_result = MagicMock(spec=DetectionResult)
        det_result.bboxes = np.array([[10, 20, 50, 60], [30, 40, 70, 80]])

        results = pipeline.predict(image, det_result)
        assert len(results) == 2
        # First detection offset: x1=10, y1=20
        np.testing.assert_allclose(results[0].keypoints[0], [20.0, 40.0])
        # Second detection offset: x1=30, y1=40
        np.testing.assert_allclose(results[1].keypoints[0], [35.0, 45.0])

    def test_predict_crops_delegates(self):
        base_model = MagicMock(spec=KeypointDetectionModel)
        pipeline = TopDownKeypointDetectionPipeline(base_model)
        crops = [np.zeros((50, 50, 3))]
        pipeline.predict_crops(crops)
        base_model.infer_batch.assert_called_once_with(crops)


# ---------------------------------------------------------------------------
# Additional coverage tests
# ---------------------------------------------------------------------------


class TestGetSimccMaximumInvalidShape:
    def test_simcc_y_invalid_ndim_raises(self):
        """Lines 235-236: simcc_y with invalid ndim (1D) raises ValueError."""
        simcc_x = rng.random((5, 10)).astype(np.float32)
        simcc_y = rng.random((50)).astype(np.float32)  # 1D - invalid
        with pytest.raises(ValueError, match="Invalid shape"):
            _get_simcc_maximum(simcc_x, simcc_y)

    def test_simcc_y_4d_raises(self):
        """Lines 235-236: simcc_y with invalid ndim (4D) raises ValueError."""
        simcc_x = rng.random((5, 10)).astype(np.float32)
        simcc_y = rng.random((1, 2, 5, 10)).astype(np.float32)  # 4D - invalid
        with pytest.raises(ValueError, match="Invalid shape"):
            _get_simcc_maximum(simcc_x, simcc_y)
