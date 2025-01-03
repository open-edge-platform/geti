"""Anomaly Scene."""

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from PIL import Image

from model_api.models.result import AnomalyResult
from model_api.visualizer.layout import Flatten, Layout
from model_api.visualizer.primitive import Overlay

from .scene import Scene


class AnomalyScene(Scene):
    """Anomaly Scene."""

    def __init__(self, image: Image, result: AnomalyResult) -> None:
        self.image = image
        self.result = result

    @property
    def default_layout(self) -> Layout:
        return Flatten(Overlay)
