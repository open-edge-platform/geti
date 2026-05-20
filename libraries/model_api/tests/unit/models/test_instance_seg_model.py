#
# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#

"""Unit tests for MaskRCNNModel and related helpers."""

from __future__ import annotations

import pathlib
from dataclasses import dataclass, field
from unittest.mock import MagicMock

import numpy as np
import pytest
from model_api.adapters.inference_adapter import InferenceAdapter
from model_api.models.instance_segmentation import (
    MaskRCNNModel,
    _append_xai_names,
    _average_and_normalize,
    _expand_box,
    _segm_postprocess,
)
from model_api.models.model import WrapperError
from model_api.models.result import InstanceSegmentationResult

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
    input_shapes=None,
    output_configs=None,
    layout="NCHW",
    rt_info=None,
):
    """Build a mock InferenceAdapter.

    Args:
        input_shapes: dict of {name: (shape, layout, names_set)} or None for default.
        output_configs: dict of {name: (shape, names_set)} or None for default.
    """
    adapter = MagicMock(spec=InferenceAdapter)

    if input_shapes is None:
        input_shapes = {"image": ((1, 3, 800, 800), layout, set())}

    inputs = {}
    for name, (shape, lay, names_set) in input_shapes.items():
        meta = FakeMetadata(shape=list(shape), layout=lay, names=names_set)
        inputs[name] = meta

    if output_configs is None:
        output_configs = {
            "labels_out": ((100,), set()),
            "boxes_out": ((100, 5), set()),
            "masks_out": ((100, 28, 28), set()),
        }

    outputs = {}
    for name, (shape, names_set) in output_configs.items():
        meta = FakeMetadata(shape=list(shape), names=names_set)
        outputs[name] = meta

    adapter.get_input_layers.return_value = inputs
    adapter.get_output_layers.return_value = outputs
    adapter.get_rt_info.side_effect = rt_info or _RT_INFO_ERROR
    adapter.embed_preprocessing = MagicMock()
    adapter.load_model.return_value = None
    return adapter


# ---------------------------------------------------------------------------
# _average_and_normalize
# ---------------------------------------------------------------------------


class TestAverageAndNormalize:
    def test_empty_maps(self):
        result = _average_and_normalize([])
        assert result == []

    def test_single_map_per_class(self):
        m = np.array([[1.0, 2.0], [3.0, 4.0]])
        result = _average_and_normalize([[m]])
        assert len(result) == 1
        assert result[0].dtype == np.uint8
        assert result[0].max() == 255

    def test_multiple_maps_per_class(self):
        m1 = np.array([[1.0, 0.0], [0.0, 0.0]])
        m2 = np.array([[0.0, 0.0], [0.0, 2.0]])
        result = _average_and_normalize([[m1, m2]])
        assert len(result) == 1
        assert result[0].dtype == np.uint8

    def test_empty_class_produces_empty_ndarray(self):
        result = _average_and_normalize([[]])
        assert len(result) == 1
        assert result[0].size == 0

    def test_mixed_classes(self):
        m = np.ones((3, 3))
        result = _average_and_normalize([[m], []])
        assert len(result) == 2
        assert result[0].dtype == np.uint8
        assert result[1].size == 0


# ---------------------------------------------------------------------------
# _expand_box
# ---------------------------------------------------------------------------


class TestExpandBox:
    def test_identity_scale(self):
        box = np.array([10.0, 20.0, 30.0, 40.0])
        result = _expand_box(box, 1.0)
        np.testing.assert_allclose(result, box)

    def test_double_scale(self):
        box = np.array([0.0, 0.0, 10.0, 10.0])
        result = _expand_box(box, 2.0)
        # center is (5, 5), half-widths become 10, 10
        np.testing.assert_allclose(result, [-5.0, -5.0, 15.0, 15.0])

    def test_half_scale(self):
        box = np.array([0.0, 0.0, 20.0, 20.0])
        result = _expand_box(box, 0.5)
        np.testing.assert_allclose(result, [5.0, 5.0, 15.0, 15.0])


