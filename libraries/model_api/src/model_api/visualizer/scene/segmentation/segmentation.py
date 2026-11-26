"""Segmentation Scene."""

# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from typing import Union

import cv2
import numpy as np
from PIL import Image

from model_api.models.result import ImageResultWithSoftPrediction
from model_api.visualizer.defaults import DEFAULT_FONT_SIZE
from model_api.visualizer.layout import HStack, Layout
from model_api.visualizer.primitive import Overlay
from model_api.visualizer.scene import Scene


class SegmentationScene(Scene):
    """Segmentation Scene."""

    def __init__(
        self,
        image: Image,
        result: ImageResultWithSoftPrediction,
        layout: Union[Layout, None] = None,
        scale: float = 1.0,
    ) -> None:
        self.scale = scale
        super().__init__(
            base=image,
            overlay=self._get_overlays(result),
            layout=layout,
        )

    def _get_overlays(self, result: ImageResultWithSoftPrediction) -> list[Overlay]:
        overlays = []
        # Use the hard prediction to get the overlays
        hard_prediction = result.resultImage  # shape H,W
        num_classes = hard_prediction.max()
        for i in range(1, num_classes + 1):  # ignore background
            class_map = (hard_prediction == i).astype(np.uint8) * 255
            class_map = cv2.applyColorMap(class_map, cv2.COLORMAP_JET)
            class_map = cv2.cvtColor(class_map, cv2.COLOR_BGR2RGB)
            overlays.append(
                Overlay(
                    class_map,
                    label=f"Class {i}",
                    font_size=int(DEFAULT_FONT_SIZE * self.scale),
                ),
            )

        # Add saliency map
        if result.saliency_map is not None and result.saliency_map.size > 0:
            saliency_map = cv2.cvtColor(result.saliency_map, cv2.COLOR_BGR2RGB)
            overlays.append(
                Overlay(
                    saliency_map,
                    label="Saliency Map",
                    font_size=int(DEFAULT_FONT_SIZE * self.scale),
                ),
            )

        return overlays

    @property
    def default_layout(self) -> Layout:
        return HStack(Overlay)
