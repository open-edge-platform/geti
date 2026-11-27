#
# Copyright (C) 2020-2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#

from __future__ import annotations

from collections import namedtuple
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import cv2
import numpy as np

from model_api.models.result import Contour, InstanceSegmentationResult, RotatedSegmentationResult

topk_namedtuple = namedtuple("topk_namedtuple", ["values", "indices"])


if TYPE_CHECKING:
    from model_api.models.result.detection import DetectionResult


@dataclass
class ResizeMetadata:
    """Image resize transformation metadata.

    Contains parameters needed to transform coordinates (e.g., bounding boxes,
    keypoints) from model input space back to the original image space. It handles different
    resize strategies including standard resize, fit-to-window, and letterbox modes.

    Attributes:
        inverted_scale_x: Scale factor to multiply x-coordinates to map from model to original space.
        inverted_scale_y: Scale factor to multiply y-coordinates to map from model to original space.
        pad_left: Left padding added during letterbox resize (0 for other resize types).
        pad_top: Top padding added during letterbox resize (0 for other resize types).
    """

    inverted_scale_x: float
    inverted_scale_y: float
    pad_left: int = 0
    pad_top: int = 0

    @classmethod
    def compute(
        cls,
        original_width: int,
        original_height: int,
        model_width: int,
        model_height: int,
        resize_type: str,
    ) -> "ResizeMetadata":
        """Compute resize metadata for coordinate transformation.

        Args:
            original_width: Width of the original input image.
            original_height: Height of the original input image.
            model_width: Width of the model input (after resize).
            model_height: Height of the model input (after resize).
            resize_type: Type of resize applied ("standard", "fit_to_window", "fit_to_window_letterbox").

        Returns:
            ResizeMetadata instance with computed scale factors and padding.
        """
        inverted_scale_x = original_width / model_width
        inverted_scale_y = original_height / model_height
        pad_left = 0
        pad_top = 0

        if resize_type in ("fit_to_window", "fit_to_window_letterbox"):
            inverted_scale_x = inverted_scale_y = max(inverted_scale_x, inverted_scale_y)
            if resize_type == "fit_to_window_letterbox":
                pad_left = (model_width - round(original_width / inverted_scale_x)) // 2
                pad_top = (model_height - round(original_height / inverted_scale_y)) // 2

        return cls(
            inverted_scale_x=inverted_scale_x,
            inverted_scale_y=inverted_scale_y,
            pad_left=pad_left,
            pad_top=pad_top,
        )

    def to_dict(self) -> dict[str, float | int]:
        """Convert to dictionary for storage in metadata.

        Returns:
            Dictionary with keys matching the legacy resize_info format.
        """
        return {
            "inverted_scale_x": self.inverted_scale_x,
            "inverted_scale_y": self.inverted_scale_y,
            "pad_left": self.pad_left,
            "pad_top": self.pad_top,
        }

    @classmethod
    def from_dict(cls, data: dict[str, float | int]) -> "ResizeMetadata":
        """Create from dictionary (e.g., from metadata).

        Args:
            data: Dictionary with resize info keys.

        Returns:
            ResizeMetadata instance.
        """
        return cls(
            inverted_scale_x=data["inverted_scale_x"],
            inverted_scale_y=data["inverted_scale_y"],
            pad_left=int(data.get("pad_left", 0)),
            pad_top=int(data.get("pad_top", 0)),
        )


def add_rotated_rects(inst_seg_result: InstanceSegmentationResult) -> RotatedSegmentationResult:
    objects_with_rects = []
    for mask in inst_seg_result.masks:
        mask = mask.astype(np.uint8)
        contours, _ = cv2.findContours(
            mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE,
        )
        # Check if contours were found before processing
        if contours:
            contour = np.vstack(contours)
            rotated_rect = cv2.minAreaRect(contour)
            # Adjust angle to be in (0, 90] range
            (cx, cy), (w, h), angle = rotated_rect
            while angle <= 0:
                (w, h) = (h, w)
                angle += 90
            while angle > 90:
                (w, h) = (h, w)
                angle -= 90
            objects_with_rects.append(((cx, cy), (w, h), angle))
        else:
            objects_with_rects.append(((0, 0), (0, 0), 0))
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
    boxes: np.ndarray,
    scores: np.ndarray,
    iou_threshold: float,
    include_boundaries: bool = False,
    max_predictions: int = 0,
) -> list[int]:
    x1 = boxes[:, 0]
    y1 = boxes[:, 1]
    x2 = boxes[:, 2]
    y2 = boxes[:, 3]
    b = 1 if include_boundaries else 0
    areas = (x2 - x1 + b) * (y2 - y1 + b)
    order = scores.argsort()[::-1]

    if max_predictions:
        order = order[:max_predictions]

    keep = []
    while order.size > 0:
        i = order[0]
        keep.append(i.item())

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

        order = order[np.where(overlap <= iou_threshold)[0] + 1]

    return keep