# ---------------------------------------------------------------------------
# _segm_postprocess
# ---------------------------------------------------------------------------


class TestSegmPostprocess:
    def test_mask_resized_to_image(self):
        box = np.array([10, 10, 50, 50])
        raw_mask = np.ones((28, 28), dtype=np.float32)
        result = _segm_postprocess(box, raw_mask, 100, 100)
        assert result.shape == (100, 100)
        assert result.dtype == np.uint8
        # Inside the box region should have non-zero values
        assert result[20, 20] > 0

    def test_mask_outside_box_is_zero(self):
        box = np.array([10, 10, 30, 30])
        raw_mask = np.ones((14, 14), dtype=np.float32)
        result = _segm_postprocess(box, raw_mask, 100, 100)
        assert result[0, 0] == 0
        assert result[99, 99] == 0


# ---------------------------------------------------------------------------
# _append_xai_names
# ---------------------------------------------------------------------------


class TestAppendXaiNames:
    def test_no_xai_outputs(self):
        outputs = {"out1": FakeMetadata()}
        result = {}
        _append_xai_names(outputs, result)
        assert "saliency_map" not in result
        assert "feature_vector" not in result

    def test_with_saliency_map(self):
        outputs = {"saliency_map": FakeMetadata()}
        result = {}
        _append_xai_names(outputs, result)
        assert result["saliency_map"] == "saliency_map"
        assert "feature_vector" not in result

    def test_with_feature_vector(self):
        outputs = {"feature_vector": FakeMetadata()}
        result = {}
        _append_xai_names(outputs, result)
        assert result["feature_vector"] == "feature_vector"
        assert "saliency_map" not in result

    def test_with_both(self):
        outputs = {
            "saliency_map": FakeMetadata(),
            "feature_vector": FakeMetadata(),
        }
        result = {}
        _append_xai_names(outputs, result)
        assert result["saliency_map"] == "saliency_map"
        assert result["feature_vector"] == "feature_vector"


# ---------------------------------------------------------------------------
# MaskRCNNModel.__init__
# ---------------------------------------------------------------------------


class TestMaskRCNNModelInit:
    def test_standard_mode_1d_2d_3d_shapes(self):
        """Standard: 1 input, outputs with 1D labels, 2D boxes, 3D masks."""
        adapter = _make_adapter()
        model = MaskRCNNModel(adapter, configuration={})
        assert not model.is_segmentoly
        assert "labels" in model.output_blob_name
        assert "boxes" in model.output_blob_name
        assert "masks" in model.output_blob_name

    def test_alternative_mode_2d_3d_4d_shapes(self):
        """Alternative: outputs with 2D labels, 3D boxes, 4D masks."""
        adapter = _make_adapter(
            output_configs={
                "labels_out": ((1, 100), set()),
                "boxes_out": ((1, 100, 5), set()),
                "masks_out": ((1, 100, 28, 28), set()),
            },
        )
        model = MaskRCNNModel(adapter, configuration={})
        assert model.output_blob_name["labels"] == "labels_out"
        assert model.output_blob_name["boxes"] == "boxes_out"
        assert model.output_blob_name["masks"] == "masks_out"

    def test_segmentoly_mode_two_inputs(self):
        """Segmentoly mode: 2 inputs with named outputs."""
        adapter = _make_adapter(
            input_shapes={
                "image": ((1, 3, 800, 800), "NCHW", set()),
                "image_info": ((1, 3), "", {"image_info"}),
            },
            output_configs={
                "boxes": ((100, 4), set()),
                "classes": ((100,), set()),
                "scores": ((100,), set()),
                "raw_masks": ((100, 2, 28, 28), set()),
            },
        )
        model = MaskRCNNModel(adapter, configuration={})
        assert model.is_segmentoly
        assert model.output_blob_name["labels"] == "classes"
        assert model.output_blob_name["scores"] == "scores"
        assert model.output_blob_name["masks"] == "raw_masks"

    def test_with_xai_outputs(self):
        """Standard mode with saliency_map and feature_vector outputs."""
        adapter = _make_adapter(
            output_configs={
                "labels_out": ((100,), set()),
                "boxes_out": ((100, 5), set()),
                "masks_out": ((100, 28, 28), set()),
                "saliency_map": ((1, 10, 10), {"saliency_map"}),
                "feature_vector": ((1, 128), {"feature_vector"}),
            },
        )
        model = MaskRCNNModel(adapter, configuration={})
        assert model.output_blob_name.get("saliency_map") == "saliency_map"
        assert model.output_blob_name.get("feature_vector") == "feature_vector"


