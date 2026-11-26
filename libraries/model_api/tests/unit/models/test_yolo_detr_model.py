# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for the native YOLO-DETR ModelAPI wrapper."""

from __future__ import annotations

from dataclasses import dataclass, field
from unittest.mock import MagicMock

import numpy as np
import pytest
from model_api.adapters.inference_adapter import InferenceAdapter
from model_api.models import YOLODETR, Model
from model_api.models.result import DetectionResult

_RT_INFO_ERROR = RuntimeError(
    "Cannot get runtime attribute. Path to runtime attribute is incorrect.",
)


@dataclass
class FakeMetadata:
    names: set = field(default_factory=set)
    shape: list = field(default_factory=list)
    layout: str = ""
    precision: str = "f32"
    type: str = ""
    meta: dict = field(default_factory=dict)


def _make_adapter(input_shape=(1, 3, 640, 640), output_shape=(1, 10, 6)):
    adapter = MagicMock(spec=InferenceAdapter)
    adapter.get_input_layers.return_value = {
        "image": FakeMetadata(shape=list(input_shape), layout="NCHW"),
    }
    adapter.get_output_layers.return_value = {
        "output": FakeMetadata(shape=list(output_shape)),
    }
    adapter.get_rt_info.side_effect = _RT_INFO_ERROR
    adapter.embed_preprocessing = MagicMock()
    adapter.load_model.return_value = None
    return adapter


class TestYOLODETRInit:
    def test_accepts_native_output_shape(self):
        model = YOLODETR(_make_adapter(), configuration={})

        assert model.params.resize_type == "fit_to_window_letterbox"
        assert model.params.confidence_threshold == 0.5
        assert model.params.nms_execute is False

    @pytest.mark.parametrize("output_shape", [(1, 10, 5), (1, 10, 7), (1, 10)])
    def test_rejects_invalid_output_shape(self, output_shape):
        with pytest.raises(Exception, match="output"):
            YOLODETR(_make_adapter(output_shape=output_shape), configuration={})

    def test_rejects_wrong_batch_dimension(self):
        with pytest.raises(Exception, match="first output dimension"):
            YOLODETR(_make_adapter(output_shape=(2, 10, 6)), configuration={})

    def test_postprocess_rejects_multiple_outputs(self):
        model = YOLODETR(_make_adapter(), configuration={})
        output = np.zeros((1, 10, 6), dtype=np.float32)

        with pytest.raises(Exception, match="expect 1 output"):
            model.postprocess({"output1": output, "output2": output}, {"original_shape": (640, 640, 3)})

    def test_postprocess_rejects_wrong_output_shape(self):
        model = YOLODETR(_make_adapter(), configuration={})

        with pytest.raises(Exception, match="shape \\[1, N, 6\\]"):
            model.postprocess({"output": np.zeros((2, 10, 6))}, {"original_shape": (640, 640, 3)})

    def test_factory_resolves_wrapper(self):
        assert Model.get_model_class("YOLODETR") is YOLODETR


class TestYOLODETRPostprocess:
    def test_converts_filters_and_labels_detections(self):
        model = YOLODETR(
            _make_adapter(),
            configuration={"confidence_threshold": 0.5, "labels": ["cat", "dog"]},
        )
        output = np.array(
            [
                [0.5, 0.5, 0.2, 0.4, 0.9, 1],
                [0.2, 0.2, 0.1, 0.1, 0.4, 0],
            ],
            dtype=np.float32,
        )[None]

        result = model.postprocess({"output": output}, {"original_shape": (640, 640, 3)})

        assert isinstance(result, DetectionResult)
        np.testing.assert_array_equal(result.bboxes, [[256, 192, 384, 448]])
        np.testing.assert_array_equal(result.labels, [1])
        np.testing.assert_allclose(result.scores, [0.9])
        assert result.label_names == ["dog"]

    def test_empty_output_has_stable_shapes(self):
        model = YOLODETR(_make_adapter(), configuration={"confidence_threshold": 0.99})
        output = np.zeros((1, 10, 6), dtype=np.float32)

        result = model.postprocess({"output": output}, {"original_shape": (640, 640, 3)})

        assert result.bboxes.shape == (0, 4)
        assert result.labels.shape == (0,)
        assert result.scores.shape == (0,)

    def test_nms_can_be_enabled_explicitly(self):
        model = YOLODETR(
            _make_adapter(),
            configuration={"confidence_threshold": 0.1, "nms_execute": True, "iou_threshold": 0.5},
        )
        output = np.array(
            [
                [0.5, 0.5, 0.4, 0.4, 0.9, 0],
                [0.5, 0.5, 0.4, 0.4, 0.8, 0],
            ],
            dtype=np.float32,
        )[None]

        result = model.postprocess({"output": output}, {"original_shape": (640, 640, 3)})

        assert len(result) == 1
