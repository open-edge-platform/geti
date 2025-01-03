"""Detection Scene."""

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from PIL import Image

from model_api.models.result import DetectionResult

from .scene import Scene


class DetectionScene(Scene):
    """Detection Scene."""

    def __init__(self, image: Image, result: DetectionResult) -> None:
        self.image = image
        self.result = result
