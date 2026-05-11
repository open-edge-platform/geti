"""Tests for primitives."""

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import numpy as np
import PIL
from model_api.visualizer import BoundingBox, Keypoint, Label, Overlay, Polygon
from PIL import ImageDraw


def test_overlay(mock_image: PIL.Image):
    """Test if the overlay is created correctly."""
    empty_image = PIL.Image.new("RGB", (100, 100))
    expected_image = PIL.Image.blend(empty_image, mock_image, 0.4)
    # Test from image
    overlay = Overlay(mock_image)
    assert overlay.compute(empty_image) == expected_image

    # Test from numpy array
    data = np.zeros((100, 100, 3), dtype=np.uint8)
    data *= 255
    overlay = Overlay(data)
    assert overlay.compute(empty_image) == expected_image


def test_bounding_box(mock_image: PIL.Image):
    """Test if the bounding box is created correctly."""
    expected_image = mock_image.copy()
    draw = ImageDraw.Draw(expected_image)
    draw.rectangle((10, 10, 100, 100), outline="blue", width=2)
    bounding_box = BoundingBox(x1=10, y1=10, x2=100, y2=100)
    assert bounding_box.compute(mock_image) == expected_image


def test_polygon(mock_image: PIL.Image):
    """Test if the polygon is created correctly."""
    # Test from points
    expected_image = mock_image.copy()
    draw = ImageDraw.Draw(expected_image)
    draw.polygon([(10, 10), (100, 10), (100, 100), (10, 100)], fill="red", width=1)
    polygon = Polygon(
        points=[(10, 10), (100, 10), (100, 100), (10, 100)],
        color="red",
        opacity=1,
        outline_width=1,
    )
    assert polygon.compute(mock_image) == expected_image

    # Test from mask
    mask = np.zeros((100, 100), dtype=np.uint8)
    mask[10:100, 10:100] = 255
    expected_image = mock_image.copy()
    draw = ImageDraw.Draw(expected_image)
    draw.polygon([(10, 10), (100, 10), (100, 100), (10, 100)], fill="red", width=1)
    polygon = Polygon(mask=mask, color="red", opacity=1, outline_width=1)
    assert polygon.compute(mock_image) == expected_image

    # Test with empty mask - should not raise, just return image unchanged
    empty_mask = np.zeros((100, 100), dtype=np.uint8)
    polygon_empty = Polygon(mask=empty_mask)
    result = polygon_empty.compute(mock_image)
    assert result == mock_image


def test_label(mock_image: PIL.Image):
    label = Label(label="Label")
    # When using a single label, compute and overlay_labels should return the same image
    assert label.compute(mock_image) == Label.overlay_labels(mock_image, [label])


def test_keypoint(mock_image: PIL.Image):
    keypoint = Keypoint(keypoints=np.array([[100, 100]]), color="red", keypoint_size=3)
    draw = ImageDraw.Draw(mock_image)
    draw.ellipse((97, 97, 103, 103), fill="red")
    assert keypoint.compute(mock_image) == mock_image
