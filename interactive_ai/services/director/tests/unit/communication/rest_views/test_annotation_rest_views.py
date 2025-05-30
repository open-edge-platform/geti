# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from unittest.mock import patch

import pytest
from testfixtures import compare

from communication.views.annotation_rest_views import AnnotationRESTViews, RestShapeType
from communication.views.scored_label_rest_views import ScoredLabelRESTViews

from iai_core.entities.annotation import Annotation
from iai_core.entities.shapes import Point, Polygon


class TestAnnotationRESTViews:
    def test_media_2d_annotation_to_rest(
        self,
        fxt_scored_label_rest,
        fxt_annotation_scene,
        fxt_annotation_scene_rest_response,
        fxt_annotation_scene_state,
    ):
        with patch.object(
            ScoredLabelRESTViews,
            "scored_label_to_rest",
            return_value=fxt_scored_label_rest,
        ) as mock_lbl_rest:
            result = AnnotationRESTViews.media_2d_annotation_to_rest(
                annotation_scene=fxt_annotation_scene,
                annotation_scene_state=fxt_annotation_scene_state,
                tasks_to_revisit=[],
            )

            mock_lbl_rest.assert_called()
        compare(result, fxt_annotation_scene_rest_response, ignore_eq=True)
        self.__assert_dimensions_are_int(annotations=result["annotations"])

    def test_media_2d_annotation_keypoint_to_rest(
        self,
        fxt_scored_label_rest,
        fxt_annotation_scene_keypoint,
        fxt_annotation_scene_keypoint_rest_response,
        fxt_annotation_scene_state,
    ):
        with patch.object(
            ScoredLabelRESTViews,
            "scored_label_to_rest",
            return_value=fxt_scored_label_rest,
        ) as mock_lbl_rest:
            result = AnnotationRESTViews.media_2d_annotation_to_rest(
                annotation_scene=fxt_annotation_scene_keypoint,
                annotation_scene_state=fxt_annotation_scene_state,
                tasks_to_revisit=[],
            )
            mock_lbl_rest.assert_called()
        compare(result, fxt_annotation_scene_keypoint_rest_response, ignore_eq=True)
        self.__assert_dimensions_are_int(annotations=result["annotations"])

    def test_media_2d_annotation_anomaly_reduced_to_rest(
        self,
        fxt_anomalous_label,
        fxt_scored_label_rest,
        fxt_annotation_scene_anomaly_reduced,
        fxt_annotation_scene_anomaly_reduced_rest_response,
        fxt_annotation_scene_state,
    ):
        with (
            patch.object(
                ScoredLabelRESTViews,
                "scored_label_to_rest",
                return_value=fxt_scored_label_rest,
            ) as mock_lbl_rest,
            patch.object(
                Annotation,
                "get_labels",
                return_value=[fxt_anomalous_label],
            ) as mock_get_label,
        ):
            result = AnnotationRESTViews.media_2d_annotation_to_rest(
                annotation_scene=fxt_annotation_scene_anomaly_reduced,
                annotation_scene_state=fxt_annotation_scene_state,
                tasks_to_revisit=[],
            )

            mock_lbl_rest.assert_called()
            mock_get_label.assert_called()
        compare(result, fxt_annotation_scene_anomaly_reduced_rest_response, ignore_eq=True)
        self.__assert_dimensions_are_int(annotations=result["annotations"])

    def test_media_2d_annotation_to_rest_label_only(
        self,
        fxt_scored_label_rest,
        fxt_annotation_scene_label_only,
        fxt_annotation_scene_rest_label_only,
        fxt_annotation_scene_state,
    ):
        with patch.object(
            ScoredLabelRESTViews,
            "scored_label_to_rest",
            return_value=fxt_scored_label_rest,
        ) as mock_lbl_rest:
            result = AnnotationRESTViews.media_2d_annotation_to_rest(
                annotation_scene=fxt_annotation_scene_label_only,
                label_only=True,
                annotation_scene_state=fxt_annotation_scene_state,
                tasks_to_revisit=[],
            )

            mock_lbl_rest.assert_called()
        compare(result, fxt_annotation_scene_rest_label_only, ignore_eq=True)

    def test_rotated_rectangle_rest_mapper(self):
        """
        Tests mapping of a rotated rectangle
        """
        for i in range(360):
            rotated_rect_dict = {
                "x": 320,
                "y": 240,
                "width": 50,
                "height": 100,
                "angle": float(i),
                "type": RestShapeType.ROTATED_RECTANGLE.name,
            }
            rectangle = AnnotationRESTViews.rotated_rectangle_shape_from_rest(
                rotated_rect_dict, media_height=480, media_width=640
            )
            mapped_rectangle = AnnotationRESTViews.rotated_rectangle_shape_to_rest(
                rectangle, media_height=480, media_width=640
            )
            compare(mapped_rectangle, rotated_rect_dict, ignore_eq=True)

    def test_rotated_rectangle_shape_to_rest_zero_width(self) -> None:
        # Arrange
        media_height = 1080
        media_width = 1920
        p1 = Point(x=0.38802080154418944, y=0.725925925925926)
        p2 = Point(x=0.38802080154418944, y=0.3981481764051649)
        p3 = Point(x=0.8437498728434245, y=0.39814814814814814)
        p4 = Point(x=0.8437498728434245, y=0.725925925925926)
        height = 0.45572907129923507
        width = 0.32777777777777783
        # media_height and media_width are swapped since the rectangle is rotated by 90 degrees
        expected_height = height * media_width
        expected_width = width * media_height

        # Act
        polygon = Polygon(points=[p1, p2, p3, p4])
        result = AnnotationRESTViews.rotated_rectangle_shape_to_rest(
            polygon, media_height=media_height, media_width=media_width
        )

        # Assert
        assert result["height"] == pytest.approx(expected_height, 0.001)
        assert result["width"] == pytest.approx(expected_width, 0.001)

    def test_rotated_rectangle_rest_mapper_accuracy(self):
        """
        Test mapping of a rotated rectangle accuracy.
        1. Obtain a guaranteed rotated rectangle represented in polygon (in pixel coordinate system) as ground truth.
        2. Using the REST representation of rotated rectangle, obtain the internal polygon representation and compare.
        3. Using the internal representation, obtain the remapped REST representation of the rotated rectangle
            and compare.
        """
        image_width = 798
        image_height = 1092
        allowed_delta_in_normalized = 0.005
        allowed_delta_in_angle = 0.1

        # guaranteed rotated rectangle in pixel system
        ori_x_pixel = [94, 349, 616, 362]
        ori_y_pixel = [148, 71, 973, 1049]

        ori_x_norm = [xi / image_width for xi in ori_x_pixel]
        ori_y_norm = [yi / image_height for yi in ori_y_pixel]

        # manually computed rotated rectangle in pixel system
        x_center, y_center, width, height, angle = (
            355,
            560,
            266.3719,
            940.0132,
            163.4350,
        )

        rotated_rect_dict = {
            "x": x_center,
            "y": y_center,
            "width": width,
            "height": height,
            "angle": angle,
            "type": RestShapeType.ROTATED_RECTANGLE.name,
        }

        rectangle_as_polygon = AnnotationRESTViews.rotated_rectangle_shape_from_rest(
            rotated_rect_dict, image_height, image_width
        )
        for xi, yi, polygon_point in zip(ori_x_norm, ori_y_norm, rectangle_as_polygon.points):
            assert abs(xi - polygon_point.x) < allowed_delta_in_normalized
            assert abs(yi - polygon_point.y) < allowed_delta_in_normalized

        mapped_rectangle = AnnotationRESTViews.rotated_rectangle_shape_to_rest(
            rectangle_as_polygon, image_height, image_width
        )

        assert abs(mapped_rectangle["x"] - rotated_rect_dict["x"]) < allowed_delta_in_normalized
        assert abs(mapped_rectangle["y"] - rotated_rect_dict["y"]) < allowed_delta_in_normalized
        assert abs(mapped_rectangle["width"] - rotated_rect_dict["width"]) < allowed_delta_in_normalized
        assert abs(mapped_rectangle["height"] - rotated_rect_dict["height"]) < allowed_delta_in_normalized
        assert abs(mapped_rectangle["angle"] - rotated_rect_dict["angle"]) < allowed_delta_in_angle

    @staticmethod
    def __assert_dimensions_are_int(annotations: list) -> None:
        for annotation in annotations:
            shape_type = annotation["shape"]["type"]
            if shape_type in ("RECTANGLE", "ELLIPSE"):
                assert isinstance(annotation["shape"]["x"], int)
                assert isinstance(annotation["shape"]["y"], int)
                assert isinstance(annotation["shape"]["width"], int)
                assert isinstance(annotation["shape"]["height"], int)
            elif shape_type == "POLYGON":
                for point in annotation["shape"]["points"]:
                    assert isinstance(point["x"], int)
                    assert isinstance(point["y"], int)
            elif shape_type == "KEYPOINT":
                assert isinstance(annotation["shape"]["x"], int)
                assert isinstance(annotation["shape"]["y"], int)
            else:
                raise ValueError(f"Unsupported shape {shape_type}")
