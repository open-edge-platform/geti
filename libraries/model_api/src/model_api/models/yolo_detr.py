# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""YOLO-DETR detection model wrapper."""

from __future__ import annotations

import numpy as np

from .detection_model import DetectionModel
from .result import DetectionResult


class YOLODETR(DetectionModel):
    """Detection wrapper for decoded YOLO-DETR query outputs.

    The model output is a single tensor with shape ``[1, N, 6]``. Each row is
    ``[center_x, center_y, width, height, confidence, class_id]`` with box
    coordinates normalized to the model input dimensions.
    """

    __model__ = "YOLODETR"

    def __init__(self, inference_adapter, configuration: dict = {}, preload: bool = False):
        super().__init__(inference_adapter, configuration, preload)
        self._check_io_number(1, 1)

        output = next(iter(self.outputs.values()))
        if len(output.shape) != 3:
            self.raise_error("the output must be of rank 3")
        if output.shape[0] not in (-1, 1):
            self.raise_error("the first output dimension must be 1")
        if output.shape[2] not in (-1, 6):
            self.raise_error("the last output dimension must be 6")

    @classmethod
    def parameters(cls):
        parameters = super().parameters()
        parameters["resize_type"].update_default_value("fit_to_window_letterbox")
        parameters["confidence_threshold"].update_default_value(0.5)
        parameters["nms_execute"].update_default_value(default_value=False)
        return parameters

    def postprocess(self, outputs, meta) -> DetectionResult:
        """Convert decoded normalized query detections to ModelAPI results."""
        if len(outputs) != 1:
            self.raise_error("expect 1 output")

        prediction = next(iter(outputs.values()))
        if prediction.ndim != 3 or prediction.shape[0] != 1 or prediction.shape[2] != 6:
            self.raise_error("the output must have shape [1, N, 6]")

        prediction = prediction[0]
        scores = prediction[:, 4].astype(np.float32, copy=False)
        keep = scores > self.params.confidence_threshold
        boxes = prediction[keep, :4].astype(np.float32, copy=True)
        scores = scores[keep]
        labels = prediction[keep, 5].astype(np.int32, copy=False)

        if len(boxes):
            centers = boxes[:, :2]
            half_sizes = boxes[:, 2:] / 2.0
            boxes = np.concatenate((centers - half_sizes, centers + half_sizes), axis=1)
        else:
            boxes = np.empty((0, 4), dtype=np.float32)

        detections = DetectionResult(bboxes=boxes, labels=labels, scores=scores)
        if self.params.nms_execute and len(detections):
            keep_nms = self._calculate_nms(
                boxes=detections.bboxes,
                scores=detections.scores,
                labels=detections.labels,
            )
            detections.bboxes = detections.bboxes[keep_nms]
            detections.labels = detections.labels[keep_nms]
            detections.scores = detections.scores[keep_nms]

        self._resize_detections(detections, meta)
        self._add_label_names(detections)
        return detections
