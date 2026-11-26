# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Tests covering remaining gaps for 100% visualizer coverage."""

from unittest.mock import patch

import numpy as np
from model_api.models.result import DetectedKeypoints
from model_api.models.result.visual_prompting import VisualPromptingResult
from model_api.visualizer.primitive.keypoints import Keypoint
from model_api.visualizer.scene.keypoint import KeypointScene
from model_api.visualizer.scene.visual_prompting import VisualPromptingScene
from model_api.visualizer.utils import truetype_font
from PIL import Image

# --- VisualPromptingScene ---


def test_visual_prompting_scene_constructor():
    """Test VisualPromptingScene stores result."""
    result = VisualPromptingResult()
    scene = VisualPromptingScene(result)
    assert scene.result is result


# --- KeypointScene ---


def test_keypoint_scene_constructor():
    """Test KeypointScene creation and _get_keypoints."""
    img = Image.new("RGB", (100, 100))
    result = DetectedKeypoints(
        keypoints=np.array([[50, 50], [70, 70]]),
        scores=np.array([0.95, 0.80]),
    )
    scene = KeypointScene(img, result)
    assert scene.keypoints is not None
    assert len(scene.keypoints) == 1
    assert isinstance(scene.keypoints[0], Keypoint)


def test_keypoint_scene_default_layout():
    """Test KeypointScene.default_layout returns Flatten(Keypoint)."""
    from model_api.visualizer.layout import Flatten

    img = Image.new("RGB", (100, 100))
    result = DetectedKeypoints(
        keypoints=np.array([[50, 50]]),
        scores=np.array([0.9]),
    )
    scene = KeypointScene(img, result)
    layout = scene.default_layout
    assert isinstance(layout, Flatten)


def test_keypoint_scene_render():
    """Test KeypointScene renders correctly."""
    img = Image.new("RGB", (100, 100))
    result = DetectedKeypoints(
        keypoints=np.array([[50, 50]]),
        scores=np.array([0.9]),
    )
    scene = KeypointScene(img, result)
    rendered = scene.render()
    assert isinstance(rendered, Image.Image)


# --- truetype_font ---


def test_truetype_font():
    """Test truetype_font loads a font from path."""
    with patch("model_api.visualizer.utils.ImageFont.truetype") as mock_truetype:
        mock_truetype.return_value = "mock_font"
        # Clear lru_cache to ensure our call goes through
        truetype_font.cache_clear()
        result = truetype_font("/fake/path/font.ttf", 12)
        assert result == "mock_font"
        mock_truetype.assert_called_once_with("/fake/path/font.ttf", 12)
        truetype_font.cache_clear()
