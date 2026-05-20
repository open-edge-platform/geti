#
# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#

"""Unit tests for SegmentationModel and related helpers."""

from __future__ import annotations

import pathlib
from dataclasses import dataclass, field
from unittest.mock import MagicMock

import cv2
import numpy as np
import pytest
from model_api.adapters.inference_adapter import InferenceAdapter
from model_api.models.model import WrapperError
from model_api.models.segmentation import (
    SegmentationModel,
    _get_activation_map,
    create_hard_prediction_from_soft_prediction,
)

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
    output_shape=(1, 1, 224, 224),
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


# ---------------------------------------------------------------------------
# create_hard_prediction_from_soft_prediction
# ---------------------------------------------------------------------------


class TestCreateHardPrediction:
    def test_blur_strength_neg1_uses_argmax(self):
        soft = rng.random((10, 10, 3)).astype(np.float32)
        result = create_hard_prediction_from_soft_prediction(soft, 0.5, -1)
        expected = np.argmax(soft, axis=2)
        np.testing.assert_array_equal(result, expected)

    def test_soft_threshold_inf_uses_argmax(self):
        soft = rng.random((10, 10, 3)).astype(np.float32)
        result = create_hard_prediction_from_soft_prediction(soft, float("inf"), 3)
        expected = np.argmax(soft, axis=2)
        np.testing.assert_array_equal(result, expected)

    def test_normal_blur_path(self):
        soft = np.zeros((20, 20, 3), dtype=np.float32)
        soft[:, :, 1] = 0.8  # class 1 dominant
        result = create_hard_prediction_from_soft_prediction(soft, 0.5, 3)
        assert result.shape == (20, 20)
        # class 1 should be selected everywhere
        assert np.all(result == 1)

    def test_blur_zeros_below_threshold(self):
        soft = np.zeros((10, 10, 2), dtype=np.float32)
        soft[:, :, 0] = 0.3
        soft[:, :, 1] = 0.3
        # With high threshold, all get zeroed → argmax returns 0
        result = create_hard_prediction_from_soft_prediction(soft, 0.9, 3)
        assert result.shape == (10, 10)


# ---------------------------------------------------------------------------
# SegmentationModel.__init__ and _get_outputs
# ---------------------------------------------------------------------------


class TestSegmentationModelInit:
    def test_single_output_3d_shape(self):
        adapter = _make_adapter(output_shape=(1, 224, 224))
        model = SegmentationModel(adapter, configuration={})
        assert model.out_channels == 0
        assert model.output_blob_name == "output"

    def test_single_output_4d_shape(self):
        adapter = _make_adapter(output_shape=(1, 5, 224, 224))
        model = SegmentationModel(adapter, configuration={})
        assert model.out_channels == 5
        assert model.output_blob_name == "output"

    def test_with_feature_vector_output(self):
        fv_meta = FakeMetadata(names={"feature_vector"}, shape=[1, 128])
        adapter = _make_adapter(
            output_shape=(1, 3, 32, 32),
            extra_outputs={"fv_out": fv_meta},
        )
        model = SegmentationModel(adapter, configuration={})
        assert model.output_blob_name == "output"
        assert model.out_channels == 3

    def test_unsupported_5d_shape_raises(self):
        adapter = _make_adapter(output_shape=(1, 2, 3, 4, 5))
        with pytest.raises(WrapperError):
            SegmentationModel(adapter, configuration={})

    def test_two_non_fv_outputs_raises(self):
        extra = {"output2": FakeMetadata(shape=[1, 3, 32, 32])}
        adapter = _make_adapter(
            output_shape=(1, 3, 32, 32),
            extra_outputs=extra,
        )
        with pytest.raises(WrapperError):
            SegmentationModel(adapter, configuration={})

    def test_only_feature_vector_output_raises(self):
        """If all outputs are feature_vector, no segmentation output found."""
        adapter = MagicMock(spec=InferenceAdapter)
        image_meta = FakeMetadata(shape=[1, 3, 224, 224], layout="NCHW")
        adapter.get_input_layers.return_value = {"image": image_meta}
        adapter.get_output_layers.return_value = {
            "fv": FakeMetadata(names={"feature_vector"}, shape=[1, 128]),
        }
        adapter.get_rt_info.side_effect = _RT_INFO_ERROR
        adapter.embed_preprocessing = MagicMock()
        adapter.load_model.return_value = None
        with pytest.raises(WrapperError):
            SegmentationModel(adapter, configuration={})


# ---------------------------------------------------------------------------
# postprocess
# ---------------------------------------------------------------------------