def multiclass_nms(
    boxes: np.ndarray,
    scores: np.ndarray,
    labels: np.ndarray,
    iou_threshold: float = 0.45,
    max_predictions: int = 200,
    include_boundaries: bool = False,
) -> list[int]:
    """Multi-class NMS.

    strategy: in order to perform NMS independently per class,
    we add an offset to all the boxes. The offset is dependent
    only on the class idx, and is large enough so that boxes
    from different classes do not overlap

    Args:
        boxes (np.ndarray): boxes in form x1, y1, x2, y2
        scores (np.ndarray): detection scores
        labels (np.ndarray): label indices for each box
        iou_threshold (float, optional): IoU threshold. Defaults to 0.45.
        max_predictions (int, optional): Max number of objects filter. Zero means no limit. Defaults to 200.
        include_boundaries (bool, optional): Whether to include box boundaries in IoU calculation. Defaults to False.

    Returns:
        indices of kept boxes.
    """
    if not boxes.size:
        return []
    max_coordinate = boxes.max()
    offsets = labels.astype(boxes.dtype) * (max_coordinate + 1)
    boxes_for_nms = boxes + offsets[:, None]

    keep = nms(
        boxes=boxes_for_nms,
        scores=scores,
        iou_threshold=iou_threshold,
        include_boundaries=include_boundaries,
    )
    if max_predictions > 0:
        keep = keep[:max_predictions]
    return keep


def calculate_nms(
    boxes: np.ndarray,
    scores: np.ndarray,
    labels: np.ndarray,
    iou_threshold: float = 0.45,
    max_predictions: int = 200,
    include_boundaries: bool = False,
    agnostic_nms: bool = False,
    execute_nms: bool = False,
) -> list[int]:
    if not execute_nms:
        return list(range(boxes.shape[0]))

    if agnostic_nms:
        return nms(
            boxes=boxes,
            scores=scores,
            iou_threshold=iou_threshold,
            max_predictions=max_predictions,
            include_boundaries=include_boundaries,
        )

    return multiclass_nms(
        boxes=boxes,
        scores=scores,
        labels=labels,
        iou_threshold=iou_threshold,
        max_predictions=max_predictions,
        include_boundaries=include_boundaries,
    )


def is_softmaxed(array: np.ndarray, axis: int, atol: float = 1e-5) -> bool:
    """Check if the input array is softmaxed along the specified axis."""
    # Check values are in [0, 1]
    if not np.all((array >= 0) & (array <= 1)):
        return False
    # Check sum along axis is close to 1
    sums = np.sum(array, axis=axis)
    return np.allclose(sums, 1.0, atol=atol)


def softmax(logits: np.ndarray, eps: float = 1e-9, axis=None, keepdims: bool = False) -> np.ndarray:
    exp = np.exp(logits - np.max(logits))
    return exp / (np.sum(exp, axis=axis, keepdims=keepdims) + eps)


def top_k(array: np.ndarray, k: int, axis: int) -> topk_namedtuple:
    """Returns the top k values and their indices along the specified axis."""
    # Get indices of the top k elements
    indices = np.take(np.argpartition(array, -k, axis=axis), range(-k, 0), axis=axis)
    # Gather the top k values
    topk_values = np.take_along_axis(array, indices, axis=axis)
    # Sort the top k values and indices in descending order
    sorted_order = np.argsort(-topk_values, axis=axis)
    topk_values = np.take_along_axis(topk_values, sorted_order, axis=axis)
    indices = np.take_along_axis(indices, sorted_order, axis=axis)
    return topk_namedtuple(values=topk_values, indices=indices)
