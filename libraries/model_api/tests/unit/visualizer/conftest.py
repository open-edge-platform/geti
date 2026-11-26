"""Conftest for visualization tests."""

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import numpy as np
import pytest
from model_api.visualizer import Overlay, Scene
from PIL import Image


@pytest.fixture(scope="session")
def mock_image():
    data = np.zeros((100, 100, 3), dtype=np.uint8)
    data *= 255
    return Image.fromarray(data)


@pytest.fixture(scope="session")
def mock_scene(mock_image: Image) -> Scene:
    """Mock scene."""
    overlay = np.zeros((100, 100, 3), dtype=np.uint8)
    overlay[50, 50] = [255, 0, 0]
    return Scene(
        base=mock_image,
        overlay=Overlay(overlay),
    )
