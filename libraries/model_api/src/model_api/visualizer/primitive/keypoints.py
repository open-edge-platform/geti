"""Keypoints primitive."""

# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from typing import Union

import numpy as np
from PIL import Image, ImageDraw

from model_api.visualizer.defaults import DEFAULT_FONT_SIZE, DEFAULT_KEYPOINT_SIZE
from model_api.visualizer.utils import default_font

from .primitive import Primitive


class Keypoint(Primitive):
    """Keypoint primitive.

    Args:
        keypoints (np.ndarray): Keypoints. Shape: (N, 2)
        scores (np.ndarray | None): Scores. Shape: (N,). Defaults to None.
        color (str | tuple[int, int, int]): Color of the keypoints. Defaults to "purple".
    """

    def __init__(
        self,
        keypoints: np.ndarray,
        scores: Union[np.ndarray, None] = None,
        color: Union[str, tuple[int, int, int]] = "purple",
        keypoint_size: int = DEFAULT_KEYPOINT_SIZE,
        font_size: int = DEFAULT_FONT_SIZE,
    ) -> None:
        self.keypoints = self._validate_keypoints(keypoints)
        self.scores = scores
        self.color = color
        self.keypoint_size = keypoint_size
        self.font_size = font_size

    def compute(self, image: Image) -> Image:
        """Draw keypoints on the image."""
        draw = ImageDraw.Draw(image)
        for keypoint in self.keypoints:
            draw.ellipse(
                (
                    keypoint[0] - self.keypoint_size,
                    keypoint[1] - self.keypoint_size,
                    keypoint[0] + self.keypoint_size,
                    keypoint[1] + self.keypoint_size,
                ),
                fill=self.color,
            )

        if self.scores is not None:
            font = default_font(size=self.font_size)
            for score, keypoint in zip(self.scores, self.keypoints):
                textbox = draw.textbbox((0, 0), f"{score:.2f}", font=font)
                draw.text(
                    (keypoint[0] - textbox[2] // 2, keypoint[1] + self.keypoint_size),
                    f"{score:.2f}",
                    font=font,
                    fill=self.color,
                )
        return image

    def _validate_keypoints(self, keypoints: np.ndarray) -> np.ndarray:
        if keypoints.shape[1] != 2:
            msg = "Keypoints must have shape (N, 2)"
            raise ValueError(msg)
        return keypoints