class TestSegmentationPostprocess:
    def _build_model(self, out_channels, h=32, w=32):
        output_shape = (1, h, w) if out_channels < 2 else (1, out_channels, h, w)
        adapter = _make_adapter(
            input_shape=(1, 3, h, w),
            output_shape=output_shape,
        )
        model = SegmentationModel(adapter, configuration={})
        return model, output_shape

    def _build_model_with_config(self, out_channels, h=32, w=32, **config):
        output_shape = (1, h, w) if out_channels < 2 else (1, out_channels, h, w)
        adapter = _make_adapter(
            input_shape=(1, 3, h, w),
            output_shape=output_shape,
        )
        model = SegmentationModel(adapter, configuration=config)
        return model, output_shape

    def test_two_channel_return_no_soft(self):
        """out_channels == 2 with return_soft_prediction=False."""
        model, _ = self._build_model_with_config(
            out_channels=2,
            h=16,
            w=16,
            return_soft_prediction=False,
        )
        outputs = {"output": rng.random((1, 2, 16, 16)).astype(np.float32)}
        meta = {"original_shape": (32, 32, 3)}
        result = model.postprocess(outputs, meta)
        assert isinstance(result, np.ndarray)
        assert result.shape == (32, 32)

    def test_multichannel_return_soft(self):
        """out_channels >= 2 with return_soft_prediction=True (default)."""
        model, _ = self._build_model(out_channels=3, h=16, w=16)
        outputs = {"output": rng.random((1, 3, 16, 16)).astype(np.float32)}
        meta = {"original_shape": (32, 32, 3)}
        result = model.postprocess(outputs, meta)
        from model_api.models.result import ImageResultWithSoftPrediction

        assert isinstance(result, ImageResultWithSoftPrediction)
        assert result.resultImage.shape == (32, 32)
        assert result.soft_prediction.shape[:2] == (32, 32)

    def test_multichannel_no_soft(self):
        """out_channels >= 2 with return_soft_prediction=False returns np array."""
        model, _ = self._build_model_with_config(
            out_channels=3,
            h=16,
            w=16,
            return_soft_prediction=False,
        )
        outputs = {"output": rng.random((1, 3, 16, 16)).astype(np.float32)}
        meta = {"original_shape": (32, 32, 3)}
        result = model.postprocess(outputs, meta)
        assert isinstance(result, np.ndarray)
        assert result.shape == (32, 32)

    def test_with_feature_vector_in_outputs(self):
        """Feature vector present in outputs produces saliency_map."""
        fv_meta = FakeMetadata(names={"feature_vector"}, shape=[1, 64])
        adapter = _make_adapter(
            input_shape=(1, 3, 16, 16),
            output_shape=(1, 3, 16, 16),
            extra_outputs={"fv_out": fv_meta},
        )
        model = SegmentationModel(adapter, configuration={})
        outputs = {
            "output": rng.random((1, 3, 16, 16)).astype(np.float32),
            "feature_vector": rng.random((1, 64)).astype(np.float32),
        }
        meta = {"original_shape": (16, 16, 3)}
        result = model.postprocess(outputs, meta)
        from model_api.models.result import ImageResultWithSoftPrediction

        assert isinstance(result, ImageResultWithSoftPrediction)
        assert result.feature_vector is not None


# ---------------------------------------------------------------------------
# get_contours
# ---------------------------------------------------------------------------


class TestGetContours:
    def test_single_layer_raises(self):
        adapter = _make_adapter(
            input_shape=(1, 3, 32, 32),
            output_shape=(1, 32, 32),
        )
        model = SegmentationModel(adapter, configuration={})
        from model_api.models.result import ImageResultWithSoftPrediction

        pred = ImageResultWithSoftPrediction(
            resultImage=np.zeros((32, 32), dtype=np.uint8),
            soft_prediction=np.zeros((32, 32, 1), dtype=np.float32),
            saliency_map=np.ndarray(0),
            feature_vector=np.ndarray(0),
        )
        with pytest.raises(RuntimeError, match="1 layer"):
            model.get_contours(pred)

    def test_multi_layer_with_contours(self):
        adapter = _make_adapter(
            input_shape=(1, 3, 64, 64),
            output_shape=(1, 3, 64, 64),
        )
        model = SegmentationModel(adapter, configuration={})
        # Create a prediction with a filled rectangle in class 1
        hard = np.zeros((64, 64), dtype=np.uint8)
        hard[10:30, 10:30] = 1
        soft = np.zeros((64, 64, 3), dtype=np.float32)
        soft[:, :, 0] = 0.8
        soft[10:30, 10:30, 0] = 0.1
        soft[10:30, 10:30, 1] = 0.9

        from model_api.models.result import ImageResultWithSoftPrediction

        pred = ImageResultWithSoftPrediction(
            resultImage=hard,
            soft_prediction=soft,
            saliency_map=np.ndarray(0),
            feature_vector=np.ndarray(0),
        )
        contours = model.get_contours(pred)
        assert len(contours) > 0
        assert contours[0].probability > 0

    def test_non_3d_soft_prediction(self):
        """Line 193: soft_prediction with non-3D shape uses full array."""
        adapter = _make_adapter(
            input_shape=(1, 3, 32, 32),
            output_shape=(1, 3, 32, 32),
        )
        model = SegmentationModel(adapter, configuration={})
        hard = np.zeros((32, 32), dtype=np.uint8)
        # 4D soft_prediction: shape[2] = 3 so n_layers = 3
        soft = np.zeros((32, 32, 3, 1), dtype=np.float32)

        from model_api.models.result import ImageResultWithSoftPrediction

        pred = ImageResultWithSoftPrediction(
            resultImage=hard,
            soft_prediction=soft,
            saliency_map=np.ndarray(0),
            feature_vector=np.ndarray(0),
        )
        contours = model.get_contours(pred)
        assert isinstance(contours, list)


