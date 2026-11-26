#
# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#

"""Custom ModelAPI wrapper for Ultralytics YOLO instance-segmentation inference."""

from __future__ import annotations

from typing import Any, cast

import numpy as np

from model_api.adapters.utils import resize_image_ocv
from model_api.models.detection_model import DetectionModel
from model_api.models.result import InstanceSegmentationResult
from model_api.models.utils import ResizeMetadata
from model_api.models.yolo import xywh2xyxy


class YOLOSeg(DetectionModel):
    """ModelAPI wrapper for YOLO instance-segmentation models.

    Expects 2 outputs:
      * detection output: ``[1, 4 + num_classes + mask_dim, num_boxes]``
      * prototype output: ``[1, mask_dim, proto_h, proto_w]``

    Post-processing:
      1. Parse detection predictions (boxes + class scores + mask coefficients).
      2. Filter by confidence, apply NMS.
      3. Decode masks: ``coefficients @ protos.reshape(mask_dim, -1)`` → sigmoid → crop → resize.
      4. Return ``InstanceSegmentationResult``.
    """

    __model__ = "YOLO-seg"

    def __init__(self, inference_adapter: object, configuration: dict | None = None, preload: bool = False) -> None:
        super().__init__(inference_adapter, configuration or {}, preload)
        self._check_io_number(1, 2)

        self._det_output_name: str = ""
        self._proto_output_name: str = ""
        outputs = cast("dict[str, Any]", self.outputs or {})

        for name, output in outputs.items():
            shape = output.shape
            if len(shape) == 3:
                self._det_output_name = name
            elif len(shape) == 4:
                self._proto_output_name = name

        if not self._det_output_name or not self._proto_output_name:
            self.raise_error(
                "Expected one rank-3 detection output and one rank-4 prototype output, "
                f"but got shapes: {[(name, out.shape) for name, out in outputs.items()]}",
            )

        det_shape = outputs[self._det_output_name].shape
        proto_shape = outputs[self._proto_output_name].shape
        self._mask_dim = proto_shape[1]
        self._proto_h = proto_shape[2]
        self._proto_w = proto_shape[3]

        self._num_classes = det_shape[1] - 4 - self._mask_dim
        if self._num_classes <= 0:
            self.raise_error(f"Detection output channel dim ({det_shape[1]}) must be > 4 + mask_dim ({self._mask_dim})")

    @classmethod
    def parameters(cls):
        parameters = super().parameters()
        parameters["pad_value"].update_default_value(114)
        parameters["resize_type"].update_default_value("fit_to_window_letterbox")
        parameters["reverse_input_channels"].update_default_value(default_value=False)
        parameters["scale_values"].update_default_value([255.0])
        parameters["confidence_threshold"].update_default_value(0.25)
        parameters["iou_threshold"].update_default_value(0.5)
        return parameters

    def postprocess(self, outputs: dict[str, Any], meta: dict[str, Any]) -> InstanceSegmentationResult:
        """Decode detections and instance masks from raw model outputs.

        Args:
            outputs: Raw model outputs keyed by output tensor name.
            meta: Preprocessing metadata from ModelAPI (original_shape, etc.).

        Returns:
            InstanceSegmentationResult with boxes in original image coordinates
            and binary masks at original image resolution.
        """
        det_output = outputs[self._det_output_name]
        proto_output = outputs[self._proto_output_name]

        prediction = det_output.astype(np.float32)
        protos = proto_output[0].astype(np.float32)

        pred = prediction[0].T

        boxes_xywh = pred[:, :4]
        class_scores = pred[:, 4 : 4 + self._num_classes]
        mask_coeffs = pred[:, 4 + self._num_classes :]

        params = cast("Any", self.params)
        conf_threshold = params.confidence_threshold
        max_scores = class_scores.max(axis=1)
        keep_conf = max_scores > conf_threshold

        if not keep_conf.any():
            return self._empty_result(meta)

        boxes_xywh = boxes_xywh[keep_conf]
        class_scores = class_scores[keep_conf]
        mask_coeffs = mask_coeffs[keep_conf]

        labels = class_scores.argmax(axis=1)
        confidences = class_scores[np.arange(len(labels)), labels]

        boxes_xyxy = xywh2xyxy(boxes_xywh.copy())

        keep_nms = self._calculate_nms(
            boxes=boxes_xyxy,
            scores=confidences,
            labels=labels.astype(np.float32),
        )
        boxes_xyxy = boxes_xyxy[keep_nms]
        confidences = confidences[keep_nms]
        labels = labels[keep_nms]
        mask_coeffs = mask_coeffs[keep_nms]

        masks = self._decode_masks(mask_coeffs, protos, boxes_xyxy, meta)

        input_img_w = meta["original_shape"][1]
        input_img_h = meta["original_shape"][0]
        resize_meta = ResizeMetadata.compute(
            original_width=input_img_w,
            original_height=input_img_h,
            model_width=self.orig_width,
            model_height=self.orig_height,
            resize_type=params.resize_type,
        )

        coords = boxes_xyxy.copy()
        coords -= (resize_meta.pad_left, resize_meta.pad_top, resize_meta.pad_left, resize_meta.pad_top)
        coords *= (
            resize_meta.inverted_scale_x,
            resize_meta.inverted_scale_y,
            resize_meta.inverted_scale_x,
            resize_meta.inverted_scale_y,
        )

        int_boxes = np.round(coords).astype(np.int32)
        np.clip(
            int_boxes,
            0,
            [input_img_w, input_img_h, input_img_w, input_img_h],
            out=int_boxes,
        )

        int_labels = labels.astype(np.int32)
        return InstanceSegmentationResult(
            bboxes=int_boxes,
            scores=confidences,
            labels=int_labels + 1,
            masks=masks,
            label_names=[self.get_label_name(i) for i in int_labels],
            saliency_map=[],
            feature_vector=np.ndarray(0),
        )

    def _decode_masks(
        self,
        mask_coeffs: np.ndarray,
        protos: np.ndarray,
        boxes_xyxy: np.ndarray,
        meta: dict,
    ) -> np.ndarray:
        """Decode instance masks from mask coefficients and prototypes.

        Args:
            mask_coeffs: Mask coefficients ``(N, mask_dim)``.
            protos: Prototype masks ``(mask_dim, proto_h, proto_w)``.
            boxes_xyxy: Bounding boxes in model input coordinates ``(N, 4)``.
            meta: Preprocessing metadata (original_shape, etc.).

        Returns:
            Binary masks at original image resolution ``(N, orig_h, orig_w)``.
        """
        mask_dim, proto_h, proto_w = protos.shape
        raw_masks = mask_coeffs @ protos.reshape(mask_dim, -1)
        raw_masks = raw_masks.reshape(-1, proto_h, proto_w)

        raw_masks = 1.0 / (1.0 + np.exp(-raw_masks))

        model_h, model_w = self.orig_height, self.orig_width
        scale_x = proto_w / model_w
        scale_y = proto_h / model_h
        proto_boxes = boxes_xyxy * np.array([scale_x, scale_y, scale_x, scale_y], dtype=np.float32)

        raw_masks = self.crop_mask(raw_masks, proto_boxes)

        input_img_h = meta["original_shape"][0]
        input_img_w = meta["original_shape"][1]

        resize_meta = ResizeMetadata.compute(
            original_width=input_img_w,
            original_height=input_img_h,
            model_width=model_w,
            model_height=model_h,
            resize_type=cast("Any", self.params).resize_type,
        )

        n = raw_masks.shape[0]
        upsampled = np.zeros((n, model_h, model_w), dtype=np.float32)
        for i in range(n):
            upsampled[i] = resize_image_ocv(raw_masks[i], (model_w, model_h))

        pad_t = resize_meta.pad_top
        pad_l = resize_meta.pad_left
        effective_w = round(input_img_w / resize_meta.inverted_scale_x)
        effective_h = round(input_img_h / resize_meta.inverted_scale_y)
        cropped = upsampled[:, pad_t : pad_t + effective_h, pad_l : pad_l + effective_w]

        final_masks = np.zeros((n, input_img_h, input_img_w), dtype=np.uint8)
        for i in range(n):
            resized = resize_image_ocv(cropped[i], (input_img_w, input_img_h))
            final_masks[i] = (resized > 0.5).astype(np.uint8)

        return final_masks

    def _empty_result(self, meta: dict) -> InstanceSegmentationResult:
        """Return an empty result when no detections pass filtering."""
        return InstanceSegmentationResult(
            bboxes=np.empty((0, 4), dtype=np.int32),
            scores=np.empty(0, dtype=np.float32),
            labels=np.empty(0, dtype=np.int32),
            masks=np.empty((0, meta["original_shape"][0], meta["original_shape"][1]), dtype=np.uint8),
            label_names=[],
            saliency_map=[],
            feature_vector=np.ndarray(0),
        )

    @staticmethod
    def crop_mask(masks: np.ndarray, boxes: np.ndarray) -> np.ndarray:
        """Zero-out mask pixels outside the bounding box.

        Args:
            masks: Binary or float masks of shape ``(N, H, W)``.
            boxes: Bounding boxes ``(N, 4)`` in xyxy format, scaled to mask dims.

        Returns:
            Cropped masks of shape ``(N, H, W)``.
        """
        n, h, w = masks.shape
        rows = np.arange(h, dtype=np.float32).reshape(1, h, 1)
        cols = np.arange(w, dtype=np.float32).reshape(1, 1, w)
        x1 = boxes[:, 0].reshape(n, 1, 1)
        y1 = boxes[:, 1].reshape(n, 1, 1)
        x2 = boxes[:, 2].reshape(n, 1, 1)
        y2 = boxes[:, 3].reshape(n, 1, 1)
        inside = (cols >= x1) & (cols < x2) & (rows >= y1) & (rows < y2)
        return masks * inside
