"""Keypoint Scene."""

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from typing import Union

from PIL import Image

from model_api.models.result import DetectedKeypoints
from model_api.visualizer.defaults import DEFAULT_FONT_SIZE, DEFAULT_KEYPOINT_SIZE
from model_api.visualizer.layout import Flatten, Layout
from model_api.visualizer.primitive import Keypoint

from .scene import Scene


class KeypointScene(Scene):
    """Keypoint Scene."""

    def __init__(
        self,
        image: Image,
        result: DetectedKeypoints,
        layout: Union[Layout, None] = None,
        scale: float = 1.0,
    ) -> None:
        self.scale = scale
        super().__init__(
            base=image,
            keypoints=self._get_keypoints(result),
            layout=layout,
        )

    def _get_keypoints(self, result: DetectedKeypoints) -> list[Keypoint]:
        return [
            Keypoint(
                result.keypoints,
                result.scores,
                keypoint_size=max(1, int(DEFAULT_KEYPOINT_SIZE * self.scale)),
                font_size=int(DEFAULT_FONT_SIZE * self.scale),
            ),
        ]

    @property
    def default_layout(self) -> Layout:
        return Flatten(Keypoint)
