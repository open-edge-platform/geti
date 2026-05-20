#
# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from model_api.models.instance_segmentation import (
    DETRInstanceSegmentation,
    InstanceSegmentationModel,
    MaskRCNNModel,
    _full_image_mask_postprocess,
    _segm_postprocess,
)
from model_api.models.result import InstanceSegmentationResult


class TestFullImageMaskPostprocess:
    """Tests for _full_image_mask_postprocess (used by DETRInstanceSegmentation)."""

    def test_resizes_to_target_dimensions(self):
        mask = np.ones((96, 96), dtype=np.float32)
        result = _full_image_mask_postprocess(mask, im_h=480, im_w=640)
        assert result.shape == (480, 640)

    def test_threshold_applied(self):
        mask = np.full((96, 96), 0.3, dtype=np.float32)
        result = _full_image_mask_postprocess(mask, im_h=100, im_w=100)
        assert result.max() == 0

        mask_above = np.full((96, 96), 0.7, dtype=np.float32)
        result_above = _full_image_mask_postprocess(mask_above, im_h=100, im_w=100)
        assert result_above.min() == 1

    def test_output_dtype_is_uint8(self):
        mask = np.ones((96, 96), dtype=np.float32)
        result = _full_image_mask_postprocess(mask, im_h=200, im_w=300)
        assert result.dtype == np.uint8

    def test_preserves_spatial_pattern(self):
        """A mask with left half filled should still have left half filled after resize."""
        mask = np.zeros((96, 96), dtype=np.float32)
        mask[:, :48] = 1.0
        result = _full_image_mask_postprocess(mask, im_h=200, im_w=200)
        left_half_mean = result[:, :90].mean()
        right_half_mean = result[:, 110:].mean()
        assert left_half_mean > 0.9
        assert right_half_mean < 0.1

    def test_non_square_input_mask(self):
        mask = np.ones((64, 128), dtype=np.float32)
        result = _full_image_mask_postprocess(mask, im_h=300, im_w=400)
        assert result.shape == (300, 400)

    def test_single_pixel_mask(self):
        mask = np.array([[0.8]], dtype=np.float32)
        result = _full_image_mask_postprocess(mask, im_h=10, im_w=10)
        assert result.shape == (10, 10)
        assert result.min() == 1


class TestFullImageVsCropPostprocess:
    """Verify that full-image postprocess differs from per-box-crop postprocess for full-image masks."""

    def test_full_image_mask_not_shifted(self):
        """A centered full-image mask should remain centered with full-image postprocess,
        but would be incorrectly placed at the box position with per-box-crop postprocess."""
        im_h, im_w = 480, 640
        mask = np.zeros((96, 96), dtype=np.float32)
        center_y, center_x = 48, 48
        mask[center_y - 10 : center_y + 10, center_x - 10 : center_x + 10] = 1.0

        full_result = _full_image_mask_postprocess(mask, im_h=im_h, im_w=im_w)

        box = np.array([100, 100, 300, 300])
        crop_result = _segm_postprocess(box, mask, im_h=im_h, im_w=im_w)

        # Full-image postprocess: mask center should be near image center
        full_ys, full_xs = np.where(full_result > 0)
        full_center_y = full_ys.mean()
        full_center_x = full_xs.mean()
        assert abs(full_center_y - im_h / 2) < im_h * 0.1
        assert abs(full_center_x - im_w / 2) < im_w * 0.1

        # Crop postprocess: mask center should be near box center (200, 200)
        crop_ys, crop_xs = np.where(crop_result > 0)
        crop_center_y = crop_ys.mean()
        crop_center_x = crop_xs.mean()
        assert abs(crop_center_y - 200) < 50
        assert abs(crop_center_x - 200) < 50


def _make_model(cls):
    """Create an instance segmentation model instance with mocked adapter."""
    with patch.object(cls, "__init__", lambda self, *a, **kw: None):
        m = object.__new__(cls)

    m.output_blob_name = {"boxes": "boxes", "labels": "labels", "masks": "masks"}
    m.is_segmentoly = False
    m.orig_width = 432
    m.orig_height = 432
    m.outputs = {"boxes": MagicMock(), "labels": MagicMock(), "masks": MagicMock()}
    m.params = SimpleNamespace(
        resize_type="standard",
        confidence_threshold=0.3,
        labels=["background", "horse"],
        nms_execute=True,
        agnostic_nms=False,
        iou_threshold=0.5,
        nms_max_predictions=200,
        postprocess_semantic_masks=True,
    )
    return m


