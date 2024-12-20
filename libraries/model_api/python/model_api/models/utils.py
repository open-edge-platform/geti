#
# Copyright (C) 2020-2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#

from __future__ import annotations  # TODO: remove when Python3.9 support is dropped

from pathlib import Path
from typing import TYPE_CHECKING

import cv2
import numpy as np

from model_api.models.result import Contour, InstanceSegmentationResult, RotatedSegmentationResult

if TYPE_CHECKING:
    from model_api.models.result.detection import DetectionResult


def add_rotated_rects(inst_seg_result: InstanceSegmentationResult) -> RotatedSegmentationResult:
    objects_with_rects = []
    for mask in inst_seg_result.masks:
        mask = mask.astype(np.uint8)
        contours, _ = cv2.findContours(
            mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE,
        )
        contour = np.vstack(contours)
        objects_with_rects.append(cv2.minAreaRect(contour))
    return RotatedSegmentationResult(
        bboxes=inst_seg_result.bboxes,
        masks=inst_seg_result.masks,
        scores=inst_seg_result.scores,
        labels=inst_seg_result.labels,
        label_names=inst_seg_result.label_names,
        rotated_rects=objects_with_rects,
        feature_vector=inst_seg_result.feature_vector,
        saliency_map=inst_seg_result.saliency_map,
    )


def get_contours(seg_result: RotatedSegmentationResult | InstanceSegmentationResult) -> list[Contour]:
    combined_contours = []
    for mask, score, label_name in zip(
        seg_result.masks,
        seg_result.scores,
        seg_result.label_names,
    ):
        contours, _ = cv2.findContours(
            mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_NONE,
        )
        # Assuming one contour output for findContours. Based on OTX this is a safe
        # assumption
        if len(contours) != 1:
            msg = "findContours() must have returned only one contour"
            raise RuntimeError(msg)
        combined_contours.append(Contour(label=label_name, probability=score, shape=contours[0]))
    return combined_contours


def clip_detections(detections: DetectionResult, size: tuple[int, int]):
    """Clip bounding boxes to image size.

    Args:
        detections (DetectionResult): detection results including boxes, labels and scores.
        size (tuple[int, int]): image size of format (height, width).
    """
    detections.bboxes[:, 0::2] = np.clip(detections.bboxes[:, 0::2], 0, size[1])
    detections.bboxes[:, 1::2] = np.clip(detections.bboxes[:, 1::2], 0, size[0])


class OutputTransform:
    def __init__(self, input_size, output_resolution):
        self.output_resolution = output_resolution
        if self.output_resolution:
            self.new_resolution = self.compute_resolution(input_size)

    def compute_resolution(self, input_size):
        self.input_size = input_size
        size = self.input_size[::-1]
        self.scale_factor = min(
            self.output_resolution[0] / size[0],
            self.output_resolution[1] / size[1],
        )
        return self.scale(size)

    def resize(self, image):
        if not self.output_resolution:
            return image
        curr_size = image.shape[:2]
        if curr_size != self.input_size:
            self.new_resolution = self.compute_resolution(curr_size)
        if self.scale_factor == 1:
            return image
        return cv2.resize(image, self.new_resolution)

    def scale(self, inputs):
        if not self.output_resolution or self.scale_factor == 1:
            return inputs
        return (np.array(inputs) * self.scale_factor).astype(np.int32)


def load_labels(label_file):
    with Path(label_file).open() as f:
        return [x.strip() for x in f]


def nms(
    x1: np.ndarray,
    y1: np.ndarray,
    x2: np.ndarray,
    y2: np.ndarray,
    scores: np.ndarray,
    thresh: float,
    include_boundaries: bool = False,
    keep_top_k: int = 0,
) -> list[int]:
    b = 1 if include_boundaries else 0
    areas = (x2 - x1 + b) * (y2 - y1 + b)
    order = scores.argsort()[::-1]

    if keep_top_k:
        order = order[:keep_top_k]

    keep = []
    while order.size > 0:
        i = order[0]
        keep.append(i)

        xx1 = np.maximum(x1[i], x1[order[1:]])
        yy1 = np.maximum(y1[i], y1[order[1:]])
        xx2 = np.minimum(x2[i], x2[order[1:]])
        yy2 = np.minimum(y2[i], y2[order[1:]])

        w = np.maximum(0.0, xx2 - xx1 + b)
        h = np.maximum(0.0, yy2 - yy1 + b)
        intersection = w * h

        union_areas = areas[i] + areas[order[1:]] - intersection
        overlap = np.divide(
            intersection,
            union_areas,
            out=np.zeros_like(intersection, dtype=float),
            where=union_areas != 0,
        )

        order = order[np.where(overlap <= thresh)[0] + 1]

    return keep


def multiclass_nms(
    detections: np.ndarray,
    iou_threshold: float = 0.45,
    max_num: int = 200,
):
    """Multi-class NMS.

    strategy: in order to perform NMS independently per class,
    we add an offset to all the boxes. The offset is dependent
    only on the class idx, and is large enough so that boxes
    from different classes do not overlap

    Args:
        detections (np.ndarray): labels, scores and boxes
        iou_threshold (float, optional): IoU threshold. Defaults to 0.45.
        max_num (int, optional): Max number of objects filter. Defaults to 200.

    Returns:
        tuple: (dets, indices), Dets are boxes with scores. Indices are indices of kept boxes.
    """
    if not detections.size:
        return detections, []
    labels = detections[:, 0]
    scores = detections[:, 1]
    boxes = detections[:, 2:]
    max_coordinate = boxes.max()
    offsets = labels.astype(boxes.dtype) * (max_coordinate + 1)
    boxes_for_nms = boxes + offsets[:, None]

    keep = nms(*boxes_for_nms.T, scores=scores, thresh=iou_threshold)  # type: ignore[misc]
    if max_num > 0:
        keep = keep[:max_num]
    keep = np.array(keep)
    det = detections[keep]
    return det, keep


def softmax(logits: np.ndarray, eps: float = 1e-9, axis=None, keepdims: bool = False) -> np.ndarray:
    exp = np.exp(logits - np.max(logits))
    return exp / (np.sum(exp, axis=axis, keepdims=keepdims) + eps)
