# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

import numpy as np
import pytest
from model_api.models.result import DetectionResult, InstanceSegmentationResult
from model_api.models.result.segmentation import Contour
from model_api.models.utils import (
    OutputTransform,
    ResizeMetadata,
    add_rotated_rects,
    clip_detections,
    get_contours,
    is_softmaxed,
    load_labels,
    softmax,
    top_k,
)

# --- ResizeMetadata ---


def test_resize_metadata_standard():
    meta = ResizeMetadata.compute(640, 480, 320, 240, "standard")
    assert meta.inverted_scale_x == pytest.approx(2.0)
    assert meta.inverted_scale_y == pytest.approx(2.0)
    assert meta.pad_left == 0
    assert meta.pad_top == 0


def test_resize_metadata_fit_to_window():
    meta = ResizeMetadata.compute(800, 600, 400, 400, "fit_to_window")
    # max(800/400, 600/400) = max(2.0, 1.5) = 2.0
    assert meta.inverted_scale_x == pytest.approx(2.0)
    assert meta.inverted_scale_y == pytest.approx(2.0)
    assert meta.pad_left == 0
    assert meta.pad_top == 0


def test_resize_metadata_fit_to_window_letterbox():
    meta = ResizeMetadata.compute(800, 600, 400, 400, "fit_to_window_letterbox")
    assert meta.inverted_scale_x == pytest.approx(2.0)
    assert meta.inverted_scale_y == pytest.approx(2.0)
    assert meta.pad_left == 0
    # pad_top = (400 - round(600/2.0)) // 2 = (400 - 300) // 2 = 50
    assert meta.pad_top == 50


def test_resize_metadata_to_dict():
    meta = ResizeMetadata(inverted_scale_x=1.5, inverted_scale_y=2.0, pad_left=10, pad_top=20)
    d = meta.to_dict()
    assert d["inverted_scale_x"] == 1.5
    assert d["pad_top"] == 20


def test_resize_metadata_from_dict():
    d = {"inverted_scale_x": 1.5, "inverted_scale_y": 2.0, "pad_left": 10, "pad_top": 20}
    meta = ResizeMetadata.from_dict(d)
    assert meta.inverted_scale_x == 1.5
    assert meta.pad_top == 20


def test_resize_metadata_from_dict_defaults():
    d = {"inverted_scale_x": 1.0, "inverted_scale_y": 1.0}
    meta = ResizeMetadata.from_dict(d)
    assert meta.pad_left == 0
    assert meta.pad_top == 0


# --- softmax ---


def test_softmax():
    logits = np.array([1.0, 2.0, 3.0])
    result = softmax(logits)
    assert result.shape == (3,)
    assert np.sum(result) == pytest.approx(1.0, abs=1e-5)
    assert result[2] > result[1] > result[0]


# --- top_k ---


def test_top_k():
    arr = np.array([[1, 5, 3, 2, 4]])
    result = top_k(arr, k=3, axis=1)
    assert result.values.shape == (1, 3)  # noqa: PD011
    assert result.values[0, 0] == 5  # noqa: PD011
    assert result.indices[0, 0] == 1


# --- is_softmaxed ---


def test_is_softmaxed_true():
    arr = np.array([[0.2, 0.3, 0.5], [0.1, 0.6, 0.3]])
    assert is_softmaxed(arr, axis=1) is True


def test_is_softmaxed_false():
    arr = np.array([[1.0, 2.0, 3.0]])
    assert is_softmaxed(arr, axis=1) is False


def test_is_softmaxed_negative():
    arr = np.array([[-0.1, 0.5, 0.6]])
    assert is_softmaxed(arr, axis=1) is False


# --- clip_detections ---


def test_clip_detections():
    bboxes = np.array([[-5, -10, 150, 200]], dtype=np.float32)
    labels = np.array([0])
    det = DetectionResult(bboxes=bboxes, labels=labels)
    clip_detections(det, size=(100, 120))
    assert det.bboxes[0, 0] == 0
    assert det.bboxes[0, 1] == 0
    assert det.bboxes[0, 2] == 120
    assert det.bboxes[0, 3] == 100


# --- OutputTransform ---


def test_output_transform_no_resolution():
    ot = OutputTransform(input_size=(100, 200), output_resolution=None)
    img = np.zeros((100, 200, 3), dtype=np.uint8)
    result = ot.resize(img)
    np.testing.assert_array_equal(result, img)


def test_output_transform_with_resolution():
    ot = OutputTransform(input_size=(100, 200), output_resolution=(100, 200))
    assert ot.output_resolution == (100, 200)


def test_output_transform_scale():
    ot = OutputTransform(input_size=(100, 200), output_resolution=(200, 400))
    scaled = ot.scale((50, 100))
    assert scaled[0] == 50
    assert scaled[1] == 100


def test_output_transform_resize_with_scaling():
    # Use output_resolution larger than input to trigger actual resizing
    ot = OutputTransform(input_size=(100, 100), output_resolution=(300, 300))
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    result = ot.resize(img)
    assert result.shape[0] > 100


