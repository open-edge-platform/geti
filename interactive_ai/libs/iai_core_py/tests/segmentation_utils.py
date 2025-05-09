# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module implements segmentation related utilities."""

# mypy: ignore-errors

import warnings
from collections.abc import Sequence
from copy import copy
from typing import cast

import cv2
import numpy as np
from bson import ObjectId

from iai_core.entities.annotation import Annotation
from iai_core.entities.scored_label import ScoredLabel
from iai_core.entities.shapes import Point, Polygon

from geti_types import ID

Contour = list[tuple[float, float]]


def get_subcontours(contour: Contour) -> list[Contour]:
    """Splits contour into subcontours that do not have self intersections."""

    ContourInternal = list[tuple[float, float] | None]

    def find_loops(points: ContourInternal) -> list[Sequence[int]]:
        """For each consecutive pair of equivalent rows in the input matrix returns their indices."""
        _, inverse, count = np.unique(points, axis=0, return_inverse=True, return_counts=True)
        duplicates = np.where(count > 1)[0]
        indices = []
        for x in duplicates:
            y = np.nonzero(inverse == x)[0]
            for i, _ in enumerate(y[:-1]):
                indices.append(y[i : i + 2])
        return indices

    base_contour = cast(ContourInternal, copy(contour))

    # Make sure that contour is closed.
    if not np.array_equal(base_contour[0], base_contour[-1]):
        base_contour.append(base_contour[0])

    subcontours: list[Contour] = []
    loops = sorted(find_loops(base_contour), key=lambda x: x[0], reverse=True)
    for loop in loops:
        i, j = loop
        subcontour = [x for x in base_contour[i:j] if x is not None]
        subcontours.append(cast(Contour, subcontour))
        base_contour[i:j] = [None] * (j - i)

    return [i for i in subcontours if len(i) > 2]


def create_annotation_from_segmentation_map(
    hard_prediction: np.ndarray, soft_prediction: np.ndarray, label_map: dict
) -> list[Annotation]:
    """Creates polygons from the soft predictions.

    Background label will be ignored and not be converted to polygons.

    Args:
        hard_prediction: hard prediction containing the final label
            index per pixel. See function
            `create_hard_prediction_from_soft_prediction`.
        soft_prediction: soft prediction with shape H x W x N_labels,
            where soft_prediction[:, :, 0] is the soft prediction for
            background. If soft_prediction is of H x W shape, it is
            assumed that this soft prediction will be applied for all
            labels.
        label_map: dictionary mapping labels to an index. It is assumed
            that the first item in the dictionary corresponds to the
            background label and will therefore be ignored.

    Returns:
        List of shapes
    """
    height, width = hard_prediction.shape[:2]
    img_class = hard_prediction.swapaxes(0, 1)

    annotations: list[Annotation] = []
    for label_index, label in label_map.items():
        # Skip background
        if label_index == 0:
            continue

        # obtain current label soft prediction
        if len(soft_prediction.shape) == 3:
            current_label_soft_prediction = soft_prediction[:, :, label_index]
        else:
            current_label_soft_prediction = soft_prediction

        obj_group = img_class == label_index
        label_index_map = (obj_group.T.astype(int) * 255).astype(np.uint8)

        # Contour retrieval mode CCOMP (Connected components) creates a two-level
        # hierarchy of contours
        contours, hierarchies = cv2.findContours(label_index_map, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)

        if hierarchies is not None:
            for contour, hierarchy in zip(contours, hierarchies[0]):
                if len(contour) <= 2 or cv2.contourArea(contour) < 1.0:
                    continue

                if hierarchy[3] == -1:
                    # In this case a contour does not represent a hole
                    point_contour = [(point[0][0], point[0][1]) for point in contour]

                    # Split contour into subcontours that do not have self intersections.
                    subcontours = get_subcontours(point_contour)
                    for subcontour in subcontours:
                        # compute probability of the shape
                        mask = np.zeros(hard_prediction.shape, dtype=np.uint8)
                        cv2.drawContours(
                            mask,
                            np.asarray([[[x, y]] for x, y in subcontour]),
                            contourIdx=-1,
                            color=1,
                            thickness=-1,
                        )
                        probability = cv2.mean(current_label_soft_prediction, mask)[0]

                        # convert the list of points to a closed polygon
                        points = [Point(x=x / (width - 1), y=y / (height - 1)) for x, y in subcontour]
                        polygon = Polygon(points=points)

                        if polygon.get_area() > 0:
                            # Contour is a closed polygon with area > 0
                            annotations.append(
                                Annotation(
                                    shape=polygon,
                                    labels=[
                                        ScoredLabel(
                                            label_id=label.id_, is_empty=label.is_empty, probability=probability
                                        )
                                    ],
                                    id_=ID(ObjectId()),
                                )
                            )
                        else:
                            # Contour is a closed polygon with area == 0
                            warnings.warn(
                                "The geometry of the segmentation map you are converting "
                                "is not fully supported. Polygons with a area of zero "
                                "will be removed.",
                                UserWarning,
                            )
                else:
                    # If contour hierarchy[3] != -1 then contour has a parent and
                    # therefore is a hole
                    # Do not allow holes in segmentation masks to be filled silently,
                    # but trigger warning instead
                    warnings.warn(
                        "The geometry of the segmentation map you are converting is "
                        "not fully supported. A hole was found and will be filled.",
                        UserWarning,
                    )

    return annotations
