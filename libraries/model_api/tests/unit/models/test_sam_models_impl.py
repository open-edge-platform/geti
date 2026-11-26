#
# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#

"""Unit tests for SAMImageEncoder and SAMDecoder."""

from __future__ import annotations

from dataclasses import dataclass, field
from unittest.mock import MagicMock

import numpy as np
from model_api.adapters.inference_adapter import InferenceAdapter

rng = np.random.default_rng(0)

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


# ---------------------------------------------------------------------------
# Adapter factories
# ---------------------------------------------------------------------------


def _make_encoder_adapter():
    adapter = MagicMock(spec=InferenceAdapter)
    adapter.get_input_layers.return_value = {
        "image": FakeMetadata(shape=[1, 3, 1024, 1024], layout="NCHW"),
    }
    adapter.get_output_layers.return_value = {
        "image_embeddings": FakeMetadata(shape=[1, 256, 64, 64]),
    }
    adapter.get_rt_info.side_effect = _RT_INFO_ERROR
    adapter.embed_preprocessing = MagicMock()
    adapter.load_model.return_value = None
    return adapter


def _make_decoder_adapter():
    adapter = MagicMock(spec=InferenceAdapter)
    adapter.get_input_layers.return_value = {
        "image_embeddings": FakeMetadata(shape=[1, 256, 64, 64]),
        "point_coords": FakeMetadata(shape=[1, 2, 2]),
        "point_labels": FakeMetadata(shape=[1, 2]),
        "mask_input": FakeMetadata(shape=[1, 1, 256, 256]),
        "has_mask_input": FakeMetadata(shape=[1, 1]),
        "orig_size": FakeMetadata(shape=[1, 2]),
    }
    adapter.get_output_layers.return_value = {
        "upscaled_masks": FakeMetadata(shape=[1, 4, 1024, 1024]),
        "iou_predictions": FakeMetadata(shape=[1, 4]),
        "low_res_masks": FakeMetadata(shape=[1, 4, 256, 256]),
        "scores": FakeMetadata(shape=[1, 4]),
    }
    adapter.get_rt_info.side_effect = _RT_INFO_ERROR
    adapter.embed_preprocessing = MagicMock()
    adapter.load_model.return_value = None
    return adapter


# ---------------------------------------------------------------------------
# SAMImageEncoder tests
# ---------------------------------------------------------------------------


class TestSAMImageEncoder:
    def _build(self):
        from model_api.models.sam_models import SAMImageEncoder

        adapter = _make_encoder_adapter()
        return SAMImageEncoder(adapter, configuration={}, preload=False)

    def test_init_output_name(self):
        model = self._build()
        assert model.output_name == "image_embeddings"

    def test_preprocess_adds_resize_type(self):
        model = self._build()
        meta = {}
        _, updated_meta = model.preprocess({"image": np.zeros((1, 3, 1024, 1024))}, meta)
        assert "resize_type" in updated_meta

    def test_postprocess_returns_output(self):
        model = self._build()
        data = rng.random((1, 256, 64, 64)).astype(np.float32)
        result = model.postprocess({"image_embeddings": data}, {})
        np.testing.assert_array_equal(result, data)

    def test_parameters_has_image_size(self):
        from model_api.models.sam_models import SAMImageEncoder

        params = SAMImageEncoder.parameters()
        assert "image_size" in params


# ---------------------------------------------------------------------------
# SAMDecoder tests
# ---------------------------------------------------------------------------


