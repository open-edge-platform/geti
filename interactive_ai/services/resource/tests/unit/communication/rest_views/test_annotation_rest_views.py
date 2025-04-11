# INTEL CONFIDENTIAL
#
# Copyright (C) 2021 Intel Corporation
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

from typing import Any
from unittest.mock import patch

import pytest
from testfixtures import compare

from communication.rest_views.annotation_rest_views import AnnotationRESTViews, RestShapeType
from communication.rest_views.scored_label_rest_views import ScoredLabelRESTViews
from entities.video_annotation_properties import VideoAnnotationProperties
from tests.fixtures.values import DummyValues

from geti_types import ID
from sc_sdk.entities.shapes import Point, Polygon
from sc_sdk.utils import time_utils


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

    def test_media_2d_annotations_to_rest(
        self,
        fxt_ann_scenes_list,
        fxt_ann_scenes_list_rest,
        fxt_ann_scene_states_list,
    ) -> None:
        dummy_properties = VideoAnnotationProperties(
            total_count=1,
            start_frame=0,
            end_frame=1,
            total_requested_count=1,
            requested_start_frame=0,
            requested_end_frame=1,
        )
        dummy_tasks_to_revisit_per_scene: list[Any] = [[] for _ in fxt_ann_scenes_list]
        result = AnnotationRESTViews.media_2d_annotations_to_rest(
            annotation_scenes=fxt_ann_scenes_list,
            annotation_scene_states=fxt_ann_scene_states_list,
            tasks_to_revisit_per_scene=dummy_tasks_to_revisit_per_scene,
            annotation_properties=dummy_properties,
        )
        video_annotation_properties = {
            "total_count": dummy_properties.total_count,
            "start_frame": dummy_properties.start_frame,
            "end_frame": dummy_properties.end_frame,
            "total_requested_count": dummy_properties.total_requested_count,
            "requested_start_frame": dummy_properties.requested_start_frame,
            "requested_end_frame": dummy_properties.requested_end_frame,
        }
        compare(
            result["video_annotations"],
            fxt_ann_scenes_list_rest["video_annotations"],
            ignore_eq=True,
        )
        compare(
            result["video_annotation_properties"],
            video_annotation_properties,
            ignore_eq=True,
        )
        for video_annotation in result["video_annotations"]:
            self.__assert_dimensions_are_int(annotations=video_annotation["annotations"])

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

    def test_media_2d_annotation_from_rest(
        self,
        fxt_mongo_id,
        fxt_label,
        fxt_scored_label,
        fxt_project,
        fxt_annotation_scene,
        fxt_annotation_scene_rest_response,
        fxt_media_identifier_1,
        fxt_annotation_scene_state_1,
    ):
        label = fxt_label
        label_per_id = {fxt_scored_label.label_id: label}

        (
            result,
            annotation_state,
        ) = AnnotationRESTViews.media_2d_annotation_from_rest(
            annotation_dict=fxt_annotation_scene_rest_response,
            label_per_id=label_per_id,
            kind=DummyValues.ANNOTATION_SCENE_KIND,
            last_annotator_id=DummyValues.ANNOTATION_EDITOR_NAME,
            media_identifier=fxt_media_identifier_1,
            media_height=DummyValues.MEDIA_HEIGHT,
            media_width=DummyValues.MEDIA_WIDTH,
            annotation_scene_id=fxt_mongo_id(),
        )

        compare(result, fxt_annotation_scene, ignore_ew=True)
        compare(
            annotation_state.labels_to_revisit_full_scene,
            fxt_annotation_scene_state_1.labels_to_revisit_full_scene,
            ignore_eq=True,
        )

        labels_to_revisit_per_annotation = annotation_state.labels_to_revisit_per_annotation
        assert len(labels_to_revisit_per_annotation) == len(
            fxt_annotation_scene_state_1.labels_to_revisit_per_annotation
        )
        assert all(
            key in fxt_annotation_scene_state_1.labels_to_revisit_per_annotation
            for key in labels_to_revisit_per_annotation
        )

    def test_media_2d_annotation_from_rest_without_id_or_date(
        self,
        fxt_mongo_id,
        fxt_label,
        fxt_scored_label,
        fxt_project,
        fxt_annotation_scene_rest_no_id_and_date,
        fxt_media_identifier_1,
    ):
        label = fxt_label
        label_per_id = {fxt_scored_label.label_id: label}

        date_begin = time_utils.now()
        (
            result,
            annotation_state,
        ) = AnnotationRESTViews.media_2d_annotation_from_rest(
            annotation_dict=fxt_annotation_scene_rest_no_id_and_date,
            label_per_id=label_per_id,
            kind=DummyValues.ANNOTATION_SCENE_KIND,
            last_annotator_id=DummyValues.ANNOTATION_EDITOR_NAME,
            media_identifier=fxt_media_identifier_1,
            media_height=DummyValues.MEDIA_HEIGHT,
            media_width=DummyValues.MEDIA_WIDTH,
            annotation_scene_id=fxt_mongo_id(),
        )
        date_end = time_utils.now()

        assert isinstance(result.annotations[0].id_, ID)
        assert str(result.annotations[0].id_)
        assert result.shapes[0].modification_date >= date_begin
        assert result.shapes[0].modification_date <= date_end

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

    def test_rectangle_to_rotated_rectangle(self) -> None:
        """
        Test mapping of a rectangle to a rotated rectangle.
        """
        x = 0
        y = 0
        width = 1920
        height = 1080
        x_center = (x + width) / 2
        y_center = (y + height) / 2
        rectangle = {
            "type": RestShapeType.RECTANGLE.name,
            "x": x,
            "y": y,
            "width": width,
            "height": height,
        }
        rotated_rectangle = {
            "type": RestShapeType.ROTATED_RECTANGLE.name,
            "x": x_center,
            "y": y_center,
            "width": width,
            "height": height,
            "angle": 0,
        }

        mapped_rotated_rectangle = AnnotationRESTViews.rest_rectangle_to_rest_rotated_rectangle(rectangle)

        assert mapped_rotated_rectangle == rotated_rectangle

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
