"""Detection result type."""

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import numpy as np

from .base import Result
from .utils import array_shape_to_str


class DetectionResult(Result):
    """Result for detection model.

    Args:
        bboxes (np.ndarray): bounding boxes in dim (N, 4) where N is the number of boxes.
        labels (np.ndarray): labels for each bounding box in dim (N,).
        scores (np.ndarray| None, optional): confidence scores for each bounding box in dim (N,).
        label_names (list[str] | None, optional): class names for each label. Defaults to None.
        saliency_map (np.ndarray | None, optional): saliency map for XAI. Defaults to None.
        feature_vector (np.ndarray | None, optional): feature vector for XAI. Defaults to None.
    """

    def __init__(
        self,
        bboxes: np.ndarray,
        labels: np.ndarray,
        scores: np.ndarray | None = None,
        label_names: list[str] | None = None,
        saliency_map: np.ndarray | None = None,
        feature_vector: np.ndarray | None = None,
    ):
        super().__init__()
        self._bboxes = bboxes
        self._labels = labels.astype(np.int32)
        self._scores = scores if scores is not None else np.zeros(len(bboxes))
        self._label_names = ["#"] * len(bboxes) if label_names is None else label_names
        self._saliency_map = saliency_map
        self._feature_vector = feature_vector

    def __len__(self) -> int:
        return len(self.bboxes)

    def __str__(self) -> str:
        repr_str = ""
        for box, score, label, name in zip(
            self.bboxes,
            self.scores,
            self.labels,
            self.label_names,
        ):
            x1, y1, x2, y2 = box
            repr_str += f"{x1}, {y1}, {x2}, {y2}, {label} ({name}): {score:.3f}; "

        repr_str += f"{array_shape_to_str(self.saliency_map)}; {array_shape_to_str(self.feature_vector)}"
        return repr_str

    def get_obj_sizes(self) -> np.ndarray:
        """Get object sizes.

        Returns:
            np.ndarray: Object sizes in dim of (N,).
        """
        return (self._bboxes[:, 2] - self._bboxes[:, 0]) * (self._bboxes[:, 3] - self._bboxes[:, 1])

    @property
    def bboxes(self) -> np.ndarray:
        return self._bboxes

    @bboxes.setter
    def bboxes(self, value):
        if not isinstance(value, np.ndarray):
            msg = "Bounding boxes must be numpy array."
            raise ValueError(msg)
        self._bboxes = value

    @property
    def labels(self) -> np.ndarray:
        return self._labels

    @labels.setter
    def labels(self, value):
        if not isinstance(value, np.ndarray):
            msg = "Labels must be numpy array."
            raise ValueError(msg)
        self._labels = value

    @property
    def scores(self) -> np.ndarray:
        return self._scores

    @scores.setter
    def scores(self, value):
        if not isinstance(value, np.ndarray):
            msg = "Scores must be numpy array."
            raise ValueError(msg)
        self._scores = value

    @property
    def label_names(self) -> list[str]:
        return self._label_names

    @label_names.setter
    def label_names(self, value):
        if not isinstance(value, list):
            msg = "Label names must be list."
            raise ValueError(msg)
        self._label_names = value

    @property
    def saliency_map(self):
        """Saliency map for XAI.

        Returns:
            np.ndarray: Saliency map in dim of (B, N_CLASSES, H, W).
        """
        return self._saliency_map

    @saliency_map.setter
    def saliency_map(self, value: np.ndarray):
        if not isinstance(value, np.ndarray):
            msg = "Saliency map must be numpy array."
            raise ValueError(msg)
        self._saliency_map = value

    @property
    def feature_vector(self) -> np.ndarray:
        return self._feature_vector

    @feature_vector.setter
    def feature_vector(self, value):
        if not isinstance(value, np.ndarray):
            msg = "Feature vector must be numpy array."
            raise ValueError(msg)
        self._feature_vector = value
