"""Anomaly result type."""

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import numpy as np

from .base import Result


class AnomalyResult(Result):
    """Results for anomaly models."""

    def __init__(
        self,
        anomaly_map: np.ndarray | None = None,
        pred_boxes: np.ndarray | None = None,
        pred_label: str | None = None,
        pred_mask: np.ndarray | None = None,
        pred_score: float | None = None,
    ) -> None:
        self.anomaly_map = anomaly_map
        self.pred_boxes = pred_boxes
        self.pred_label = pred_label
        self.pred_mask = pred_mask
        self.pred_score = pred_score

    def _compute_min_max(self, tensor: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Computes min and max values of the tensor."""
        return tensor.min(), tensor.max()

    def __str__(self) -> str:
        assert self.anomaly_map is not None
        assert self.pred_mask is not None
        anomaly_map_min, anomaly_map_max = self._compute_min_max(self.anomaly_map)
        pred_mask_min, pred_mask_max = self._compute_min_max(self.pred_mask)
        return (
            f"anomaly_map min:{anomaly_map_min} max:{anomaly_map_max};"
            f"pred_score:{np.round(self.pred_score, 1) if self.pred_score else 0.0};"
            f"pred_label:{self.pred_label};"
            f"pred_mask min:{pred_mask_min} max:{pred_mask_max};"
        )
