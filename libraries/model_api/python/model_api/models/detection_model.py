#
# Copyright (C) 2020-2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#

import numpy as np

from .image_model import ImageModel
from .result import DetectionResult
from .types import ListValue, NumericalValue, StringValue
from .utils import load_labels


class DetectionModel(ImageModel):
    """An abstract wrapper for object detection model

    The DetectionModel must have a single image input.
    It inherits `preprocess` from `ImageModel` wrapper. Also, it defines `_resize_detections` method,
    which should be used in `postprocess`, to clip bounding boxes and resize ones to original image shape.

    The `postprocess` method must be implemented in a specific inherited wrapper.
    """

    __model__ = "DetectionModel"

    def __init__(self, inference_adapter, configuration: dict = {}, preload=False):
        """Detection Model constructor

        It extends the `ImageModel` construtor.

        Args:
            inference_adapter (InferenceAdapter): allows working with the specified executor
            configuration (dict, optional): it contains values for parameters accepted by specific
              wrapper (`confidence_threshold`, `labels` etc.) which are set as data attributes
            preload (bool, optional): a flag whether the model is loaded to device while
              initialization. If `preload=False`, the model must be loaded via `load` method before inference

        Raises:
            WrapperError: if the model has more than 1 image inputs
        """
        super().__init__(inference_adapter, configuration, preload)
        self.path_to_labels: str
        self.confidence_threshold: float
        if not self.image_blob_name:
            self.raise_error(
                f"The Wrapper supports only one image input, but {len(self.image_blob_names)} found",
            )

        if self.path_to_labels:
            self.labels = load_labels(self.path_to_labels)

    @classmethod
    def parameters(cls):
        parameters = super().parameters()
        parameters.update(
            {
                "confidence_threshold": NumericalValue(
                    default_value=0.5,
                    description="Probability threshold value for bounding box filtering",
                ),
                "labels": ListValue(description="List of class labels"),
                "path_to_labels": StringValue(
                    description="Path to file with labels. Overrides the labels, if they sets via 'labels' parameter",
                ),
            },
        )

        return parameters

    def _resize_detections(self, detection_result: DetectionResult, meta: dict):
        """Resizes detection bounding boxes according to initial image shape.

        It implements image resizing depending on the set `resize_type`(see `ImageModel` for details).
        Next, it applies bounding boxes clipping.

        Args:
            detection_result (DetectionList): detection result with coordinates in normalized form
            meta (dict): the input metadata obtained from `preprocess` method
        """
        input_img_height, input_img_widht = meta["original_shape"][:2]
        inverted_scale_x = input_img_widht / self.w
        inverted_scale_y = input_img_height / self.h
        pad_left = 0
        pad_top = 0
        if self.resize_type == "fit_to_window" or self.resize_type == "fit_to_window_letterbox":
            inverted_scale_x = inverted_scale_y = max(
                inverted_scale_x,
                inverted_scale_y,
            )
            if self.resize_type == "fit_to_window_letterbox":
                pad_left = (self.w - round(input_img_widht / inverted_scale_x)) // 2
                pad_top = (self.h - round(input_img_height / inverted_scale_y)) // 2

        boxes = detection_result.bboxes
        boxes[:, 0::2] = (boxes[:, 0::2] * self.w - pad_left) * inverted_scale_x
        boxes[:, 1::2] = (boxes[:, 1::2] * self.h - pad_top) * inverted_scale_y
        np.round(boxes, out=boxes)
        boxes[:, 0::2] = np.clip(boxes[:, 0::2], 0, input_img_widht)
        boxes[:, 1::2] = np.clip(boxes[:, 1::2], 0, input_img_height)
        detection_result.bboxes = boxes.astype(np.int32)

    def _filter_detections(self, detection_result: DetectionResult, box_area_threshold=0.0):
        """Filters detections by confidence threshold and box size threshold

        Args:
            detection_result (DetectionResult): DetectionResult object with coordinates in normalized form
            box_area_threshold (float): minimal area of the bounding to be considered

        Returns:
            - list of detections with confidence above the threshold
        """
        keep = (detection_result.get_obj_sizes() > box_area_threshold) & (
            detection_result.scores > self.confidence_threshold
        )
        detection_result.bboxes = detection_result.bboxes[keep]
        detection_result.labels = detection_result.labels[keep]
        detection_result.scores = detection_result.scores[keep]

    def _add_label_names(self, detection_result: DetectionResult) -> None:
        """Adds labels names to detections if they are available

        Args:
            detection_result (List[Detection]): list of detections with coordinates in normalized form
        """
        detection_result.label_names = [self.get_label_name(label_idx) for label_idx in detection_result.labels]
