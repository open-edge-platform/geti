"""Detection Scene."""

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from typing import Union

import cv2
from PIL import Image

from model_api.models.result import DetectionResult
from model_api.visualizer.defaults import DEFAULT_FONT_SIZE, DEFAULT_OUTLINE_WIDTH
from model_api.visualizer.layout import Flatten, HStack, Layout
from model_api.visualizer.primitive import BoundingBox, Label, Overlay
from model_api.visualizer.utils import get_label_color_mapping

from .scene import Scene


class DetectionScene(Scene):
    """Detection Scene."""

    def __init__(
        self,
        image: Image,
        result: DetectionResult,
        layout: Union[Layout, None] = None,
        scale: float = 1.0,
    ) -> None:
        self.color_per_label = get_label_color_mapping(result.label_names)
        self.scale = scale
        super().__init__(
            base=image,
            bounding_box=self._get_bounding_boxes(result),
            overlay=self._get_overlays(result),
            layout=layout,
        )

    def _get_overlays(self, result: DetectionResult) -> list[Overlay]:
        overlays = []
        # Add only the overlays that are predicted
        label_index_mapping = dict(zip(result.labels, result.label_names))
        for label_index, label_name in label_index_mapping.items():
            # Index 0 as it assumes only one batch
            if result.saliency_map is not None and result.saliency_map.size > 0:
                saliency_map = cv2.applyColorMap(result.saliency_map[0][label_index], cv2.COLORMAP_JET)
                saliency_map = cv2.cvtColor(saliency_map, cv2.COLOR_BGR2RGB)
                overlays.append(
                    Overlay(
                        saliency_map,
                        label=label_name.title(),
                        font_size=int(DEFAULT_FONT_SIZE * self.scale),
                    ),
                )
        return overlays

    def _get_bounding_boxes(self, result: DetectionResult) -> list[BoundingBox]:
        bounding_boxes = []
        for score, label_name, bbox in zip(result.scores, result.label_names, result.bboxes):
            x1, y1, x2, y2 = bbox
            label = f"{label_name} ({score:.2f})"
            bounding_boxes.append(
                BoundingBox(
                    x1=x1,
                    y1=y1,
                    x2=x2,
                    y2=y2,
                    label=label,
                    color=self.color_per_label[label_name],
                    outline_width=max(1, int(DEFAULT_OUTLINE_WIDTH * self.scale)),
                    font_size=int(DEFAULT_FONT_SIZE * self.scale),
                ),
            )
        return bounding_boxes

    @property
    def default_layout(self) -> Layout:
        return HStack(Flatten(BoundingBox, Label), Overlay)
