"""
 Copyright (C) 2020-2023 Intel Corporation

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

from __future__ import annotations  # TODO: remove when Python3.9 support is dropped

from collections import namedtuple
from typing import List, NamedTuple, Tuple, Union

import cv2
import numpy as np


class AnomalyResult(NamedTuple):
    """Results for anomaly models."""

    anomaly_map: np.ndarray | None = None
    pred_boxes: np.ndarray | None = None
    pred_label: str | None = None
    pred_mask: np.ndarray | None = None
    pred_score: float | None = None

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
            f"pred_score:{np.round(self.pred_score, 1)};"
            f"pred_label:{self.pred_label};"
            f"pred_mask min:{pred_mask_min} max:{pred_mask_max};"
        )


class ClassificationResult(
    namedtuple(
        "ClassificationResult", "top_labels saliency_map feature_vector raw_scores"
    )  # Contains "raw_scores", "saliency_map" and "feature_vector" model outputs if such exist
):
    def __str__(self):
        labels = ", ".join(
            f"{idx} ({label}): {confidence:.3f}"
            for idx, label, confidence in self.top_labels
        )
        return (
            f"{labels}, [{','.join(str(i) for i in self.saliency_map.shape)}], [{','.join(str(i) for i in self.feature_vector.shape)}], "
            f"[{','.join(str(i) for i in self.raw_scores.shape)}]"
        )


class Detection:
    def __init__(self, xmin, ymin, xmax, ymax, score, id, str_label=None):
        self.xmin = xmin
        self.ymin = ymin
        self.xmax = xmax
        self.ymax = ymax
        self.score = score
        self.id = int(id)
        self.str_label = str_label

    def __str__(self):
        return f"{self.xmin}, {self.ymin}, {self.xmax}, {self.ymax}, {self.id} ({self.str_label}): {self.score:.3f}"


class DetectionResult(
    namedtuple(
        "DetectionResult", "objects saliency_map feature_vector"
    )  # Contan "saliency_map" and "feature_vector" model outputs if such exist
):
    def __str__(self):
        obj_str = "; ".join(str(obj) for obj in self.objects)
        if obj_str:
            obj_str += "; "
        return f"{obj_str}[{','.join(str(i) for i in self.saliency_map.shape)}]; [{','.join(str(i) for i in self.feature_vector.shape)}]"


class SegmentedObject(Detection):
    def __init__(self, xmin, ymin, xmax, ymax, score, id, str_label, mask):
        super().__init__(xmin, ymin, xmax, ymax, score, id, str_label)
        self.mask = mask

    def __str__(self):
        return f"{super().__str__()}, {(self.mask > 0.5).sum()}"


class SegmentedObjectWithRects(SegmentedObject):
    def __init__(self, segmented_object, rotated_rect):
        super().__init__(
            segmented_object.xmin,
            segmented_object.ymin,
            segmented_object.xmax,
            segmented_object.ymax,
            segmented_object.score,
            segmented_object.id,
            segmented_object.str_label,
            segmented_object.mask,
        )
        self.rotated_rect = rotated_rect

    def __str__(self):
        res = super().__str__()
        rect = self.rotated_rect
        res += f", RotatedRect: {rect[0][0]:.3f} {rect[0][1]:.3f} {rect[1][0]:.3f} {rect[1][1]:.3f} {rect[2]:.3f}"
        return res


class InstanceSegmentationResult(NamedTuple):
    segmentedObjects: List[Union[SegmentedObject, SegmentedObjectWithRects]]
    # Contain per class saliency_maps and "feature_vector" model output if feature_vector exists
    saliency_map: List[np.ndarray]
    feature_vector: np.ndarray

    def __str__(self):
        obj_str = "; ".join(str(obj) for obj in self.segmentedObjects)
        filled = 0
        for cls_map in self.saliency_map:
            if cls_map.size:
                filled += 1
        return f"{obj_str}; {filled}; [{','.join(str(i) for i in self.feature_vector.shape)}]"


def add_rotated_rects(segmented_objects):
    objects_with_rects = []
    for segmented_object in segmented_objects:
        mask = segmented_object.mask.astype(np.uint8)
        contours, hierarchies = cv2.findContours(
            mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        contour = np.vstack(contours)
        objects_with_rects.append(
            SegmentedObjectWithRects(segmented_object, cv2.minAreaRect(contour))
        )
    return objects_with_rects


def get_contours(
    segmentedObjects: List[Union[SegmentedObject, SegmentedObjectWithRects]]
):
    combined_contours = []
    for obj in segmentedObjects:
        contours, _ = cv2.findContours(
            obj.mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE
        )
        # Assuming one contour output for findContours. Based on OTX this is a safe
        # assumption
        if len(contours) != 1:
            raise RuntimeError("findContours() must have returned only one contour")
        combined_contours.append(Contour(obj.str_label, obj.score, contours[0]))
    return combined_contours


def clip_detections(detections, size):
    for detection in detections:
        detection.xmin = min(max(round(detection.xmin), 0), size[1])
        detection.ymin = min(max(round(detection.ymin), 0), size[0])
        detection.xmax = min(max(round(detection.xmax), 0), size[1])
        detection.ymax = min(max(round(detection.ymax), 0), size[0])
    return detections


class Contour(NamedTuple):
    label: str
    probability: float
    shape: List[Tuple[int, int]]

    def __str__(self):
        return f"{self.label}: {self.probability:.3f}, {len(self.shape)}"


class ImageResultWithSoftPrediction(NamedTuple):
    resultImage: np.ndarray
    soft_prediction: np.ndarray
    # Contain per class saliency_maps and "feature_vector" model output if feature_vector exists
    saliency_map: np.ndarray  # Requires return_soft_prediction==True
    feature_vector: np.ndarray

    def __str__(self):
        outHist = cv2.calcHist(
            [self.resultImage.astype(np.uint8)],
            channels=None,
            mask=None,
            histSize=[256],
            ranges=[0, 255],
        )
        hist = ""
        for i, count in enumerate(outHist):
            if count > 0:
                hist += f"{i}: {count[0] / self.resultImage.size:.3f}, "
        return f"{hist}[{','.join(str(i) for i in self.soft_prediction.shape)}], [{','.join(str(i) for i in self.saliency_map.shape)}], [{','.join(str(i) for i in self.feature_vector.shape)}]"


class DetectionWithLandmarks(Detection):
    def __init__(self, xmin, ymin, xmax, ymax, score, id, landmarks_x, landmarks_y):
        super().__init__(xmin, ymin, xmax, ymax, score, id)
        self.landmarks = []
        for x, y in zip(landmarks_x, landmarks_y):
            self.landmarks.append((x, y))


class OutputTransform:
    def __init__(self, input_size, output_resolution):
        self.output_resolution = output_resolution
        if self.output_resolution:
            self.new_resolution = self.compute_resolution(input_size)

    def compute_resolution(self, input_size):
        self.input_size = input_size
        size = self.input_size[::-1]
        self.scale_factor = min(
            self.output_resolution[0] / size[0], self.output_resolution[1] / size[1]
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
    with open(label_file, "r") as f:
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