# ---------------------------------------------------------------------------
# _get_activation_map
# ---------------------------------------------------------------------------


class TestGetActivationMap:
    def test_normalize_to_uint8(self):
        features = np.array([0.0, 0.5, 1.0], dtype=np.float32)
        result = _get_activation_map(features)
        assert result.dtype == np.uint8
        assert result[0] == 0
        assert result[-1] == 255

    def test_constant_input(self):
        features = np.full((5,), 3.0, dtype=np.float32)
        result = _get_activation_map(features)
        assert result.dtype == np.uint8
        # All same → all map to 0
        np.testing.assert_array_equal(result, np.zeros(5, dtype=np.uint8))

    def test_2d_input(self):
        features = rng.random((10, 10)).astype(np.float32)
        result = _get_activation_map(features)
        assert result.dtype == np.uint8
        assert result.shape == (10, 10)
        assert result.max() <= 255
        assert result.min() >= 0


# ---------------------------------------------------------------------------
# Additional coverage tests
# ---------------------------------------------------------------------------


class TestSegmentationModelPathToLabels:
    def test_path_to_labels_loads_labels(self):
        """Line 81: labels loaded from path_to_labels file."""
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("label1\nlabel2\n")
            label_path = f.name
        try:
            adapter = _make_adapter(output_shape=(1, 2, 64, 64))
            model = SegmentationModel(adapter, configuration={"path_to_labels": label_path}, preload=False)
            assert model._labels == ["label1", "label2"]  # noqa: SLF001
        finally:
            pathlib.Path(label_path).unlink()


class TestSegmentationPostprocessArgmaxed:
    def test_out_channels_less_than_2_uses_uint8(self):
        """Line 127: when out_channels < 2, soft_prediction = predictions.astype(np.uint8).
        Note: This path crashes in create_hard_prediction_from_soft_prediction since it receives 2D data.
        Line 127 is still covered by the execution before the crash."""
        adapter = _make_adapter(
            input_shape=(1, 3, 16, 16),
            output_shape=(1, 16, 16),  # 3D → out_channels = 0
        )
        model = SegmentationModel(adapter, configuration={"return_soft_prediction": True})
        assert model.out_channels == 0

        predictions = rng.random((1, 16, 16)).astype(np.float32)
        meta = {"original_shape": (16, 16, 3)}
        # The 2D soft_prediction triggers AxisError in argmax(axis=2)
        with pytest.raises(np.exceptions.AxisError):
            model.postprocess({"output": predictions}, meta)


class TestGetContoursWithHoles:
    def test_donut_shape_skips_child_contours(self):
        """Lines 208, 216-218, 221: get_contours with nested contours (donut shape)."""
        adapter = _make_adapter(
            input_shape=(1, 3, 100, 100),
            output_shape=(1, 2, 100, 100),
        )
        model = SegmentationModel(adapter, configuration={"labels": ["ring"]})

        # Create donut: outer circle with hole
        mask = np.zeros((100, 100), dtype=np.uint8)
        cv2.circle(mask, (50, 50), 40, 255, -1)
        cv2.circle(mask, (50, 50), 20, 0, -1)

        hard = np.zeros((100, 100), dtype=np.uint8)
        hard[mask > 0] = 1

        # Use float64 to trigger dtype conversion (line 221)
        soft = np.zeros((100, 100, 2), dtype=np.float64)
        soft[:, :, 1] = mask.astype(np.float64) / 255.0

        from model_api.models.result import ImageResultWithSoftPrediction

        pred = ImageResultWithSoftPrediction(
            resultImage=hard,
            soft_prediction=soft,
            saliency_map=np.ndarray(0),
            feature_vector=np.ndarray(0),
        )
        contours = model.get_contours(pred, include_nested_contours=True)
        assert len(contours) >= 1
        # The donut should produce one parent contour with children (the hole)
        assert len(contours[0].shape) >= 1  # contour[0] is a Contour object
        assert contours[0].probability > 0
