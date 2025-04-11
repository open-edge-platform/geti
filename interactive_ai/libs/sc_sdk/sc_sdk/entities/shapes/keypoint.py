# INTEL CONFIDENTIAL
#
# Copyright (C) 2024 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and
# your use of them is governed by the express license under which they were provided to
# you ("License"). Unless the License provides otherwise, you may not use, modify, copy,
# publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is,
# with no express or implied warranties, other than those that are expressly stated
# in the License.
"""This module implements the Keypoint shape entity."""

import datetime

from shapely.geometry import Polygon as ShapelyPolygon

from sc_sdk.utils.time_utils import now

from .rectangle import Rectangle
from .shape import Shape, ShapeType


class Keypoint(Shape):
    """
    Keypoint represents a keypoint shape which is a single pixel

    Keypoints are used to annotate keypoint-detection type tasks
    - x and y represent the coordinates of the keypoint
    - is_visible indicates if the feature the keypoint represents is visible in the image

    :param x: x-coordinate of the keypoint
    :param y: y-coordinate of the keypoint
    :param is_visible: if the feature the keypoint represents is visible in the image
    :param modification_date: last modified date
    """

    def __init__(
        self,
        x: float,
        y: float,
        is_visible: bool,
        modification_date: datetime.datetime | None = None,
    ):
        modification_date = now() if modification_date is None else modification_date
        super().__init__(shape_type=ShapeType.KEYPOINT, modification_date=modification_date)
        self._validate_coordinates(x, y)

        self.x = x
        self.y = y
        self.is_visible = is_visible

    def __repr__(self) -> str:
        """
        String representation of the keypoint
        """
        return f"Keypoint(x={self.x}, y={self.y}, is_visible={self.is_visible})"

    def __eq__(self, other: object):
        """
        Returns True if `other` is a `Keypoint` with the same coordinates and visibility
        """
        if isinstance(other, Keypoint):
            return self.x == other.x and self.y == other.y and self.is_visible == other.is_visible
        return False

    def __hash__(self):
        """
        Returns the hash of the keypoint
        """
        return hash(str(self))

    def normalize_wrt_roi_shape(self, roi_shape: Rectangle) -> "Keypoint":
        """
        Transforms the keypoint from the 'roi' coordinate system to the normalized coordinate system
        """
        if not isinstance(roi_shape, Rectangle):
            raise ValueError("roi_shape has to be a Rectangle.")

        roi_shape = roi_shape.clip_to_visible_region()

        return Keypoint(
            x=self.x * roi_shape.width + roi_shape.x1,
            y=self.y * roi_shape.height + roi_shape.y1,
            is_visible=self.is_visible,
            modification_date=self.modification_date,
        )

    def denormalize_wrt_roi_shape(self, roi_shape: Rectangle) -> "Keypoint":
        """
        Transforms the keypoint from the normalized coordinate system to the 'roi' coordinate system
        """
        if not isinstance(roi_shape, Rectangle):
            raise ValueError("roi_shape has to be a Rectangle.")

        roi_shape = roi_shape.clip_to_visible_region()

        return Keypoint(
            x=(self.x - roi_shape.x1) / roi_shape.width,
            y=(self.y - roi_shape.y1) / roi_shape.height,
            is_visible=self.is_visible,
            modification_date=self.modification_date,
        )

    def _as_shapely_polygon(self) -> ShapelyPolygon:
        raise NotImplementedError

    def get_area(self) -> float:
        raise NotImplementedError