class TestSAMDecoder:
    def _build(self):
        from model_api.models.sam_models import SAMDecoder

        adapter = _make_decoder_adapter()
        return SAMDecoder(adapter, configuration={}, preload=False)

    def test_init_mask_input_shape(self):
        model = self._build()
        assert model.mask_input.shape == (1, 1, 256, 256)

    def test_init_has_mask_input_shape(self):
        model = self._build()
        assert model.has_mask_input.shape == (1, 1)

    def test_parameters_keys(self):
        from model_api.models.sam_models import SAMDecoder

        params = SAMDecoder.parameters()
        for key in ("image_size", "mask_threshold", "embed_dim", "embedded_processing"):
            assert key in params, f"Missing parameter: {key}"

    def test_get_outputs(self):
        model = self._build()
        assert model._get_outputs() == "upscaled_masks"  # noqa: SLF001

    def test_base_preprocess_bboxes(self):
        model = self._build()
        bbox = np.array([10, 20, 100, 200], dtype=np.float32)
        inputs = {
            "bboxes": [bbox],
            "points": None,
            "labels": {"bboxes": [1], "points": None},
            "orig_size": [512, 512],
        }
        result = model.base_preprocess(inputs)
        assert len(result) == 1
        np.testing.assert_array_equal(result[0]["point_labels"].flatten(), [2, 3])

    def test_base_preprocess_points(self):
        model = self._build()
        point = np.array([50, 60], dtype=np.float32)
        inputs = {
            "bboxes": None,
            "points": [point],
            "labels": {"bboxes": None, "points": [0]},
            "orig_size": [512, 512],
        }
        result = model.base_preprocess(inputs)
        assert len(result) == 1
        np.testing.assert_array_equal(result[0]["point_labels"].flatten(), [1])

    def test_base_preprocess_mixed(self):
        model = self._build()
        bbox = np.array([0, 0, 50, 50], dtype=np.float32)
        point = np.array([25, 25], dtype=np.float32)
        inputs = {
            "bboxes": [bbox],
            "points": [point],
            "labels": {"bboxes": [0], "points": [1]},
            "orig_size": [256, 256],
        }
        result = model.base_preprocess(inputs)
        assert len(result) == 2

    def test_apply_coords_scaling(self):
        model = self._build()
        coords = np.array([[[100.0, 200.0]]], dtype=np.float32)
        result = model.apply_coords(coords, (500, 500))
        scale = 1024 / 500
        expected_x = 100.0 * scale
        expected_y = 200.0 * scale
        np.testing.assert_allclose(result[0, 0, 0], expected_x, rtol=1e-3)
        np.testing.assert_allclose(result[0, 0, 1], expected_y, rtol=1e-3)

    def test_get_preprocess_shape_landscape(self):
        model = self._build()
        h, w = model._get_preprocess_shape(500, 1000, 1024)  # noqa: SLF001
        assert w == 1024
        assert h < w

    def test_get_preprocess_shape_portrait(self):
        model = self._build()
        h, w = model._get_preprocess_shape(1000, 500, 1024)  # noqa: SLF001
        assert h == 1024
        assert w < h

    def test_get_preprocess_shape_square(self):
        model = self._build()
        h, w = model._get_preprocess_shape(800, 800, 1024)  # noqa: SLF001
        assert h == 1024
        assert w == 1024

    def test_check_io_number_noop(self):
        model = self._build()
        # Should not raise
        model._check_io_number(6, 4)  # noqa: SLF001
        model._check_io_number((1, 2, 3), (1, 2))  # noqa: SLF001

    def test_get_inputs(self):
        model = self._build()
        image_blob_names, image_info_blob_names = model._get_inputs()  # noqa: SLF001
        assert len(image_blob_names) == 6
        assert image_info_blob_names == []

    def test_postprocess(self):
        model = self._build()
        scores = np.array([[0.3, 0.8, -0.1, 1.5]])
        upscaled = rng.random((1, 4, 64, 64)).astype(np.float32)
        outputs = {
            "scores": scores,
            "upscaled_masks": upscaled.copy(),
            "iou_predictions": np.array([[0.9, 0.8, 0.7, 0.6]]),
            "low_res_masks": rng.random((1, 4, 16, 16)).astype(np.float32),
        }
        result = model.postprocess(outputs, {})
        # scores clipped to [0,1]
        assert "hard_prediction" in result
        assert "soft_prediction" in result
        # hard_prediction is boolean-like: threshold is 0.0 by default
        assert result["hard_prediction"].dtype == bool
        # soft_prediction spatial dims match hard_prediction
        assert result["soft_prediction"].shape[-2:] == result["hard_prediction"].shape[-2:]
