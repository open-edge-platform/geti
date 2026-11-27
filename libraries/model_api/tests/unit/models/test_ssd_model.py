#
# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#

"""Unit tests for SSD model and its output parsers."""

from __future__ import annotations

from dataclasses import dataclass, field
from unittest.mock import MagicMock

import numpy as np
import pytest
from model_api.adapters.inference_adapter import InferenceAdapter
from model_api.models.result import DetectionResult
from model_api.models.ssd import (
    SSD,
    BoxesLabelsParser,
    MultipleOutputParser,
    SingleOutputParser,
    find_layer_by_name,
)

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
    input_shape=(1, 3, 300, 300),
    output_shape=(1, 1, 100, 7),
    layout="NCHW",
    extra_inputs=None,
    extra_outputs=None,
    rt_info=None,
):
    adapter = MagicMock(spec=InferenceAdapter)
    image_meta = FakeMetadata(shape=list(input_shape), layout=layout)
    inputs = {"image": image_meta}
    if extra_inputs:
        inputs.update(extra_inputs)

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
# find_layer_by_name
# ---------------------------------------------------------------------------


class TestFindLayerByName:
    def test_found(self):
        layers = {"det_bboxes": None, "det_scores": None}
        assert find_layer_by_name("bboxes", layers) == "det_bboxes"

    def test_not_found(self):
        with pytest.raises(ValueError, match="not found"):
            find_layer_by_name("labels", {"bboxes_out": None, "scores_out": None})

    def test_multiple_matches(self):
        layers = {"bboxes_1": None, "bboxes_2": None}
        with pytest.raises(ValueError, match="More than 1"):
            find_layer_by_name("bboxes", layers)


# ---------------------------------------------------------------------------
# SingleOutputParser
# ---------------------------------------------------------------------------


class TestSingleOutputParser:
    def test_init_multiple_outputs_raises(self):
        outputs = {
            "out1": FakeMetadata(shape=[1, 1, 10, 7]),
            "out2": FakeMetadata(shape=[1, 1, 10, 7]),
        }
        with pytest.raises(ValueError, match="only one output"):
            SingleOutputParser(outputs)

    def test_init_wrong_last_dim_raises(self):
        outputs = {"out": FakeMetadata(shape=[1, 1, 10, 5])}
        with pytest.raises(ValueError, match="last dimension"):
            SingleOutputParser(outputs)

    def test_call_parses_correctly(self):
        outputs_meta = {"det_out": FakeMetadata(shape=[1, 1, 3, 7])}
        parser = SingleOutputParser(outputs_meta)

        data = np.array(
            [
                [
                    [
                        [0, 1, 0.9, 0.1, 0.2, 0.3, 0.4],
                        [0, 2, 0.8, 0.5, 0.6, 0.7, 0.8],
                        [0, 0, 0.1, 0.0, 0.0, 0.1, 0.1],
                    ],
                ],
            ],
            dtype=np.float32,
        )
        result = parser({"det_out": data})
        assert isinstance(result, DetectionResult)
        assert len(result.bboxes) == 3
        assert result.labels[0] == 1
        assert result.labels[1] == 2
        np.testing.assert_almost_equal(result.scores[0], 0.9)


# ---------------------------------------------------------------------------
# MultipleOutputParser
# ---------------------------------------------------------------------------


class TestMultipleOutputParser:
    def test_init_and_call(self):
        layers = {
            "det_bboxes": FakeMetadata(shape=[1, 10, 4]),
            "det_scores": FakeMetadata(shape=[1, 10]),
            "det_labels": FakeMetadata(shape=[1, 10]),
        }
        parser = MultipleOutputParser(layers)
        assert parser.bboxes_layer == "det_bboxes"
        assert parser.scores_layer == "det_scores"
        assert parser.labels_layer == "det_labels"

        outputs = {
            "det_bboxes": np.array([[[0.1, 0.2, 0.3, 0.4], [0.5, 0.6, 0.7, 0.8]]]),
            "det_scores": np.array([[0.9, 0.8]]),
            "det_labels": np.array([[1, 2]]),
        }
        result = parser(outputs)
        assert isinstance(result, DetectionResult)
        assert len(result.bboxes) == 2
        np.testing.assert_almost_equal(result.scores[0], 0.9)

    def test_missing_layer_raises(self):
        layers = {
            "det_bboxes": FakeMetadata(shape=[1, 10, 4]),
            "det_scores": FakeMetadata(shape=[1, 10]),
        }
        with pytest.raises(ValueError, match="not found"):
            MultipleOutputParser(layers)


