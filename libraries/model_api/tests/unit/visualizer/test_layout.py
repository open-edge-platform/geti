"""Test layout."""

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import numpy as np
from model_api.visualizer import Flatten, HStack, Scene
from model_api.visualizer.primitive import Overlay
from PIL import Image


def test_flatten_layout(mock_image: Image, mock_scene: Scene):
    """Test if the layout is created correctly."""
    overlay = np.zeros((100, 100, 3), dtype=np.uint8)
    overlay[50, 50] = [255, 0, 0]
    overlay = Image.fromarray(overlay)

    expected_image = Image.blend(mock_image, overlay, 0.4)
    mock_scene.layout = Flatten(Overlay)
    assert mock_scene.render() == expected_image


def test_flatten_layout_with_no_primitives(mock_image: Image, mock_scene: Scene):
    """Test if the layout is created correctly."""
    mock_scene.layout = Flatten()
    assert mock_scene.render() == mock_image


def test_hstack_layout():
    """Test if the layout is created correctly."""
    blue_overlay = np.zeros((100, 100, 3), dtype=np.uint8)
    blue_overlay[50, 50] = [0, 0, 255]
    blue_overlay = Image.fromarray(blue_overlay)

    red_overlay = np.zeros((100, 100, 3), dtype=np.uint8)
    red_overlay[50, 50] = [255, 0, 0]
    red_overlay = Image.fromarray(red_overlay)

    mock_scene = Scene(
        base=Image.new("RGB", (100, 100)),
        overlay=[Overlay(blue_overlay, opacity=1.0), Overlay(red_overlay, opacity=1.0)],
        layout=HStack(Overlay),
    )

    expected_image = Image.new("RGB", (200, 100))
    expected_image.paste(blue_overlay, (0, 0))
    expected_image.paste(red_overlay, (100, 0))

    assert mock_scene.render() == expected_image