# ---------------------------------------------------------------------------
# MaskRCNNModel._get_outputs
# ---------------------------------------------------------------------------


class TestMaskRCNNModelGetOutputs:
    def test_error_on_unexpected_outputs(self):
        """Should raise when outputs don't match expected patterns."""
        adapter = _make_adapter(
            output_configs={
                "out1": ((100, 5, 5, 5, 5), set()),
                "out2": ((100, 5, 5, 5, 5), set()),
                "out3": ((100, 5, 5, 5, 5), set()),
            },
        )
        with pytest.raises(WrapperError):
            MaskRCNNModel(adapter, configuration={})

    def test_topk_outputs_are_skipped(self):
        """Outputs starting with TopK should be ignored."""
        adapter = _make_adapter(
            output_configs={
                "labels_out": ((100,), set()),
                "boxes_out": ((100, 5), set()),
                "masks_out": ((100, 28, 28), set()),
                "TopK_something": ((100,), set()),
            },
        )
        model = MaskRCNNModel(adapter, configuration={})
        assert "TopK_something" not in model.output_blob_name.values()


# ---------------------------------------------------------------------------
# MaskRCNNModel.preprocess
# ---------------------------------------------------------------------------


class TestMaskRCNNModelPreprocess:
    def test_standard_preprocess(self):
        adapter = _make_adapter()
        model = MaskRCNNModel(adapter, configuration={})
        dict_inputs = {"image": np.zeros((1, 3, 800, 800))}
        meta = {"resized_shape": (800, 800, 3)}
        result_inputs, _ = model.preprocess(dict_inputs, meta)
        # Non-segmentoly: no image_info added
        assert "image_info" not in result_inputs or len(model.image_info_blob_names) == 0

    def test_segmentoly_preprocess(self):
        adapter = _make_adapter(
            input_shapes={
                "image": ((1, 3, 800, 800), "NCHW", set()),
                "image_info": ((1, 3), "", {"image_info"}),
            },
            output_configs={
                "boxes": ((100, 4), set()),
                "classes": ((100,), set()),
                "scores": ((100,), set()),
                "raw_masks": ((100, 2, 28, 28), set()),
            },
        )
        model = MaskRCNNModel(adapter, configuration={})
        dict_inputs = {"image": np.zeros((1, 3, 800, 800))}
        meta = {"resized_shape": (600, 800, 3)}
        result_inputs, _ = model.preprocess(dict_inputs, meta)
        info_key = model.image_info_blob_names[0]
        assert info_key in result_inputs
        info = result_inputs[info_key]
        np.testing.assert_array_equal(info, [[600, 800, 1]])


# ---------------------------------------------------------------------------
# MaskRCNNModel.postprocess
# ---------------------------------------------------------------------------