def _make_outputs(boxes, labels, masks):
    """Helper to create outputs dict in the format expected by postprocess."""
    return {"boxes": boxes, "labels": labels, "masks": masks}


def _make_meta(original_h=480, original_w=640):
    """Helper to create metadata dict."""
    return {"original_shape": (original_h, original_w, 3), "resized_shape": (432, 432, 3)}


class TestDETRInstanceSegmentationPostprocess:
    """Tests for DETRInstanceSegmentation.postprocess method."""

    @pytest.fixture()
    def model(self):
        return _make_model(DETRInstanceSegmentation)

    def test_basic_postprocess(self, model):
        """Single detection with full-image mask."""
        boxes = np.array([[100, 100, 300, 300, 0.9]], dtype=np.float32)
        labels = np.array([0], dtype=np.int64)
        masks = np.ones((1, 96, 96), dtype=np.float32)

        result = model.postprocess(_make_outputs(boxes, labels, masks), _make_meta())

        assert isinstance(result, InstanceSegmentationResult)
        assert len(result.bboxes) == 1
        assert result.masks.shape[1:] == (480, 640)
        assert result.masks[0].max() == 1

    def test_batch_dimension_squeezed(self, model):
        """Outputs with batch dimension [1, N, ...] should be handled."""
        boxes = np.array([[[200, 150, 400, 350, 0.8]]], dtype=np.float32)
        labels = np.array([[0]], dtype=np.int64)
        masks = np.ones((1, 1, 96, 96), dtype=np.float32)

        result = model.postprocess(_make_outputs(boxes, labels, masks), _make_meta())

        assert isinstance(result, InstanceSegmentationResult)
        assert len(result.bboxes) == 1

    def test_confidence_threshold_filters(self, model):
        """Detections below confidence threshold should be filtered out."""
        boxes = np.array(
            [[100, 100, 300, 300, 0.9], [50, 50, 200, 200, 0.1]],
            dtype=np.float32,
        )
        labels = np.array([0, 0], dtype=np.int64)
        masks = np.ones((2, 96, 96), dtype=np.float32)

        result = model.postprocess(_make_outputs(boxes, labels, masks), _make_meta())

        assert len(result.bboxes) == 1
        assert result.scores[0] > 0.3

    def test_empty_detections(self, model):
        """No detections above threshold should return empty result."""
        boxes = np.array([[100, 100, 300, 300, 0.1]], dtype=np.float32)
        labels = np.array([0], dtype=np.int64)
        masks = np.ones((1, 96, 96), dtype=np.float32)

        result = model.postprocess(_make_outputs(boxes, labels, masks), _make_meta())

        assert len(result.bboxes) == 0
        assert result.masks.shape == (0, 16, 16)

    def test_labels_incremented(self, model):
        """Non-segmentoly models should have labels incremented by 1."""
        boxes = np.array([[100, 100, 300, 300, 0.9]], dtype=np.float32)
        labels = np.array([0], dtype=np.int64)
        masks = np.ones((1, 96, 96), dtype=np.float32)

        result = model.postprocess(_make_outputs(boxes, labels, masks), _make_meta())

        assert result.labels[0] == 1

    def test_label_names_assigned(self, model):
        """Label names should be resolved from params.labels."""
        boxes = np.array([[100, 100, 300, 300, 0.9]], dtype=np.float32)
        labels = np.array([0], dtype=np.int64)
        masks = np.ones((1, 96, 96), dtype=np.float32)

        result = model.postprocess(_make_outputs(boxes, labels, masks), _make_meta())

        assert result.label_names == ["horse"]

    def test_mask_uses_full_image_not_crop(self, model):
        """Verify masks are resized to full image dims, not placed at box position."""
        mask = np.zeros((96, 96), dtype=np.float32)
        mask[44:52, 44:52] = 1.0

        boxes = np.array([[50, 50, 150, 150, 0.9]], dtype=np.float32)
        labels = np.array([0], dtype=np.int64)
        masks = mask[np.newaxis]

        result = model.postprocess(_make_outputs(boxes, labels, masks), _make_meta(original_h=480, original_w=640))

        # The mask center should be near the IMAGE center (240, 320),
        # not near the BOX center (100, 100 in original coords).
        mask_ys, mask_xs = np.where(result.masks[0] > 0)
        mask_center_y = mask_ys.mean()
        mask_center_x = mask_xs.mean()
        assert abs(mask_center_y - 240) < 30
        assert abs(mask_center_x - 320) < 50

    def test_multiple_detections(self, model):
        """Multiple valid detections should all be returned."""
        boxes = np.array(
            [[50, 50, 200, 200, 0.9], [250, 250, 400, 400, 0.8], [10, 10, 50, 50, 0.7]],
            dtype=np.float32,
        )
        labels = np.array([0, 0, 0], dtype=np.int64)
        masks = np.ones((3, 96, 96), dtype=np.float32)

        result = model.postprocess(_make_outputs(boxes, labels, masks), _make_meta())

        assert len(result.bboxes) == 3


