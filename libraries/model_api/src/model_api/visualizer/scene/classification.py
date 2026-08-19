"""Classification Scene."""

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from typing import TYPE_CHECKING, Union

import cv2
from PIL import Image

from model_api.models.result import ClassificationResult
from model_api.visualizer.defaults import DEFAULT_FONT_SIZE, DEFAULT_LABEL_BG_COLOR
from model_api.visualizer.layout import Flatten, Layout
from model_api.visualizer.primitive import Label, Overlay

from .scene import Scene

if TYPE_CHECKING:
    from collections.abc import Mapping

    from model_api.visualizer.utils import Color


class ClassificationScene(Scene):
    """Classification Scene.

    Args:
        image: Base image to draw on.
        result: Classification result to render.
        layout: Optional layout to use for rendering.
        scale: Scale factor applied to drawing sizes.
        label_colors: Optional mapping of label name to colour used as the label
            background. Labels absent from the mapping keep the default background.
    """

    def __init__(
        self,
        image: Image,
        result: ClassificationResult,
        layout: Union[Layout, None] = None,
        scale: float = 1.0,
        label_colors: Union["Mapping[str, Color]", None] = None,
    ) -> None:
        self.scale = scale
        self.label_colors = label_colors or {}
        super().__init__(
            base=image,
            label=self._get_labels(result),
            overlay=self._get_overlays(result),
            layout=layout,
        )

    def _get_labels(self, result: ClassificationResult) -> list[Label]:
        labels = []
        if result.top_labels is not None and len(result.top_labels) > 0:
            for label in result.top_labels:
                if label.name is not None:
                    labels.append(
                        Label(
                            label=label.name,
                            score=label.confidence,
                            size=int(DEFAULT_FONT_SIZE * self.scale),
                            bg_color=self.label_colors.get(label.name, DEFAULT_LABEL_BG_COLOR),
                        ),
                    )
        return labels

    def _get_overlays(self, result: ClassificationResult) -> list[Overlay]:
        overlays = []
        if result.saliency_map is not None and result.saliency_map.size > 0:
            saliency_map = cv2.cvtColor(result.saliency_map, cv2.COLOR_BGR2RGB)
            overlays.append(Overlay(saliency_map))
        return overlays

    @property
    def default_layout(self) -> Layout:
        return Flatten(Overlay, Label)