class TestMaskRCNNModelPostprocess:
    def _build_standard_model(self, labels=None, confidence=0.5, postprocess_masks=True):
        config = {
            "confidence_threshold": confidence,
            "postprocess_semantic_masks": postprocess_masks,
        }
        if labels is not None:
            config["labels"] = labels
        adapter = _make_adapter()
        return MaskRCNNModel(adapter, configuration=config)

    def _make_meta(self, orig_h=480, orig_w=640):
        return {"original_shape": (orig_h, orig_w, 3)}

    def test_standard_postprocess_basic(self):
        model = self._build_standard_model(
            labels=["bg", "cat", "dog"],
            confidence=0.3,
        )
        n = 3
        labels = np.array([0, 1, 0], dtype=np.int32)
        boxes = np.array(
            [[10, 10, 100, 100, 0.9], [20, 20, 80, 80, 0.8], [30, 30, 60, 60, 0.1]],
            dtype=np.float32,
        )
        masks = np.ones((n, 28, 28), dtype=np.float32)
        outputs = {
            "labels_out": labels,
            "boxes_out": boxes,
            "masks_out": masks,
        }
        result = model.postprocess(outputs, self._make_meta())
        assert isinstance(result, InstanceSegmentationResult)
        # Third detection has score 0.1 < 0.3 threshold, should be filtered
        assert len(result.scores) <= 2

    def test_confidence_filtering(self):
        model = self._build_standard_model(confidence=0.95)
        labels = np.array([0], dtype=np.int32)
        boxes = np.array([[10, 10, 100, 100, 0.5]], dtype=np.float32)
        masks = np.ones((1, 28, 28), dtype=np.float32)
        outputs = {
            "labels_out": labels,
            "boxes_out": boxes,
            "masks_out": masks,
        }
        result = model.postprocess(outputs, self._make_meta())
        assert len(result.scores) == 0

    def test_area_filtering(self):
        """Boxes with area <= 1 should be filtered out."""
        model = self._build_standard_model(confidence=0.0)
        labels = np.array([0], dtype=np.int32)
        # box with zero area
        boxes = np.array([[10, 10, 10, 10, 0.9]], dtype=np.float32)
        masks = np.ones((1, 28, 28), dtype=np.float32)
        outputs = {
            "labels_out": labels,
            "boxes_out": boxes,
            "masks_out": masks,
        }
        result = model.postprocess(outputs, self._make_meta())
        assert len(result.scores) == 0

    def test_label_filtering(self):
        """Labels >= len(labels_list) should be filtered out when labels set."""
        model = self._build_standard_model(
            labels=["bg", "cat"],
            confidence=0.0,
        )
        # label 0 + 1 offset = 1 (valid), label 5 + 1 offset = 6 (invalid)
        labels = np.array([0, 5], dtype=np.int32)
        boxes = np.array(
            [[10, 10, 100, 100, 0.9], [10, 10, 100, 100, 0.9]],
            dtype=np.float32,
        )
        masks = np.ones((2, 28, 28), dtype=np.float32)
        outputs = {
            "labels_out": labels,
            "boxes_out": boxes,
            "masks_out": masks,
        }
        result = model.postprocess(outputs, self._make_meta())
        assert len(result.scores) == 1

    def test_batched_squeeze(self):
        """When outputs have extra batch dim (ndim==2/3/4), they should be squeezed."""
        model = self._build_standard_model(confidence=0.0)
        labels = np.array([[0]], dtype=np.int32)  # 2D
        boxes = np.array([[[10, 10, 100, 100, 0.9]]], dtype=np.float32)  # 3D
        masks = np.ones((1, 1, 28, 28), dtype=np.float32)  # 4D
        outputs = {
            "labels_out": labels,
            "boxes_out": boxes,
            "masks_out": masks,
        }
        result = model.postprocess(outputs, self._make_meta())
        assert isinstance(result, InstanceSegmentationResult)

    def test_segmentoly_postprocess(self):
        """Segmentoly mode: uses scores output, no label offset."""
        adapter = _make_adapter(
            input_shapes={
                "image": ((1, 3, 800, 800), "NCHW", set()),
                "image_info": ((1, 3), "", {"image_info"}),
            },
            output_configs={
                "boxes": ((100, 4), set()),
                "classes": ((100,), set()),
                "scores": ((100,), set()),
                "raw_masks": ((100, 2, 28, 28), set()),
            },
        )
        model = MaskRCNNModel(
            adapter,
            configuration={
                "confidence_threshold": 0.3,
                "labels": ["cat", "dog"],
            },
        )

        n = 2
        labels = np.array([0, 1], dtype=np.int32)
        boxes = np.array(
            [[10, 10, 100, 100], [20, 20, 80, 80]],
            dtype=np.float32,
        )
        scores_arr = np.array([0.9, 0.8], dtype=np.float32)
        masks = np.ones((n, 2, 28, 28), dtype=np.float32)

        # Pad remaining outputs with zeros
        pad_labels = np.zeros(98, dtype=np.int32)
        pad_boxes = np.zeros((98, 4), dtype=np.float32)
        pad_scores = np.zeros(98, dtype=np.float32)
        pad_masks = np.zeros((98, 2, 28, 28), dtype=np.float32)

        outputs = {
            "classes": np.concatenate([labels, pad_labels]),
            "boxes": np.concatenate([boxes, pad_boxes]),
            "scores": np.concatenate([scores_arr, pad_scores]),
            "raw_masks": np.concatenate([masks, pad_masks]),
        }
        meta = {"original_shape": (480, 640, 3)}
        result = model.postprocess(outputs, meta)
        assert isinstance(result, InstanceSegmentationResult)
        # No label offset in segmentoly mode
        assert 0 in result.labels or 1 in result.labels

    def test_postprocess_with_feature_vector(self):
        """With feature_vector output, saliency maps should be aggregated."""
        adapter = _make_adapter(
            output_configs={
                "labels_out": ((100,), set()),
                "boxes_out": ((100, 5), set()),
                "masks_out": ((100, 28, 28), set()),
                "saliency_map": ((1, 10, 10), {"saliency_map"}),
                "feature_vector": ((1, 128), {"feature_vector"}),
            },
        )
        model = MaskRCNNModel(
            adapter,
            configuration={
                "confidence_threshold": 0.3,
                "labels": ["bg", "cat", "dog"],
                "postprocess_semantic_masks": True,
            },
        )

        labels = np.array([0], dtype=np.int32)
        boxes = np.array([[10, 10, 100, 100, 0.9]], dtype=np.float32)
        masks = np.ones((1, 28, 28), dtype=np.float32)
        fv = rng.random((1, 128)).astype(np.float32)

        outputs = {
            "labels_out": labels,
            "boxes_out": boxes,
            "masks_out": masks,
            "feature_vector": fv,
        }
        result = model.postprocess(outputs, {"original_shape": (480, 640, 3)})
        assert isinstance(result, InstanceSegmentationResult)
        assert result.feature_vector is not None

    def test_empty_detections(self):
        """All detections filtered → empty result."""
        model = self._build_standard_model(confidence=1.0)
        labels = np.array([0], dtype=np.int32)
        boxes = np.array([[10, 10, 100, 100, 0.5]], dtype=np.float32)
        masks = np.ones((1, 28, 28), dtype=np.float32)
        outputs = {
            "labels_out": labels,
            "boxes_out": boxes,
            "masks_out": masks,
        }
        result = model.postprocess(outputs, self._make_meta())
        assert len(result.scores) == 0
        assert result.masks.shape[0] == 0