# ---------------------------------------------------------------------------
# BoxesLabelsParser
# ---------------------------------------------------------------------------


class TestBoxesLabelsParser:
    def test_find_layer_bboxes_2d(self):
        layers = {"boxes": FakeMetadata(shape=[100, 5])}
        assert BoxesLabelsParser.find_layer_bboxes_output(layers) == "boxes"

    def test_find_layer_bboxes_3d(self):
        layers = {"boxes": FakeMetadata(shape=[1, 100, 5])}
        assert BoxesLabelsParser.find_layer_bboxes_output(layers) == "boxes"

    def test_find_layer_bboxes_none_found(self):
        layers = {"boxes": FakeMetadata(shape=[100, 4])}
        with pytest.raises(ValueError, match="not found"):
            BoxesLabelsParser.find_layer_bboxes_output(layers)

    def test_find_layer_bboxes_multiple(self):
        layers = {
            "boxes1": FakeMetadata(shape=[100, 5]),
            "boxes2": FakeMetadata(shape=[50, 5]),
        }
        with pytest.raises(ValueError, match="More than 1"):
            BoxesLabelsParser.find_layer_bboxes_output(layers)

    def test_with_labels_layer(self):
        layers = {
            "boxes_out": FakeMetadata(shape=[1, 100, 5]),
            "labels_out": FakeMetadata(shape=[1, 100]),
        }
        parser = BoxesLabelsParser(layers, input_size=(300, 300))
        assert parser.labels_layer == "labels_out"

        bboxes_data = np.zeros((1, 100, 5), dtype=np.float32)
        bboxes_data[0, 0] = [30, 30, 60, 60, 0.9]
        labels_data = np.array([[1] * 100], dtype=np.float32)
        result = parser({"boxes_out": bboxes_data, "labels_out": labels_data})
        assert isinstance(result, DetectionResult)
        assert len(result.bboxes) == 100
        np.testing.assert_almost_equal(result.scores[0], 0.9)

    def test_without_labels_layer_init(self):
        """When labels layer isn't found, parser falls back to default_label."""
        layers = {"det_boxes": FakeMetadata(shape=[1, 50, 5])}
        parser = BoxesLabelsParser(layers, input_size=(300, 300), default_label=5)
        assert parser.labels_layer is None
        assert parser.default_label == 5

    def test_call_with_3d_bboxes(self):
        layers = {
            "boxes": FakeMetadata(shape=[1, 10, 5]),
            "labels_out": FakeMetadata(shape=[1, 10]),
        }
        parser = BoxesLabelsParser(layers, input_size=(300, 300))
        bboxes_data = np.zeros((1, 10, 5), dtype=np.float32)
        bboxes_data[0, 0] = [150, 150, 300, 300, 0.95]
        labels_data = np.zeros((1, 10), dtype=np.float32)
        result = parser({"boxes": bboxes_data, "labels_out": labels_data})
        assert isinstance(result, DetectionResult)
        assert result.bboxes.shape == (10, 4)
        np.testing.assert_almost_equal(result.scores[0], 0.95)


# ---------------------------------------------------------------------------
# SSD.__init__
# ---------------------------------------------------------------------------


class TestSSDInit:
    def test_without_image_info(self):
        adapter = _make_adapter(output_shape=(1, 1, 10, 7))
        model = SSD(adapter, configuration={})
        assert model.image_info_blob_name is None
        assert isinstance(model.output_parser, SingleOutputParser)

    def test_with_image_info(self):
        info_meta = FakeMetadata(names={"image_info"}, shape=[1, 3])
        adapter = _make_adapter(
            output_shape=(1, 1, 10, 7),
            extra_inputs={"im_info": info_meta},
        )
        model = SSD(adapter, configuration={})
        assert model.image_info_blob_name == "im_info"


# ---------------------------------------------------------------------------
# SSD.preprocess
# ---------------------------------------------------------------------------