class TestMaskRCNNModelPostprocess:
    """Tests for MaskRCNNModel.postprocess method (per-box-crop masks)."""

    @pytest.fixture()
    def model(self):
        return _make_model(MaskRCNNModel)

    def test_basic_postprocess(self, model):
        """Single detection with per-box mask."""
        boxes = np.array([[100, 100, 300, 300, 0.9]], dtype=np.float32)
        labels = np.array([0], dtype=np.int64)
        masks = np.ones((1, 28, 28), dtype=np.float32)

        result = model.postprocess(_make_outputs(boxes, labels, masks), _make_meta())

        assert isinstance(result, InstanceSegmentationResult)
        assert len(result.bboxes) == 1
        assert result.masks.shape[1:] == (480, 640)

    def test_mask_placed_at_box_position(self, model):
        """Per-box-crop mask should be placed at the box position in the output."""
        mask = np.ones((28, 28), dtype=np.float32)

        boxes = np.array([[200, 200, 400, 400, 0.9]], dtype=np.float32)
        labels = np.array([0], dtype=np.int64)
        masks = mask[np.newaxis]

        result = model.postprocess(_make_outputs(boxes, labels, masks), _make_meta())

        # Mask should be concentrated around the box area, not the full image
        mask_ys, mask_xs = np.where(result.masks[0] > 0)
        # Box in original coords (after rescaling from 432 model input to 640x480 original)
        # box [200, 200, 400, 400] * (640/432, 480/432) ~ [296, 222, 593, 444]
        assert mask_ys.mean() > 200  # not at image top
        mask_center_x = mask_xs.mean()
        # Should NOT be at image center (240, 320) but shifted toward box position
        assert mask_center_x > 350


class TestClassHierarchy:
    """Tests for the InstanceSegmentationModel class hierarchy."""

    def test_detr_model_class_attribute(self):
        assert DETRInstanceSegmentation.__model__ == "DETRInstSeg"

    def test_maskrcnn_model_class_attribute(self):
        assert MaskRCNNModel.__model__ == "MaskRCNN"

    def test_detr_inherits_from_base(self):
        assert issubclass(DETRInstanceSegmentation, InstanceSegmentationModel)

    def test_maskrcnn_inherits_from_base(self):
        assert issubclass(MaskRCNNModel, InstanceSegmentationModel)

    def test_detr_does_not_inherit_from_maskrcnn(self):
        assert not issubclass(DETRInstanceSegmentation, MaskRCNNModel)

    def test_maskrcnn_does_not_inherit_from_detr(self):
        assert not issubclass(MaskRCNNModel, DETRInstanceSegmentation)

    def test_base_class_defines_abstract_hook(self):
        """InstanceSegmentationModel defines _postprocess_single_mask as the extension point."""
        assert hasattr(InstanceSegmentationModel, "_postprocess_single_mask")
        # Both subclasses must provide their own implementation (not the base version)
        base_method = getattr(InstanceSegmentationModel, "_postprocess_single_mask")
        assert getattr(MaskRCNNModel, "_postprocess_single_mask") is not base_method
        assert getattr(DETRInstanceSegmentation, "_postprocess_single_mask") is not base_method
