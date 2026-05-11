"""Polygon primitive."""

# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import cv2
from PIL import Image, ImageColor, ImageDraw

from model_api.visualizer.defaults import DEFAULT_OPACITY, DEFAULT_OUTLINE_WIDTH

from .primitive import Primitive

if TYPE_CHECKING:
    import numpy as np

logger = logging.getLogger(__name__)


class Polygon(Primitive):
    """Polygon primitive.

    Args:
        points: List of points.
        mask: Mask to draw the polygon.
        color: Color of the polygon.

    Examples:
        >>> polygon = Polygon(points=[(10, 10), (100, 10), (100, 100), (10, 100)], color="red")
        >>> polygon = Polygon(mask=mask, color="red")
        >>> polygon.compute(image).save("polygon.jpg")

        >>> polygon = Polygon(mask=mask, color="red")
        >>> polygon.compute(image).save("polygon.jpg")
    """

    def __init__(
        self,
        points: list[tuple[int, int]] | None = None,
        mask: np.ndarray | None = None,
        color: str | tuple[int, int, int] = "blue",
        opacity: float = DEFAULT_OPACITY,
        outline_width: int = DEFAULT_OUTLINE_WIDTH,
    ) -> None:
        self.points = self._get_points(points, mask)
        self.color = color
        self.opacity = opacity
        self.outline_width = outline_width

    def _get_points(self, points: list[tuple[int, int]] | None, mask: np.ndarray | None) -> list[tuple[int, int]]:
        """Get points from either points or mask.
        Note:
            Either points or mask should be provided.

        Args:
            points: List of points.
            mask: Mask to draw the polygon.

        Returns:
            List of points.
        """
        if points is not None and mask is not None:
            msg = "Either points or mask should be provided, not both."
            raise ValueError(msg)
        if points is not None:
            points_ = points
        elif mask is not None:
            points_ = self._get_points_from_mask(mask)
        else:
            logger.warning("Neither points nor mask provided. Skipping polygon drawing.")
            return []
        return points_

    def _get_points_from_mask(self, mask: np.ndarray) -> list[tuple[int, int]]:
        """Get points from mask.

        Args:
            mask: Mask to draw the polygon.

        Returns:
            List of points.
        """
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        # incase of multiple contours, use the one with the largest area
        if len(contours) > 1:
            logger.debug("Multiple contours found in the mask. Using the largest one.")
            contours = sorted(contours, key=cv2.contourArea, reverse=True)
        if len(contours) == 0:
            logger.warning("No contours found in the mask. Skipping polygon drawing.")
            return []
        points_ = contours[0].squeeze().tolist()
        return [tuple(point) for point in points_]

    def compute(self, image: Image) -> Image:
        """Compute the polygon.

        Args:
            image: Image to draw the polygon on.

        Returns:
            Image with the polygon drawn on it.
        """
        if len(self.points) == 0:
            return image

        draw = ImageDraw.Draw(image, "RGBA")
        # Draw polygon with darker edge and a semi-transparent fill.
        ink = ImageColor.getrgb(self.color)
        draw.polygon(self.points, fill=(*ink, int(255 * self.opacity)), outline=self.color, width=self.outline_width)
        return image
