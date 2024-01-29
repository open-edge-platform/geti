"""Definition for anomaly models.

Note: This file will change when anomalib is upgraded in OTX. CVS-114640

 Copyright (c) 2021-2023 Intel Corporation

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

      http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
"""

from __future__ import annotations

from typing import Any

import cv2
import numpy as np

from .image_model import ImageModel
from .types import ListValue, NumericalValue, StringValue
from .utils import AnomalyResult


class AnomalyDetection(ImageModel):
    __model__ = "AnomalyDetection"

    def __init__(self, inference_adapter, configuration=dict(), preload=False):
        super().__init__(inference_adapter, configuration, preload)
        self._check_io_number(1, 1)
        self.normalization_scale: float
        self.image_threshold: float
        self.pixel_threshold: float
        self.task: str
        self.labels: list[str]

    def postprocess(self, outputs: dict[str, np.ndarray], meta: dict[str, Any]):
        """Post-processes the outputs and returns the results.

        Args:
            outputs (Dict[str, np.ndarray]): Raw model outputs
            meta (Dict[str, Any]): Meta data containing the original image shape

        Returns:
            AnomalyResult: Results
        """
        anomaly_map: np.ndarray | None = None
        pred_label: str | None = None
        pred_mask: np.ndarray | None = None
        pred_boxes: np.ndarray | None = None
        predictions = outputs[list(self.outputs)[0]]

        if len(predictions.shape) == 1:
            pred_score = predictions
        else:
            anomaly_map = predictions.squeeze()
            pred_score = anomaly_map.reshape(-1).max()

        pred_label = (
            self.labels[1] if pred_score > self.image_threshold else self.labels[0]
        )

        assert anomaly_map is not None
        pred_mask = (anomaly_map >= self.pixel_threshold).astype(np.uint8)
        anomaly_map = self._normalize(anomaly_map, self.pixel_threshold)
        anomaly_map *= 255
        anomaly_map = np.round(anomaly_map).astype(np.uint8)
        pred_mask = cv2.resize(
            pred_mask, (meta["original_shape"][1], meta["original_shape"][0])
        )

        # normalize
        pred_score = self._normalize(pred_score, self.image_threshold)

        if pred_label == self.labels[0]:  # normal
            pred_score = 1 - pred_score  # Score of normal is 1 - score of anomaly

        # resize outputs
        if anomaly_map is not None:
            anomaly_map = cv2.resize(
                anomaly_map, (meta["original_shape"][1], meta["original_shape"][0])
            )

        if self.task == "detection":
            pred_boxes = self._get_boxes(pred_mask)

        return AnomalyResult(
            anomaly_map=anomaly_map,
            pred_boxes=pred_boxes,
            pred_label=pred_label,
            pred_mask=pred_mask,
            pred_score=pred_score.item(),
        )

    @classmethod
    def parameters(cls) -> dict:
        parameters = super().parameters()
        parameters.update(
            {
                "image_threshold": NumericalValue(
                    description="Image threshold", min=0.0, default_value=0.5
                ),
                "pixel_threshold": NumericalValue(
                    description="Pixel threshold", min=0.0, default_value=0.5
                ),
                "normalization_scale": NumericalValue(
                    description="Value used for normalization",
                ),
                "task": StringValue(
                    description="Task type", default_value="segmentation"
                ),
                "labels": ListValue(description="List of class labels"),
            }
        )
        return parameters

    def _normalize(self, tensor: np.ndarray, threshold: float) -> np.ndarray:
        """Currently supports only min-max normalization."""
        normalized = ((tensor - threshold) / self.normalization_scale) + 0.5
        normalized = np.clip(normalized, 0, 1)
        return normalized

    @staticmethod
    def _get_boxes(mask: np.ndarray) -> np.ndarray:
        """Get bounding boxes from mask.

        Args:
            mask (np.ndarray): Input mask of shapw (H, W)

        Returns:
            np.ndarray: array of shape (N,4) containing the bounding box coordinates of the objects in the masks in
                format [x1, y1, x2, y2]
        """
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        boxes = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            boxes.append([x, y, x + w, y + h])
        return np.array(boxes)
