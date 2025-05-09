# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module contains helper functions for evaluation."""

from collections.abc import Sequence

import numpy as np
from iai_core.entities.shapes import Rectangle


def intersection_box(box1: Rectangle, box2: Rectangle) -> list[float] | None:
    """
    Calculate the intersection box of two bounding boxes.

    :param box1: a Rectangle that represents the first bounding box
    :param box2: a Rectangle that represents the second bounding box
    :return: a Rectangle that represents the intersection box if inputs have a valid intersection, else None
    """
    x_left = max(box1.x1, box2.x1)
    y_top = max(box1.y1, box2.y1)
    x_right = min(box1.x2, box2.x2)
    y_bottom = min(box1.y2, box2.y2)
    if x_right <= x_left or y_bottom <= y_top:
        return None
    return [x_left, y_top, x_right, y_bottom]


def intersection_over_union(box1: Rectangle, box2: Rectangle, intersection: list[float] | None = None) -> float:
    """
    Calculate the Intersection over Union (IoU) of two bounding boxes.

    :parm box1: a Rectangle representing a bounding box
    :parm box2: a Rectangle representing a second bounding box
    :parm intersection: precomputed intersection between two boxes (see intersection_box function), if exists.

    :return: intersection-over-union of box1 and box2
    """
    iou = 0.0
    if intersection is None:
        intersection = intersection_box(box1, box2)
    if intersection is not None:
        intersection_area = (intersection[2] - intersection[0]) * (intersection[3] - intersection[1])
        box1_area = (box1.x2 - box1.x1) * (box1.y2 - box1.y1)
        box2_area = (box2.x2 - box2.x1) * (box2.y2 - box2.y1)
        union_area = float(box1_area + box2_area - intersection_area)
        if union_area != 0:
            iou = intersection_area / union_area
    if iou < 0.0 or iou > 1.0:
        raise ValueError(f"intersection over union should be in range [0,1], instead got iou={iou}")
    return iou


def get_iou_matrix(
    ground_truth: Sequence[tuple[float, float, float, float, str, float]],
    predicted: Sequence[tuple[float, float, float, float, str, float]],
) -> np.ndarray:
    """
    Constructs an iou matrix of shape [num_ground_truth_boxes, num_predicted_boxes].

    Each cell(x,y) in the iou matrix contains the intersection over union of ground truth box(x) and predicted box(y)
    An iou matrix corresponds to a single image

    :param ground_truth: list of ground truth boxes.
        Each box is a list of (x,y) coordinates and a label.
        a box: [x1: float, y1, x2, y2, class: str, score: float]
        boxes_per_image: [box1, box2, …]
        boxes1: [boxes_per_image_1, boxes_per_image_2, boxes_per_image_3, …]
    :param predicted: list of predicted boxes.
        Each box is a list of (x,y) coordinates and a label.
        a box: [x1: float, y1, x2, y2, class: str, score: float]
        boxes_per_image: [box1, box2, …]
        boxes2: [boxes_per_image_1, boxes_per_image_2, boxes_per_image_3, …]
    :return: IoU matrix of shape [ground_truth_boxes, predicted_boxes]
    """
    gt_rects = [Rectangle(x1=x1, y1=y1, x2=x2, y2=y2) for x1, y1, x2, y2, *_ in ground_truth]
    pred_rects = [Rectangle(x1=x1, y1=y1, x2=x2, y2=y2) for x1, y1, x2, y2, *_ in predicted]
    return np.array([[intersection_over_union(gts, preds) for preds in pred_rects] for gts in gt_rects])


def get_n_false_negatives(iou_matrix: np.ndarray, iou_threshold: float) -> int:
    """
    Get the number of false negatives inside the IoU matrix for a given threshold.

    The first loop accounts for all the ground truth boxes which do not have a high enough iou with any predicted
    box (they go undetected)
    The second loop accounts for the much rarer case where two ground truth boxes are detected by the same predicted
    box. The principle is that each ground truth box requires a unique prediction box

    :param iou_matrix: IoU matrix of shape [ground_truth_boxes, predicted_boxes]
    :param iou_threshold: IoU threshold to use for the false negatives.
    :return: Number of false negatives
    """
    n_false_negatives = 0
    for row in iou_matrix:
        if max(row) < iou_threshold:
            n_false_negatives += 1
    for column in np.rot90(iou_matrix):
        indices = np.where(column > iou_threshold)
        n_false_negatives += max(len(indices[0]) - 1, 0)
    return n_false_negatives
