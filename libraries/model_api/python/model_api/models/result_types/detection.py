"""Detection result type."""

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import TYPE_CHECKING

from .utils import array_shape_to_str

if TYPE_CHECKING:
    import numpy as np


class Detection:
    def __init__(
        self,
        xmin: int,
        ymin: int,
        xmax: int,
        ymax: int,
        score: float,
        id: int,
        str_label: str | None = None,
    ) -> None:
        self.xmin = xmin
        self.ymin = ymin
        self.xmax = xmax
        self.ymax = ymax
        self.score = score
        self.id = int(id)
        self.str_label = str_label

    def __str__(self):
        return f"{self.xmin}, {self.ymin}, {self.xmax}, {self.ymax}, {self.id} ({self.str_label}): {self.score:.3f}"


class DetectionResult:
    """Result for detection model."""

    def __init__(
        self,
        objects: list[Detection] | None = None,
        saliency_map: np.ndarray | None = None,
        feature_vector: np.ndarray | None = None,
    ) -> None:
        self.objects = objects
        self.saliency_map = saliency_map
        self.feature_vector = feature_vector

    def __str__(self):
        assert self.objects is not None
        obj_str = "; ".join(str(obj) for obj in self.objects)
        if obj_str:
            obj_str += "; "
        return f"{obj_str}{array_shape_to_str(self.saliency_map)}; {array_shape_to_str(self.feature_vector)}"
