# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from unittest.mock import patch

import pytest
from shapely.errors import TopologicalError

from sc_sdk.entities.annotation import Annotation
from sc_sdk.entities.label import NullLabel, distinct_colors
from sc_sdk.entities.shapes import Ellipse, GeometryException, Keypoint, Point, Polygon, Rectangle
from sc_sdk.entities.shapes import Rectangle as SDK_Rectangle
from tests.test_helpers import assert_almost_equal


class TestShapes:
    def test_normalize_denormalize_rectangle(self) -> None:
        """
        <b>Description:</b>
        Check that a rectangle can be correctly normalized and denormalized based on a ROI

        <b>Input data:</b>
        A rectangle
        A Region of Interest

        <b>Expected results:</b>
        Test passes if the normalized and then denormalized rectangle has almost exactly the same dimensions

        <b>Steps</b>
        1. Create Rectangle and ROI
        2. Normalize and denormalize rectangle
        3. Compare original rectangle with denormalized rectangle
        """
        rectangle = Rectangle(x1=0.25, x2=0.5, y1=0.1, y2=0.3)
        roi = Annotation(Rectangle(x1=0.15, x2=0.6, y1=0.0, y2=0.4), labels=[])
        rectangle_normalized = rectangle.normalize_wrt_roi_shape(roi.shape)
        rectangle_denormalized = rectangle_normalized.denormalize_wrt_roi_shape(roi.shape)
        assert_almost_equal(
            first=rectangle.x1,
            second=rectangle_denormalized.x1,
            delta=0.0000001,
            msg="Expected the denormalized x1 to be equal to the input Rectangle",
        )
        assert_almost_equal(
            first=rectangle.y1,
            second=rectangle_denormalized.y1,
            delta=0.0000001,
            msg="Expected the denormalized y1 to be equal to the input Rectangle",
        )
        assert_almost_equal(
            first=rectangle.width,
            second=rectangle_denormalized.width,
            delta=0.0000001,
            msg="Expected the denormalized width to be equal to the input Rectangle",
        )
        assert_almost_equal(
            first=rectangle.height,
            second=rectangle_denormalized.height,
            delta=0.0000001,
            msg="Expected the denormalized height to be equal to the input Rectangle",
        )

    def test_normalize_denormalize_ellipse(self) -> None:
        """
        <b>Description:</b>
        Check that an ellipse can be correctly normalized and denormalized based on a ROI

        <b>Input data:</b>
        An ellipse
        A Region of Interest

        <b>Expected results:</b>
        Test passes if the normalized and then denormalized ellipse has almost exactly the same dimensions

        <b>Steps</b>
        1. Create an Ellipse and ROI
        2. Normalize and denormalize the ellipse
        3. Compare original ellipse with denormalized ellipse
        """
        ellipse = Ellipse(x1=0.35, y1=0.2, x2=0.45, y2=0.4)
        roi = Rectangle(x1=0.15, x2=0.6, y1=0.0, y2=0.4)
        ellipse_normalized = ellipse.normalize_wrt_roi_shape(roi)
        ellipse_denormalized = ellipse_normalized.denormalize_wrt_roi_shape(roi)
        assert_almost_equal(
            first=ellipse.x1,
            second=ellipse_denormalized.x1,
            delta=0.0000001,
            msg="Expected the denormalized x1 to be equal to the input Ellipse",
        )
        assert_almost_equal(
            first=ellipse.y1,
            second=ellipse_denormalized.y1,
            delta=0.0000001,
            msg="Expected the denormalized y1 to be equal to the input Ellipse",
        )
        assert_almost_equal(
            first=ellipse.x2,
            second=ellipse_denormalized.x2,
            delta=0.0000001,
            msg="Expected the denormalized r to be equal to the input Ellipse",
        )

    def test_normalize_denormalize_polygon(self) -> None:
        """
        <b>Description:</b>
        Check that a polygon  can be correctly normalized and denormalized based on a ROI

        <b>Input data:</b>
        A polygon
        A Region of Interest

        <b>Expected results:</b>
        Test passes if the normalized and then denormalized polygon has almost exactly the same dimensions

        <b>Steps</b>
        1. Create polygon and ROI
        2. Normalize and denormalize polygon
        3. Compare original polygon with denormalized polygon
        """
        point1 = Point(x=0.35, y=0.2)
        point2 = Point(x=0.35, y=0.2)
        point3 = Point(x=0.35, y=0.2)
        polygon = Polygon(points=[point1, point2, point3])
        roi = Rectangle(x1=0.15, x2=0.6, y1=0.0, y2=0.4)
        polygon_normalized = polygon.normalize_wrt_roi_shape(roi)
        polygon_denormalized = polygon_normalized.denormalize_wrt_roi_shape(roi)
        for i in range(len(polygon.points)):
            point_original = polygon.points[i]
            point_denormalized = polygon_denormalized.points[i]
            assert_almost_equal(
                first=point_original.x,
                second=point_denormalized.x,
                delta=0.0000001,
                msg="Expected the denormalized x1 to be equal to the input Point",
            )
            assert_almost_equal(
                first=point_original.y,
                second=point_denormalized.y,
                delta=0.0000001,
                msg="Expected the denormalized y1 to be equal to the input Point",
            )

    def test_normalize_denormalize_keypoint(self) -> None:
        """
        <b>Description:</b>
        Check that a keypoint can be correctly normalized and denormalized based on a ROI

        <b>Input data:</b>
        A keypoint
        A Region of Interest

        <b>Expected results:</b>
        Test passes if the normalized and then denormalized keypoint has almost exactly the same dimensions

        <b>Steps</b>
        1. Create keypoint and ROI
        2. Normalize and denormalize polygon
        3. Compare original keypoint with denormalized keypoint
        """
        keypoint = Keypoint(x=0.35, y=0.2, is_visible=True)
        roi = SDK_Rectangle(x1=0.15, x2=0.6, y1=0.0, y2=0.4)
        keypoint_normalized = keypoint.normalize_wrt_roi_shape(roi)
        keypoint_denormalized = keypoint_normalized.denormalize_wrt_roi_shape(roi)
        assert_almost_equal(
            first=keypoint.x,
            second=keypoint_denormalized.x,
            delta=0.0000001,
            msg="Expected the denormalized x to be equal to the input Keypoint",
        )
        assert_almost_equal(
            first=keypoint.y,
            second=keypoint_denormalized.y,
            delta=0.0000001,
            msg="Expected the denormalized y to be equal to the input Keypoint",
        )

    @staticmethod
    def __generate_three_shapes() -> tuple[Polygon, Rectangle, Ellipse]:
        """
        Generate three shapes (Polygon, Rectangle, Ellipse).
        The polygon intersects the ellipse and the rectangle.
        The rectangle intersects the polygon, but not the ellipse.
        The ellipse intersect the polygon, but not the rectangle.
        :return: Tuple of shapes
        """
        polygon_points = [
            Point(0.566, 0.711),
            Point(0.596, 0.388),
            Point(0.637, 0.38),
            Point(0.64, 0.381),
            Point(0.675, 0.399),
            Point(0.681, 0.404),
            Point(0.69, 0.411),
            Point(0.697, 0.418),
            Point(0.761, 0.799),
        ]

        colors = distinct_colors(3)
        polygon_label = NullLabel()
        polygon_label.color = colors[0]
        ellipse_label = NullLabel()
        ellipse_label.color = colors[1]
        rect_label = NullLabel()
        rect_label.color = colors[2]

        polygon = Polygon(points=polygon_points)
        rectangle = Rectangle(x1=0.324, y1=0.617, x2=0.582, y2=0.864)
        ellipse = Ellipse(x1=0.56, y1=0.3, x2=0.653, y2=0.393)
        return polygon, rectangle, ellipse

    def test_intersections(self) -> None:
        """
        <b>Description:</b>
        Check that intersecting shapes are correctly detected

        <b>Input data:</b>
        An intersecting polygon, rectangle and ellipse

        <b>Expected results:</b>
        Test passes if each shapes intersects with the others

        <b>Steps</b>
        1. Create Polygon, Rectangle and Ellipse
        2. Convert shapes to shapely polygon
        3. Check that all polygons intersect
        """
        polygon, rectangle, ellipse = self.__generate_three_shapes()
        polygon_s = polygon._as_shapely_polygon()
        rectangle_s = rectangle._as_shapely_polygon()
        ellipse_s = ellipse._as_shapely_polygon()
        assert ellipse_s.intersects(polygon_s), "Expected the Ellipse to intersect the Polygon"
        assert not ellipse_s.intersects(rectangle_s), "Expected the Ellipse to not intersect the Rectangle"

        assert polygon_s.intersects(ellipse_s), "Expected the Polygon to intersect the Ellipse"
        assert polygon_s.intersects(rectangle_s), "Expected the Polygon to intersect the Rectangle"

        assert not rectangle_s.intersects(ellipse_s), "Expected the Rectangle to not intersect the Ellipse"
        assert rectangle_s.intersects(polygon_s), "Expected the Rectangle to intersect the Polygon"

    def test_polygon_intersection(self) -> None:
        """
        <b>Description:</b>
        Check that intersection between two polygons is detected

        <b>Input data:</b>
        Two intersecting polygons

        <b>Expected results:</b>
        Test passes if the intersection is detected

        <b>Steps</b>
        1. Create polygons
        2. Check for intersection
        """
        polygon_1 = Ellipse(x1=0.3, y1=0.4, x2=0.5, y2=0.8)
        polygon_2 = Ellipse(x1=0.2, y1=0.3, x2=0.4, y2=0.5)
        assert polygon_1.intersects(polygon_2)

    def test_intersection_error(self) -> None:
        """
        <b>Description:</b>
        Test that checking for intersection of a polygon that is a single point raises an error

        <b>Input data:</b>
        A polygon with three points with the same dimension
        A Rectangle

        <b>Expected results:</b>
        Test passes if a GeometryException is raised

        <b>Steps</b>
        1. Create polygons
        2. Attempt to check for intersection
        """
        point1 = Point(x=0.35, y=0.2)
        point2 = Point(x=0.35, y=0.2)
        point3 = Point(x=0.35, y=0.2)
        polygon_1 = Polygon(points=[point1, point2, point3])
        polygon_2 = Rectangle(x1=0.15, x2=0.6, y1=0.0, y2=0.4)

        with patch(
            "shapely.geometry.base.BaseGeometry.intersects",
            side_effect=TopologicalError("error"),
        ):
            with pytest.raises(GeometryException):
                polygon_1.intersects(polygon_2)

    def test_area(self) -> None:
        """
        <b>Description:</b>
        Check that area of shapes is calculated correctly

        <b>Input data:</b>
        Various shapes

        <b>Expected results:</b>
        Test passes if each shape has an area equal to the precomputed area

        <b>Steps</b>
        1. Check valid polygons
        2. Check invalid polygons
        """
        assert Rectangle(0, 0, 1, 1).get_area() == 1
        assert Rectangle(0.5, 0.5, 1, 1).get_area() == 0.25
        assert_almost_equal(first=Ellipse(x1=0, y1=0, x2=0.8, y2=0.4).get_area(), second=0.251, places=2)
        assert Polygon([Point(0.0, 0.0), Point(0.0, 1.0), Point(1.0, 1.0)]).get_area() == 0.5
        # Test that invalid polygons don't raise errors
        assert Polygon([Point(0.0, 0.0), Point(0.0, 0.0), Point(0.0, 0.0)]).get_area() == 0.0
        assert Polygon([Point(0.0, 1.0), Point(0.0, 1.0), Point(0.0, 0.0)]).get_area() == 0.0
        assert (
            Polygon(
                [
                    Point(0.0, 0.0),
                    Point(0.0, 0.5),
                    Point(0.0, 0.0),
                    Point(0.0, 0.5),
                    Point(0.5, 1.0),
                    Point(1.0, 1.0),
                ]
            ).get_area()
            == 0.375
        )
