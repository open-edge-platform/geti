#
# Copyright (C) 2020-2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#
"""Definition for anomaly models.

Note: This file will change when anomalib is upgraded in OTX. CVS-114640
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import cv2
import numpy as np

from model_api.models.image_model import ImageModel
from model_api.models.parameters import ParameterRegistry
from model_api.models.result import AnomalyResult

if TYPE_CHECKING:
    from model_api.adapters.inference_adapter import InferenceAdapter


class AnomalyDetection(ImageModel):
    """Anomaly Detection model.

    Generic anomaly detection model that acts as an inference wrapper for all the exported models from
    Anomalib.

    Args:
        inference_adapter (InferenceAdapter): Inference adapter
        configuration (dict, optional): Configuration parameters. Defaults to {}.
        preload (bool, optional): Whether to preload the model. Defaults to False.

    Example:
        >>> from model_api.models import AnomalyDetection
        >>> import cv2
        >>> model = AnomalyDetection.create_model("./path_to_model.xml")
        >>> image = cv2.imread("path_to_image.jpg")
        >>> result = model.predict(image)
            AnomalyResult(anomaly_map=array([[150, 150, 150, ..., 138, 138, 138],
                [150, 150, 150, ..., 138, 138, 138],
                [150, 150, 150, ..., 138, 138, 138],
                ...,
                [134, 134, 134, ..., 138, 138, 138],
                [134, 134, 134, ..., 138, 138, 138],
                [134, 134, 134, ..., 138, 138, 138]], dtype=uint8),
                pred_boxes=None, pred_label='Anomaly',
                pred_mask=array([[1, 1, 1, ..., 1, 1, 1],
                    [1, 1, 1, ..., 1, 1, 1],
                    [1, 1, 1, ..., 1, 1, 1],
                    ...,
                    [1, 1, 1, ..., 1, 1, 1],
                    [1, 1, 1, ..., 1, 1, 1],
                    [1, 1, 1, ..., 1, 1, 1]], dtype=uint8),
                    pred_score=0.8536462108391619)
    """

    __model__ = "AnomalyDetection"

    def __init__(
        self,
        inference_adapter: InferenceAdapter,
        configuration: dict = {},
        preload: bool = False,
    ) -> None:
        super().__init__(inference_adapter, configuration, preload)
        self._check_io_number(1, (1, 4))

    def _resize_image(self, image: np.ndarray) -> tuple[np.ndarray, dict]:
        if (
            self._is_dynamic
            and getattr(self.inference_adapter, "device", "") == "NPU"
            and hasattr(self.inference_adapter, "compiled_model")
        ):
            _, self.c, self.h, self.w = self.inference_adapter.compiled_model.inputs[0].get_shape()
            self._is_dynamic = False

        return super()._resize_image(image)

    def _input_transform(self, image: np.ndarray) -> np.ndarray:
        if image.dtype == np.uint8:
            return image.astype(np.float32) / 255.0
        return image.astype(np.float32)

    def postprocess(self, outputs: dict[str, np.ndarray], meta: dict[str, Any]) -> AnomalyResult:
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

        anomalib_keys = ["pred_score", "pred_label", "pred_mask", "anomaly_map"]
        if not all(key in outputs for key in anomalib_keys):
            predictions = outputs[next(iter(self.outputs))]

            if len(predictions.shape) == 1:
                npred_score = predictions
            else:
                anomaly_map = predictions.squeeze()
                npred_score = anomaly_map.reshape(-1).max()

            labels_list = self.params.labels
            pred_label = labels_list[1] if npred_score > self.params.image_threshold else labels_list[0]

            assert anomaly_map is not None
            pred_mask = (anomaly_map >= self.params.pixel_threshold).astype(np.uint8)
            anomaly_map = self._normalize(anomaly_map, self.params.pixel_threshold)

            # normalize
            npred_score = self._normalize(npred_score, self.params.image_threshold)

            if pred_label == labels_list[0]:  # normal
                npred_score = 1 - npred_score  # Score of normal is 1 - score of anomaly
            pred_score = npred_score.item()
        else:
            pred_score = outputs["pred_score"].item()
            pred_label = str(outputs["pred_label"].item())
            anomaly_map = outputs["anomaly_map"].squeeze()
            pred_mask = outputs["pred_mask"].squeeze().astype(np.uint8)

        anomaly_map *= 255
        anomaly_map = np.round(anomaly_map).astype(np.uint8)

        if anomaly_map is not None:
            anomaly_map = cv2.resize(
                anomaly_map,
                (meta["original_shape"][1], meta["original_shape"][0]),
            )

        pred_mask = cv2.resize(
            pred_mask,
            (meta["original_shape"][1], meta["original_shape"][0]),
        )

        if self.params.task == "detection":
            pred_boxes = self._get_boxes(pred_mask)

        return AnomalyResult(
            anomaly_map=anomaly_map,
            pred_boxes=pred_boxes,
            pred_label=pred_label,
            pred_mask=pred_mask,
            pred_score=pred_score,
        )

    @classmethod
    def parameters(cls) -> dict:
        parameters = super().parameters()
        parameters.update(ParameterRegistry.ANOMALY)
        parameters.update(ParameterRegistry.LABELS)
        return parameters

    def _normalize(self, tensor: np.ndarray, threshold: float) -> np.ndarray:
        """Currently supports only min-max normalization."""
        normalized = ((tensor - threshold) / self.params.normalization_scale) + 0.5
        return np.clip(normalized, 0, 1)

    @staticmethod
    def _get_boxes(mask: np.ndarray) -> np.ndarray:
        """Get bounding boxes from mask.

        Args:
            mask (np.ndarray): Input mask of shape (H, W)

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