# ---------------------------------------------------------------------------
# Additional coverage tests
# ---------------------------------------------------------------------------


class TestMaskRCNNPathToLabels:
    def test_path_to_labels_loads_labels(self):
        """Line 25: labels loaded from path_to_labels file."""
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("cat\ndog\n")
            label_path = f.name
        try:
            adapter = _make_adapter()
            model = MaskRCNNModel(adapter, configuration={"path_to_labels": label_path}, preload=False)
            assert model._labels == ["cat", "dog"]  # noqa: SLF001
        finally:
            pathlib.Path(label_path).unlink()


class TestMaskRCNNTopKSkip:
    def test_topk_output_is_skipped_first_loop(self):
        """Line 51: outputs starting with 'TopK' skipped in first loop."""
        adapter = _make_adapter(
            output_configs={
                "labels_out": ((100,), set()),
                "boxes_out": ((100, 5), set()),
                "masks_out": ((100, 28, 28), set()),
                "TopK_scores": ((100,), set()),
            },
        )
        model = MaskRCNNModel(adapter, configuration={})
        assert "TopK_scores" not in model.output_blob_name.values()

    def test_topk_output_is_skipped_second_loop(self):
        """Line 67: outputs starting with 'TopK' skipped in second loop (2D/3D/4D pattern)."""
        adapter = _make_adapter(
            output_configs={
                "labels_out": ((1, 100), set()),
                "boxes_out": ((1, 100, 5), set()),
                "masks_out": ((1, 100, 28, 28), set()),
                "TopK_scores": ((1, 100), set()),
            },
        )
        model = MaskRCNNModel(adapter, configuration={})
        assert "TopK_scores" not in model.output_blob_name.values()


