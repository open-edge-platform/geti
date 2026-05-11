"""Visual Prompting result type."""

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import numpy as np

from .base import Result


class VisualPromptingResult(Result):
    def __init__(
        self,
        upscaled_masks: list[np.ndarray] | None = None,
        processed_mask: list[np.ndarray] | None = None,
        low_res_masks: list[np.ndarray] | None = None,
        iou_predictions: list[np.ndarray] | None = None,
        scores: list[np.ndarray] | None = None,
        labels: list[np.ndarray] | None = None,
        hard_predictions: list[np.ndarray] | None = None,
        soft_predictions: list[np.ndarray] | None = None,
        best_iou: list[float] | None = None,
    ) -> None:
        self.upscaled_masks = upscaled_masks
        self.processed_mask = processed_mask
        self.low_res_masks = low_res_masks
        self.iou_predictions = iou_predictions
        self.scores = scores
        self.labels = labels
        self.hard_predictions = hard_predictions
        self.soft_predictions = soft_predictions
        self.best_iou = best_iou

    def _compute_min_max(self, tensor: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        return tensor.min(), tensor.max()

    def __str__(self) -> str:
        assert self.hard_predictions is not None
        assert self.upscaled_masks is not None
        upscaled_masks_min, upscaled_masks_max = self._compute_min_max(
            self.upscaled_masks[0],
        )

        return (
            f"upscaled_masks min:{upscaled_masks_min:.3f} max:{upscaled_masks_max:.3f};"
            f"hard_predictions shape:{self.hard_predictions[0].shape};"
        )


class PredictedMask:
    def __init__(
        self,
        mask: list[np.ndarray],
        points: list[np.ndarray] | np.ndarray,
        scores: list[float] | np.ndarray,
    ) -> None:
        self.mask = mask
        self.points = points
        self.scores = scores

    def __str__(self) -> str:
        obj_str = ""
        obj_str += f"mask sum: {np.sum(sum(self.mask))}; "

        if isinstance(self.points, list):
            for i, point in enumerate(self.points):
                obj_str += "["
                obj_str += ", ".join(str(round(c, 2)) for c in point)
                obj_str += "] "
                obj_str += "iou: " + f"{float(self.scores[i]):.3f} "
        else:
            for i in range(self.points.shape[0]):
                point = self.points[i]
                obj_str += "["
                obj_str += ", ".join(str(round(c, 2)) for c in point)
                obj_str += "] "
                obj_str += "iou: " + f"{float(self.scores[i]):.3f} "

        return obj_str.strip()


class ZSLVisualPromptingResult(Result):
    def __init__(self, data: dict[int, PredictedMask]) -> None:
        self.data = data

    def __str__(self) -> str:
        return ", ".join(str(self.data[k]) for k in self.data)

    def get_mask(self, label: int) -> PredictedMask:
        """Returns a mask belonging to a given label"""
        return self.data[label]