def test_output_transform_resize_different_size():
    ot = OutputTransform(input_size=(100, 200), output_resolution=(50, 100))
    img = np.zeros((200, 400, 3), dtype=np.uint8)  # different from input_size
    result = ot.resize(img)
    assert result.shape != (200, 400, 3)


# --- load_labels ---


def test_load_labels(request):
    label_file = Path(request.fspath).parent / "test_labels_file.txt"
    label_file.write_text("cat\ndog\nbird\n")
    try:
        labels = load_labels(str(label_file))
        assert labels == ["cat", "dog", "bird"]
    finally:
        label_file.unlink()


# --- add_rotated_rects ---


def test_add_rotated_rects():
    bboxes = np.array([[0, 0, 20, 20]], dtype=np.float32)
    labels = np.array([0], dtype=np.int32)
    masks = np.zeros((1, 30, 30), dtype=np.uint8)
    masks[0, 5:15, 5:15] = 1
    inst = InstanceSegmentationResult(
        bboxes=bboxes,
        labels=labels,
        masks=masks,
        scores=np.array([0.9]),
        label_names=["obj"],
        saliency_map=[np.ones((3, 3))],
    )
    rotated = add_rotated_rects(inst)
    assert len(rotated.rotated_rects) == 1
    _center, _size, angle = rotated.rotated_rects[0]
    assert 0 < angle <= 90


def test_add_rotated_rects_empty_mask():
    bboxes = np.array([[0, 0, 20, 20]], dtype=np.float32)
    labels = np.array([0], dtype=np.int32)
    masks = np.zeros((1, 30, 30), dtype=np.uint8)  # empty mask
    inst = InstanceSegmentationResult(
        bboxes=bboxes,
        labels=labels,
        masks=masks,
        saliency_map=[np.array([])],
    )
    rotated = add_rotated_rects(inst)
    assert rotated.rotated_rects[0] == ((0, 0), (0, 0), 0)


# --- Contour ---


def test_contour_str():
    c = Contour(label="tree", probability=0.75, shape=[(0, 0), (1, 0), (1, 1), (0, 1)])
    assert "tree" in str(c)
    assert "0.750" in str(c)


def test_contour_repr():
    c = Contour(label="tree", probability=0.75, shape=[(0, 0), (1, 0)])
    assert repr(c) == str(c)


def test_get_contours():
    bboxes = np.array([[0, 0, 20, 20]], dtype=np.float32)
    labels = np.array([0], dtype=np.int32)
    # Create a mask with a single connected component
    masks = np.zeros((1, 30, 30), dtype=np.uint8)
    masks[0, 5:15, 5:15] = 1
    inst = InstanceSegmentationResult(
        bboxes=bboxes,
        labels=labels,
        masks=masks,
        scores=np.array([0.9]),
        label_names=["obj"],
        saliency_map=[np.ones((3, 3))],
    )
    contours = get_contours(inst)
    assert len(contours) == 1
    assert contours[0].label == "obj"
    assert contours[0].probability == 0.9


# --- add_rotated_rects angle adjustment (lines 134-135) ---


def test_add_rotated_rects_angle_above_90():
    """Test angle normalization when angle > 90."""
    bboxes = np.array([[10, 20, 30, 40]], dtype=np.float32)
    labels = np.array([0], dtype=np.int32)
    scores = np.array([0.9], dtype=np.float32)
    masks = [np.eye(20, dtype=np.uint8) * 255]
    inst = InstanceSegmentationResult(
        bboxes=bboxes,
        labels=labels,
        masks=masks,
        scores=scores,
        label_names=["obj"],
        saliency_map=[np.ones((3, 3))],
    )
    result = add_rotated_rects(inst)
    assert len(result.rotated_rects) == 1


# --- get_contours error case (lines 166-167) ---


def test_get_contours_multiple_contours_raises():
    """Test that multiple contours from a single mask raises RuntimeError."""
    bboxes = np.array([[0, 0, 100, 100]], dtype=np.float32)
    labels = np.array([0], dtype=np.int32)
    scores = np.array([0.9], dtype=np.float32)
    # Create a mask with two disconnected regions
    mask = np.zeros((100, 100), dtype=np.uint8)
    mask[10:20, 10:20] = 1
    mask[50:60, 50:60] = 1
    masks = [mask]
    inst = InstanceSegmentationResult(
        bboxes=bboxes,
        labels=labels,
        masks=masks,
        scores=scores,
        label_names=["obj"],
        saliency_map=[np.ones((3, 3))],
    )
    with pytest.raises(RuntimeError, match="findContours"):
        get_contours(inst)


# --- OutputTransform.resize with different sizes (line 205) ---


def test_output_transform_resize_changed_size():
    """Test resize when current size differs from input size."""
    ot = OutputTransform((100, 100), (200, 200))
    img = np.zeros((50, 50, 3), dtype=np.uint8)
    resized = ot.resize(img)
    assert resized.shape[0] != 50 or resized.shape[1] != 50
