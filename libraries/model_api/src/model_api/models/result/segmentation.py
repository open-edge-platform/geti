"""Segmentation result type."""

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import TYPE_CHECKING

import cv2
import numpy as np

from .base import Result
from .detection import DetectionResult
from .utils import array_shape_to_str

if TYPE_CHECKING:
    from cv2.typing import RotatedRect


class InstanceSegmentationResult(DetectionResult):
    """Instance segmentation result type.

    Args:
        bboxes (np.ndarray): bounding boxes in dim (N, 4) where N is the number of boxes.
        labels (np.ndarray): labels for each bounding box in dim (N,).
        masks (np.ndarray): masks for each bounding box in dim (N, H, W).
        scores (np.ndarray | None, optional): confidence scores for each bounding box in dim (N,). Defaults to None.
        label_names (list[str] | None, optional): class names for each label. Defaults to None.
        saliency_map (list[np.ndarray] | None, optional): saliency maps for XAI. Defaults to None.
        feature_vector (np.ndarray | None, optional): feature vector for XAI. Defaults to None.
    """

    def __init__(
        self,
        bboxes: np.ndarray,
        labels: np.ndarray,
        masks: np.ndarray,
        scores: np.ndarray | None = None,
        label_names: list[str] | None = None,
        saliency_map: list[np.ndarray] | None = None,
        feature_vector: np.ndarray | None = None,
    ):
        super().__init__(bboxes, labels, scores, label_names, saliency_map, feature_vector)
        self._masks = masks

    def __str__(self) -> str:
        repr_str = ""
        for box, score, label, name, mask in zip(
            self.bboxes,
            self.scores,
            self.labels,
            self.label_names,
            self.masks,
        ):
            x1, y1, x2, y2 = box
            repr_str += f"{x1}, {y1}, {x2}, {y2}, {label} ({name}): {score:.3f}, {(mask > 0.5).sum()}; "

        filled = 0
        for cls_map in self.saliency_map:
            if cls_map.size:
                filled += 1
        prefix = f"{repr_str}" if len(repr_str) else ""
        return prefix + f"{filled}; {array_shape_to_str(self.feature_vector)}"

    @property
    def masks(self) -> np.ndarray:
        return self._masks

    @masks.setter
    def masks(self, value):
        if not isinstance(value, np.ndarray):
            msg = "Masks must be numpy array."
            raise ValueError(msg)
        self._masks = value

    @property
    def saliency_map(self):
        return self._saliency_map

    @saliency_map.setter
    def saliency_map(self, value: list[np.ndarray]):
        if not isinstance(value, list):
            msg = "Saliency maps must be list."
            raise ValueError(msg)
        self._saliency_map = value


class RotatedSegmentationResult(InstanceSegmentationResult):
    """Rotated instance segmentation result type.

    Args:
        bboxes (np.ndarray): bounding boxes in dim (N, 4) where N is the number of boxes.
        labels (np.ndarray): labels for each bounding box in dim (N,).
        masks (np.ndarray): masks for each bounding box in dim (N, H, W).
        rotated_rects (list[RotatedRect]): rotated rectangles for each bounding box.
        scores (np.ndarray | None, optional): confidence scores for each bounding box in dim (N,). Defaults to None.
        label_names (list[str] | None, optional): class names for each label. Defaults to None.
        saliency_map (list[np.ndarray] | None, optional): saliency maps for XAI. Defaults to None.
        feature_vector (np.ndarray | None, optional): feature vector for XAI. Defaults to None.
    """

    def __init__(
        self,
        bboxes: np.ndarray,
        labels: np.ndarray,
        masks: np.ndarray,
        rotated_rects: list[RotatedRect],
        scores: np.ndarray | None = None,
        label_names: list[str] | None = None,
        saliency_map: list[np.ndarray] | None = None,
        feature_vector: np.ndarray | None = None,
    ):
        super().__init__(bboxes, labels, masks, scores, label_names, saliency_map, feature_vector)
        self.rotated_rects = rotated_rects

    def __str__(self) -> str:
        repr_str = ""
        for box, score, label, name, mask, rotated_rect in zip(
            self.bboxes,
            self.scores,
            self.labels,
            self.label_names,
            self.masks,
            self.rotated_rects,
        ):
            x1, y1, x2, y2 = box
            (cx, cy), (w, h), angle = rotated_rect
            repr_str += f"{x1}, {y1}, {x2}, {y2}, {label} ({name}): {score:.3f}, {(mask > 0.5).sum()},"
            repr_str += f" RotatedRect: {cx:.3f} {cy:.3f} {w:.3f} {h:.3f} {angle:.3f}; "

        filled = 0
        for cls_map in self.saliency_map:
            if cls_map.size:
                filled += 1
        prefix = f"{repr_str}" if len(repr_str) else ""
        return prefix + f"{filled}; {array_shape_to_str(self.feature_vector)}"

    @property
    def rotated_rects(self) -> list[RotatedRect]:
        return self._rotated_rects

    @rotated_rects.setter
    def rotated_rects(self, value):
        if not isinstance(value, list):
            msg = "RotatedRects must be list."
            raise ValueError(msg)
        self._rotated_rects = value


class Contour:
    """Represents a semantic segmentation mask as internals of a contour with "holes".
    Args:
        label (str): The label of the contour.
        probability (float): The probability associated with the contour.
        shape (np.ndarray | list[tuple[int, int]]): The shape of the contour. Shape is represented as a
            list of 2d points or an equivalent numpy array (N, 2).
        excluded_shapes (list[np.ndarray] | list[tuple[int, int]] | None, optional): Shapes of excluded contours.
            If empty, the main shape is simply connected. Otherwise, excluded_shapes
            represent "holes". Defaults to None.
    """

    def __init__(
        self,
        label: str,
        probability: float,
        shape: np.ndarray | list[tuple[int, int]],
        excluded_shapes: list[np.ndarray] | list[list[tuple[int, int]]] | None = None,
    ):
        self.shape = np.array(shape)
        self.label = label
        self.probability = probability
        self.excluded_shapes = [np.array(x) for x in excluded_shapes] if excluded_shapes is not None else None

    def __str__(self):
        num_children = len(self.excluded_shapes) if self.excluded_shapes is not None else 0
        return f"{self.label}: {self.probability:.3f}, {len(self.shape)}, {num_children}"

    def __repr__(self):
        return self.__str__()


class ImageResultWithSoftPrediction(Result):
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