class TestSSDPreprocess:
    def test_adds_image_info_blob(self):
        info_meta = FakeMetadata(names={"image_info"}, shape=[1, 3])
        adapter = _make_adapter(
            output_shape=(1, 1, 10, 7),
            extra_inputs={"im_info": info_meta},
        )
        model = SSD(adapter, configuration={})
        dict_inputs = {"image": np.zeros((1, 3, 300, 300))}
        meta = {"original_shape": (600, 800, 3)}
        result_inputs, _ = model.preprocess(dict_inputs, meta)
        assert "im_info" in result_inputs
        np.testing.assert_array_equal(
            result_inputs["im_info"],
            [[model.h, model.w, 1]],
        )

    def test_no_image_info_blob(self):
        adapter = _make_adapter(output_shape=(1, 1, 10, 7))
        model = SSD(adapter, configuration={})
        dict_inputs = {"image": np.zeros((1, 3, 300, 300))}
        meta = {"original_shape": (600, 800, 3)}
        result_inputs, _ = model.preprocess(dict_inputs, meta)
        assert "im_info" not in result_inputs


# ---------------------------------------------------------------------------
# SSD.postprocess
# ---------------------------------------------------------------------------


class TestSSDPostprocess:
    def test_full_pipeline(self):
        adapter = _make_adapter(output_shape=(1, 1, 5, 7))
        model = SSD(adapter, configuration={})

        data = np.zeros((1, 1, 5, 7), dtype=np.float32)
        # [image_id, label, score, xmin, ymin, xmax, ymax] - normalized coords
        data[0, 0, 0] = [0, 1, 0.95, 0.1, 0.1, 0.5, 0.5]
        data[0, 0, 1] = [0, 2, 0.80, 0.2, 0.2, 0.6, 0.6]
        data[0, 0, 2] = [0, 0, 0.01, 0.0, 0.0, 0.01, 0.01]  # low score

        outputs = {"output": data}
        meta = {
            "original_shape": (300, 300, 3),
            "resize_info": {
                "inverted_scale_x": 1.0,
                "inverted_scale_y": 1.0,
                "pad_left": 0,
                "pad_top": 0,
            },
        }
        result = model.postprocess(outputs, meta)
        assert isinstance(result, DetectionResult)
        # Low-scoring detections should be filtered
        assert all(s > model.params.confidence_threshold for s in result.scores)


# ---------------------------------------------------------------------------
# SSD._get_output_parser
# ---------------------------------------------------------------------------


class TestSSDGetOutputParser:
    def test_single_output_parser_selected(self):
        adapter = _make_adapter(output_shape=(1, 1, 10, 7))
        model = SSD(adapter, configuration={})
        assert isinstance(model.output_parser, SingleOutputParser)

    def test_multiple_output_parser_selected(self):
        outputs = {
            "det_bboxes": FakeMetadata(shape=[1, 10, 4]),
            "det_scores": FakeMetadata(shape=[1, 10]),
            "det_labels": FakeMetadata(shape=[1, 10]),
        }
        adapter = _make_adapter(extra_outputs=outputs)
        # Override default output to not match single parser
        adapter.get_output_layers.return_value = outputs
        model = SSD(adapter, configuration={})
        assert isinstance(model.output_parser, MultipleOutputParser)

    def test_boxes_labels_parser_selected(self):
        outputs = {"boxes": FakeMetadata(shape=[100, 5])}
        adapter = _make_adapter(extra_outputs=outputs)
        adapter.get_output_layers.return_value = outputs
        model = SSD(adapter, configuration={})
        assert isinstance(model.output_parser, BoxesLabelsParser)

    def test_unsupported_outputs_raises(self):
        outputs = {"some_output": FakeMetadata(shape=[1, 10, 3])}
        adapter = _make_adapter(extra_outputs=outputs)
        adapter.get_output_layers.return_value = outputs
        with pytest.raises(ValueError, match="Unsupported"):
            SSD(adapter, configuration={})


# ---------------------------------------------------------------------------
# Additional coverage tests
# ---------------------------------------------------------------------------


class TestBoxesLabelsParserNoLabelsLayer:
    def test_default_labels_when_no_labels_layer(self):
        """Line 144: default labels used when labels_layer not found."""
        outputs_meta = {"boxes": FakeMetadata(shape=[100, 5])}
        parser = BoxesLabelsParser(outputs_meta, (300, 300))

        bboxes = np.array([[[10, 20, 50, 60, 0.9]]], dtype=np.float32)  # (1, 1, 5)
        result = parser({"boxes": bboxes})
        assert isinstance(result, DetectionResult)
        # Labels should be filled with default_label (0)
        assert result.labels == 0
