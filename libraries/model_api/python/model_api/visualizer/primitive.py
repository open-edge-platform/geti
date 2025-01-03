"""Base class for primitives."""

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np
import PIL


class Primitive(ABC):
    """Primitive class."""

    @abstractmethod
    def compute(self, image: PIL.Image) -> PIL.Image:
        pass


class Overlay(Primitive):
    """Overlay primitive.

    Useful for XAI and Anomaly Maps.

    Args:
        image (PIL.Image | np.ndarray): Image to be overlaid.
        opacity (float): Opacity of the overlay.
    """

    def __init__(self, image: PIL.Image | np.ndarray, opacity: float = 0.4) -> None:
        self.image = self._to_pil(image)
        self.opacity = opacity

    def _to_pil(self, image: PIL.Image | np.ndarray) -> PIL.Image:
        if isinstance(image, np.ndarray):
            return PIL.Image.fromarray(image)
        return image

    def compute(self, image: PIL.Image) -> PIL.Image:
        _image = self.image.resize(image.size)
        return PIL.Image.blend(image, _image, self.opacity)
