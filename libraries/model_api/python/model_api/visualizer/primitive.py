"""Base class for primitives."""

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np
import PIL
from PIL import Image, ImageDraw


class Primitive(ABC):
    """Primitive class."""

    @abstractmethod
    def compute(self, image: Image) -> Image:
        pass


class BoundingBox(Primitive):
    """Bounding box primitive.

    Args:
        x1 (int): x-coordinate of the top-left corner of the bounding box.
        y1 (int): y-coordinate of the top-left corner of the bounding box.
        x2 (int): x-coordinate of the bottom-right corner of the bounding box.
        y2 (int): y-coordinate of the bottom-right corner of the bounding box.
        label (str | None): Label of the bounding box.
        color (str | tuple[int, int, int]): Color of the bounding box.

    Example:
        >>> bounding_box = BoundingBox(x1=10, y1=10, x2=100, y2=100, label="Label Name")
        >>> bounding_box.compute(image)
    """

    def __init__(
        self,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        label: str | None = None,
        color: str | tuple[int, int, int] = "blue",
    ) -> None:
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.label = label
        self.color = color
        self.y_buffer = 5  # Text at the bottom of the text box is clipped. This prevents that.

    def compute(self, image: Image) -> Image:
        draw = ImageDraw.Draw(image)
        # draw rectangle
        draw.rectangle((self.x1, self.y1, self.x2, self.y2), outline=self.color, width=2)
        # add label
        if self.label:
            # draw the background of the label
            textbox = draw.textbbox((0, 0), self.label)
            label_image = Image.new(
                "RGB",
                (textbox[2] - textbox[0], textbox[3] + self.y_buffer - textbox[1]),
                self.color,
            )
            draw = ImageDraw.Draw(label_image)
            # write the label on the background
            draw.text((0, 0), self.label, fill="white")
            image.paste(label_image, (self.x1, self.y1))
        return image


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
