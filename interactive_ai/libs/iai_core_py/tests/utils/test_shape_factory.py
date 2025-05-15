"""This UnitTest tests ShapeFactory functionality"""

# Copyright (C) 2021-2022 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#

import pytest

from iai_core.entities.shapes import Ellipse, Keypoint, Point, Polygon, Rectangle
from iai_core.utils.shape_factory import ShapeFactory


class TestShapeFactory:
    def test_rectangle_shape_conversion(self):
        """
        <b>Description:</b>
        Checks that conversions from Rectangle to other shapes works correctly

        <b>Input data:</b>
        A rectangle at [0.25, 0.1, 0.5, 0.3]

        <b>Expected results:</b>
        The test passes if the rectangle can be converted to Ellipse and Polygon

        <b>Steps</b>
        1. Create rectangle and get coordinates
        2. Convert to Ellipse
        3. Convert to Polygon
        4. Convert to Rectangle
        """
        rectangle = Rectangle(x1=0.25, y1=0.1, x2=0.5, y2=0.3)
        rectangle_coords = (rectangle.x1, rectangle.y1, rectangle.x2, rectangle.y2)

        ellipse = ShapeFactory.shape_as_ellipse(rectangle)
        assert isinstance(ellipse, Ellipse)
        assert (ellipse.x1, ellipse.y1, ellipse.x2, ellipse.y2) == rectangle_coords

        polygon = ShapeFactory.shape_as_polygon(rectangle)
        assert isinstance(polygon, Polygon)
        assert (
            polygon.min_x,
            polygon.min_y,
            polygon.max_x,
            polygon.max_y,
        ) == rectangle_coords

        rectangle2 = ShapeFactory.shape_as_rectangle(rectangle)
        assert isinstance(rectangle2, Rectangle)
        assert rectangle == rectangle2

    def test_ellipse_shape_conversion(self):
        """
        <b>Description:</b>
        Checks that conversions from Ellipse to other shapes works correctly

        <b>Input data:</b>
        A rectangle at [0.1, 0.1, 0.5, 0.2]

        <b>Expected results:</b>
        The test passes if the Ellipse can be converted to Rectangle and Polygon

        <b>Steps</b>
        1. Create Ellipse and get coordinates
        2. Convert to Ellipse
        3. Convert to Polygon
        4. Convert to Rectangle
        """
        ellipse = Ellipse(x1=0.1, y1=0.1, x2=0.5, y2=0.2)
        ellipse_coords = (ellipse.x1, ellipse.y1, ellipse.x2, ellipse.y2)

        ellipse2 = ShapeFactory.shape_as_ellipse(ellipse)
        assert isinstance(ellipse, Ellipse)
        assert ellipse == ellipse2

        polygon = ShapeFactory.shape_as_polygon(ellipse)
        assert isinstance(polygon, Polygon)
        assert polygon.min_x == pytest.approx(ellipse.x1, 0.1)
        assert polygon.min_y == pytest.approx(ellipse.y1, 0.1)
        assert polygon.max_x == pytest.approx(ellipse.x2, 0.1)
        assert polygon.max_y == pytest.approx(ellipse.y2, 0.1)

        rectangle = ShapeFactory.shape_as_rectangle(ellipse)
        assert isinstance(rectangle, Rectangle)
        assert (
            rectangle.x1,
            rectangle.y1,
            rectangle.x2,
            rectangle.y2,
        ) == ellipse_coords

    def test_polygon_shape_conversion(self):
        """
        <b>Description:</b>
        Checks that conversions from Polygon to other shapes works correctly

        <b>Input data:</b>
        A Polygon at [[0.01, 0.2], [0.35, 0.2], [0.35, 0.4]]

        <b>Expected results:</b>
        The test passes if the Polygon can be converted to Rectangle and Ellipse

        <b>Steps</b>
        1. Create rectangle and get coordinates
        2. Convert to Ellipse
        3. Convert to Polygon
        4. Convert to Rectangle
        """
        point1 = Point(x=0.01, y=0.2)
        point2 = Point(x=0.35, y=0.2)
        point3 = Point(x=0.35, y=0.4)
        polygon = Polygon(points=[point1, point2, point3])
        polygon_coords = (polygon.min_x, polygon.min_y, polygon.max_x, polygon.max_y)

        ellipse = ShapeFactory.shape_as_ellipse(polygon)
        assert isinstance(ellipse, Ellipse)
        assert (ellipse.x1, ellipse.y1, ellipse.x2, ellipse.y2) == polygon_coords

        polygon2 = ShapeFactory.shape_as_polygon(polygon)
        assert isinstance(polygon2, Polygon)
        assert polygon == polygon2

        rectangle = ShapeFactory.shape_as_rectangle(polygon)
        assert isinstance(rectangle, Rectangle)
        assert (
            rectangle.x1,
            rectangle.y1,
            rectangle.x2,
            rectangle.y2,
        ) == polygon_coords

    def test_produces_valid_crop(self):
        """
        <b>Description:</b>
        Checks that shape_produces_valid_crop returns the correct values and
        does not raise errors

        <b>Input data:</b>
        A valid Rectangle at [0, 0.4, 1, 0.5]
        An invalid out-of-bounds Rectangle
        A valid Polygon at [[0.01, 0.1], [0.35, 0.1], [0.35, 0.1], [0.35, 0.4]]
        An invalid Polygon that has a dimensionless bounding box
        An invalid out-of-bounds Polygon
        A valid Ellipse at [0.1, 0.1, 0.5, 0.2]
        An invalid out-of-bounds Ellipse
        An invalid Keypoint

        <b>Expected results:</b>
        The test passes if the various shapes follow the rules of producing a valid crop

        <b>Steps</b>
        1. Check valid Rectangle
        2. Check invalid out-of-bounds Rectangle
        3. Check valid Polygon
        4. Check invalid dimensionless Polygon
        5. Check invalid out-of-bounds Polygon
        6. Check valid ellipse
        7. Check invalid out-of-bounds ellipse
        8. Check invalid keypoint (All keypoints are invalid)
        """
        rectangle = Rectangle(x1=0, y1=0.4, x2=1, y2=0.5)
        assert ShapeFactory.shape_produces_valid_crop(rectangle)

        rectangle = Rectangle(x1=-0.6, y1=0.4, x2=1, y2=0.5)
        assert not ShapeFactory.shape_produces_valid_crop(rectangle)

        point1 = Point(x=0.01, y=0.1)
        point2 = Point(x=0.35, y=0.1)
        point3 = Point(x=0.35, y=0.1)
        point4 = Point(x=0.35, y=0.4)
        point5 = Point(x=-0.35, y=0.4)
        polygon = Polygon(points=[point1, point2, point3, point4])
        assert ShapeFactory.shape_produces_valid_crop(polygon)

        polygon = Polygon(points=[point1, point2, point3])
        assert ShapeFactory.shape_produces_valid_crop(polygon)

        polygon = Polygon(points=[point1, point2, point3, point4, point5])
        assert not ShapeFactory.shape_produces_valid_crop(polygon)

        ellipse = Ellipse(x1=0.1, y1=0.1, x2=0.5, y2=0.2)
        assert ShapeFactory.shape_produces_valid_crop(ellipse)

        ellipse = Ellipse(x1=-0.1, y1=0.1, x2=0.5, y2=0.2)
        assert not ShapeFactory.shape_produces_valid_crop(ellipse)

        keypoint = Keypoint(x=0.1, y=0.1, is_visible=True)
        assert ShapeFactory.shape_produces_valid_crop(keypoint)
