"""Segmentation result type."""

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import TYPE_CHECKING

import cv2
import numpy as np

from .utils import array_shape_to_str

if TYPE_CHECKING:
    from cv2.typing import RotatedRect


class SegmentedObject:
    def __init__(
        self,
        xmin: int,
        ymin: int,
        xmax: int,
        ymax: int,
        score: float,
        id: int,
        str_label: str,
        mask: np.ndarray,
    ) -> None:
        self.xmin = xmin
        self.ymin = ymin
        self.xmax = xmax
        self.ymax = ymax
        self.score = score
        self.id = id
        self.str_label = str_label
        self.mask = mask

    def __str__(self):
        return (
            f"{self.xmin}, {self.ymin}, {self.xmax}, {self.ymax}, {self.id} ({self.str_label}): {self.score:.3f}"
            f", {(self.mask > 0.5).sum()}"
        )


class SegmentedObjectWithRects(SegmentedObject):
    def __init__(self, segmented_object: SegmentedObject, rotated_rect: RotatedRect) -> None:
        super().__init__(
            segmented_object.xmin,
            segmented_object.ymin,
            segmented_object.xmax,
            segmented_object.ymax,
            segmented_object.score,
            segmented_object.id,
            segmented_object.str_label,
            segmented_object.mask,
        )
        self.rotated_rect = rotated_rect

    def __str__(self):
        res = super().__str__()
        rect = self.rotated_rect
        res += f", RotatedRect: {rect[0][0]:.3f} {rect[0][1]:.3f} {rect[1][0]:.3f} {rect[1][1]:.3f} {rect[2]:.3f}"
        return res


class InstanceSegmentationResult:
    def __init__(
        self,
        segmentedObjects: list[SegmentedObject | SegmentedObjectWithRects],
        saliency_map: list[np.ndarray],
        feature_vector: np.ndarray,
    ):
        self.segmentedObjects = segmentedObjects
        # Contain per class saliency_maps and "feature_vector" model output if feature_vector exists
        self.saliency_map = saliency_map
        self.feature_vector = feature_vector

    def __str__(self):
        obj_str = "; ".join(str(obj) for obj in self.segmentedObjects)
        filled = 0
        for cls_map in self.saliency_map:
            if cls_map.size:
                filled += 1
        prefix = f"{obj_str}; " if len(obj_str) else ""
        return prefix + f"{filled}; [{','.join(str(i) for i in self.feature_vector.shape)}]"


class Contour:
    def __init__(self, label: str, probability: float, shape: list[tuple[int, int]]):
        self.shape = shape
        self.label = label
        self.probability = probability

    def __str__(self):
        return f"{self.label}: {self.probability:.3f}, {len(self.shape)}"


class ImageResultWithSoftPrediction:
    def __init__(
        self,
        resultImage: np.ndarray,
        soft_prediction: np.ndarray,
        saliency_map: np.ndarray,
        feature_vector: np.ndarray,
    ):
        self.resultImage = resultImage
        # Contain per class saliency_maps and "feature_vector" model output if feature_vector exists
        self.soft_prediction = soft_prediction
        self.saliency_map = saliency_map  # Requires return_soft_prediction==True
        self.feature_vector = feature_vector

    def __str__(self):
        outHist = cv2.calcHist(
            [self.resultImage.astype(np.uint8)],
            channels=None,
            mask=None,
            histSize=[256],
            ranges=[0, 255],
        )
        hist = ""
        for i, count in enumerate(outHist):
            if count > 0:
                hist += f"{i}: {count[0] / self.resultImage.size:.3f}, "
        return (
            f"{hist}{array_shape_to_str(self.soft_prediction)}, "
            f"{array_shape_to_str(self.saliency_map)}, "
            f"{array_shape_to_str(self.feature_vector)}"
        )
