#
# Copyright (C) 2020-2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#

from __future__ import annotations  # TODO: remove when Python3.9 support is dropped

from pathlib import Path

import cv2
import numpy as np

from .result_types import Contour, SegmentedObject, SegmentedObjectWithRects


def add_rotated_rects(segmented_objects):
    objects_with_rects = []
    for segmented_object in segmented_objects:
        mask = segmented_object.mask.astype(np.uint8)
        contours, _ = cv2.findContours(
            mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE,
        )

        contour = np.vstack(contours)
        objects_with_rects.append(
            SegmentedObjectWithRects(segmented_object, cv2.minAreaRect(contour)),
        )
    return objects_with_rects


def get_contours(
    segmentedObjects: list[SegmentedObject | SegmentedObjectWithRects],
):
    combined_contours = []
    for obj in segmentedObjects:
        contours, _ = cv2.findContours(
            obj.mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_NONE,
        )
        # Assuming one contour output for findContours. Based on OTX this is a safe
        # assumption
        if len(contours) != 1:
            msg = "findContours() must have returned only one contour"
            raise RuntimeError(msg)
        combined_contours.append(Contour(str(obj.str_label), obj.score, contours[0]))
    return combined_contours


def clip_detections(detections, size):
    for detection in detections:
        detection.xmin = min(max(round(detection.xmin), 0), size[1])
        detection.ymin = min(max(round(detection.ymin), 0), size[0])
        detection.xmax = min(max(round(detection.xmax), 0), size[1])
        detection.ymax = min(max(round(detection.ymax), 0), size[0])
    return detections


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


def nms(x1, y1, x2, y2, scores, thresh, include_boundaries=False, keep_top_k=0):
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
    detections,
    iou_threshold=0.45,
    max_num=200,
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

    keep = nms(*boxes_for_nms.T, scores, iou_threshold)
    if max_num > 0:
        keep = keep[:max_num]
    keep = np.array(keep)
    det = detections[keep]
    return det, keep


def softmax(logits, axis=None, keepdims=False):
    exp = np.exp(logits - np.max(logits))
    return exp / np.sum(exp, axis=axis, keepdims=keepdims)
