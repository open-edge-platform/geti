"""Visualizer for modelAPI."""

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

from PIL import Image

from model_api.models.result import (
    AnomalyResult,
    ClassificationResult,
    DetectionResult,
    Result,
)

from .layout import Layout
from .scene import AnomalyScene, ClassificationScene, DetectionScene, Scene


class Visualizer:
    def __init__(self, layout: Layout) -> None:
        self.layout = layout

    def show(self, image: Image, result: Result) -> Image:
        scene = self._scene_from_result(image, result)
        return scene.show()

    def save(self, image: Image, result: Result, path: Path) -> None:
        scene = self._scene_from_result(image, result)
        scene.save(path)

    def _scene_from_result(self, image: Image, result: Result) -> Scene:
        scene: Scene
        if isinstance(result, AnomalyResult):
            scene = AnomalyScene(image, result)
        elif isinstance(result, ClassificationResult):
            scene = ClassificationScene(image, result)
        elif isinstance(result, DetectionResult):
            scene = DetectionScene(image, result)
        else:
            msg = f"Unsupported result type: {type(result)}"
            raise ValueError(msg)

        return scene