class TestMaskRCNNSegmentolyUnexpectedOutput:
    def test_segmentoly_unexpected_shape_raises(self):
        """Line 94: unexpected output in segmentoly mode raises error."""
        adapter = _make_adapter(
            input_shapes={
                "image": ((1, 3, 800, 800), "NCHW", set()),
                "image_info": ((1, 3), "", {"image_info"}),
            },
            output_configs={
                "boxes": ((100, 4), set()),
                "classes": ((100,), set()),
                "scores": ((100,), set()),
                "raw_masks": ((100, 2, 28, 28), set()),
                "unexpected_out": ((5, 5, 5), set()),
            },
        )
        with pytest.raises(WrapperError):
            MaskRCNNModel(adapter, configuration={})


class TestMaskRCNNFeatureVectorWithoutLabels:
    def test_feature_vector_without_labels_raises(self):
        """Line 171: feature_vector output without labels raises error."""
        adapter = _make_adapter(
            output_configs={
                "labels_out": ((100,), set()),
                "boxes_out": ((100, 5), set()),
                "masks_out": ((100, 28, 28), set()),
                "feature_vector": ((1, 128), {"feature_vector"}),
            },
        )
        model = MaskRCNNModel(adapter, configuration={"confidence_threshold": 0.0})

        labels = np.array([0], dtype=np.int32)
        boxes = np.array([[10, 10, 100, 100, 0.9]], dtype=np.float32)
        masks = np.ones((1, 28, 28), dtype=np.float32)
        fv = rng.random((1, 128)).astype(np.float32)

        outputs = {
            "labels_out": labels,
            "boxes_out": boxes,
            "masks_out": masks,
            "feature_vector": fv,
        }
        with pytest.raises(WrapperError, match="labels are empty"):
            model.postprocess(outputs, {"original_shape": (480, 640, 3)})


class TestMaskRCNNNoPostprocessSemanticMasks:
    def test_raw_mask_returned_without_postprocess(self):
        """Line 222: resized_mask = raw_cls_mask when postprocess_semantic_masks=False."""
        adapter = _make_adapter(
            output_configs={
                "labels_out": ((100,), set()),
                "boxes_out": ((100, 5), set()),
                "masks_out": ((100, 28, 28), set()),
            },
        )
        model = MaskRCNNModel(
            adapter,
            configuration={
                "confidence_threshold": 0.0,
                "labels": ["cat", "dog"],
                "postprocess_semantic_masks": False,
            },
        )

        labels = np.array([0], dtype=np.int32)
        boxes = np.array([[10, 10, 100, 100, 0.9]], dtype=np.float32)
        masks = np.ones((1, 28, 28), dtype=np.float32)

        outputs = {
            "labels_out": labels,
            "boxes_out": boxes,
            "masks_out": masks,
        }
        result = model.postprocess(outputs, {"original_shape": (480, 640, 3)})
        assert isinstance(result, InstanceSegmentationResult)
        # Raw mask should be returned without resizing
        assert result.masks[0].shape == (28, 28)
