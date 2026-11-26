"""Overlay primitive."""

# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Union

import numpy as np
import PIL

from model_api.visualizer.defaults import DEFAULT_FONT_SIZE, DEFAULT_OPACITY
from model_api.visualizer.utils import default_font, make_label_image

from .primitive import Primitive


class Overlay(Primitive):
    """Overlay primitive.

    Useful for XAI and Anomaly Maps.

    Args:
        image (PIL.Image | np.ndarray): Image to be overlaid.
        label (str | None): Optional label name to overlay.
        opacity (float): Opacity of the overlay.
    """

    def __init__(
        self,
        image: PIL.Image | np.ndarray,
        opacity: float = DEFAULT_OPACITY,
        label: Union[str, None] = None,
        font_size: int = DEFAULT_FONT_SIZE,
    ) -> None:
        self.image = self._to_pil(image)
        self.label = label
        self.opacity = opacity
        self.font_size = font_size

    def _to_pil(self, image: PIL.Image | np.ndarray) -> PIL.Image:
        if isinstance(image, np.ndarray):
            return PIL.Image.fromarray(image)
        return image

    def compute(self, image: PIL.Image) -> PIL.Image:
        image_ = self.image.resize(image.size)
        return PIL.Image.blend(image, image_, self.opacity)

    @classmethod
    def overlay_labels(
        cls,
        image: PIL.Image,
        labels: Union[list[str], str, None] = None,
        font_size: int = DEFAULT_FONT_SIZE,
    ) -> PIL.Image:
        """Draw labels at the bottom center of the image.

        This is handy when you want to add a label to the image.

        Args:
            image: Image to overlay the labels on.
            labels: Labels to overlay.
            font_size: Font size for the label text.
        """
        if labels is not None:
            labels = [labels] if isinstance(labels, str) else labels
            font = default_font(size=font_size)
            image_ = make_label_image(", ".join(labels), font, fg_color="black", bg_color="white")
            image.paste(image_, (image.width // 2 - image_.width // 2, image.height - image_.height))
        return image
