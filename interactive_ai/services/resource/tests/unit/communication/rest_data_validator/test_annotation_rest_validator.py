# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from contextlib import nullcontext
from unittest.mock import PropertyMock, patch

import jsonschema
import pytest

from communication.constants import MINIMUM_PIXELS_FOR_ANNOTATION
from communication.exceptions import (
    ConflictingExclusiveLabelsException,
    DuplicatedAnnotationIDException,
    LabelNotFoundException,
)
from communication.rest_data_validator import AnnotationRestValidator
from communication.rest_views.annotation_rest_views import RestShapeType
from features.feature_flags import FeatureFlag
from service.label_schema_service import LabelSchemaService
from tests.fixtures.values import DummyValues

from geti_fastapi_tools.exceptions import BadRequestException
from geti_types import ID
from iai_core.entities.label import Domain, Label
from iai_core.entities.label_schema import LabelGroup, LabelSchema, LabelSchemaView, LabelTree
from iai_core.entities.project import Project


@pytest.fixture
def fxt_annotation_scene_rest_conflicting_labels(fxt_segmentation_label_factory):
    # annotation with multiple labels in the same group, which is not allowed
    labels = [fxt_segmentation_label_factory(i) for i in range(2)]
    scored_labels_rest = [
        {
            "id": str(label.id_),
            "name": label.name,
            "probability": 0.5,
            "color": "#ff0000ff",
        }
        for label in labels
    ]
    yield {
        "annotations": [
            {
                "shape": {
                    "type": "RECTANGLE",
                    "x": 0.3 * DummyValues.MEDIA_WIDTH,
                    "y": 0.3 * DummyValues.MEDIA_HEIGHT,
                    "width": 0.1 * DummyValues.MEDIA_WIDTH,
                    "height": 0.1 * DummyValues.MEDIA_HEIGHT,
                },
                "labels": scored_labels_rest,
            }
        ]
    }


@pytest.fixture
def fxt_annotation_scene_rest_invalid_shape_type(
    fxt_segmentation_scored_label_rest_factory,
):
    # annotation with a shape type 'circle', which isn't allowed
    yield {
        "annotations": [
            {
                "shape": {"type": "CIRCLE"},
                "labels": [fxt_segmentation_scored_label_rest_factory(2)],
            }
        ]
    }


@pytest.fixture
def fxt_annotation_scene_rest_invalid_shape(
    fxt_segmentation_scored_label_rest_factory,
):
    # annotation with a shape dictionary that is incomplete
    yield {
        "annotations": [
            {
                "shape": {
                    "type": "POLYGON",
                    "x": DummyValues.X * DummyValues.MEDIA_WIDTH,
                    "y": DummyValues.Y * DummyValues.MEDIA_HEIGHT,
                },
                "labels": [fxt_segmentation_scored_label_rest_factory(2)],
            }
        ]
    }


@pytest.fixture
def fxt_annotation_scene_rest_invalid_shape_minimum(
    fxt_detection_scored_label_rest_factory,
):
    # annotation with a shape dictionary that has x value that is too large
    yield {
        "annotations": [
            {
                "shape": {
                    "type": "RECTANGLE",
                    "x": 0,
                    "y": 0,
                    "width": 0,
                    "height": 0,
                },
                "labels": [fxt_detection_scored_label_rest_factory(2)],
            }
        ]
    }


@pytest.fixture
def fxt_annotation_scene_rest_shape_out_of_bounds(
    fxt_detection_scored_label_rest_factory,
):
    # annotation with a shape dictionary that has x value that is too large
    yield {
        "annotations": [
            {
                "shape": {
                    "type": "RECTANGLE",
                    "x": 10 * DummyValues.MEDIA_WIDTH,
                    "y": 0.1 * DummyValues.MEDIA_HEIGHT,
                    "width": 0.1 * DummyValues.MEDIA_WIDTH,
                    "height": 0.1 * DummyValues.MEDIA_HEIGHT,
                },
                "labels": [fxt_detection_scored_label_rest_factory(2)],
            }
        ]
    }


@pytest.fixture
def fxt_annotation_scene_rest_shape_out_of_bounds_2(
    fxt_detection_scored_label_rest_factory,
):
    # annotation with a shape that is out of bounds because y+height is larger than 1
    yield {
        "annotations": [
            {
                "shape": {
                    "type": "RECTANGLE",
                    "x": 0,
                    "y": 0.6 * DummyValues.MEDIA_HEIGHT,
                    "width": DummyValues.MEDIA_WIDTH + 1,
                    "height": 0.6 * DummyValues.MEDIA_HEIGHT,
                },
                "labels": [fxt_detection_scored_label_rest_factory(2)],
            }
        ]
    }


@pytest.fixture
def fxt_annotation_scene_rest_ellipse_out_of_bounds(
    fxt_segmentation_scored_label_rest_factory,
):
    # annotation with an ellipse that is out of bounds
    yield {
        "annotations": [
            {
                "shape": {
                    "type": "ELLIPSE",
                    "x": 1.5 * DummyValues.MEDIA_WIDTH,
                    "y": 0.5 * DummyValues.MEDIA_HEIGHT,
                    "width": 0.1 * DummyValues.MEDIA_WIDTH,
                    "height": 0.5 * DummyValues.MEDIA_HEIGHT,
                },
                "labels": [fxt_segmentation_scored_label_rest_factory(2)],
            }
        ]
    }


@pytest.fixture
def fxt_annotation_scene_rest_rotated_rectangle_out_of_bounds(
    fxt_segmentation_scored_label_rest_factory,
):
    # annotation with an ellipse that is out of bounds
    yield {
        "annotations": [
            {
                "shape": {
                    "type": RestShapeType.ROTATED_RECTANGLE.name,
                    "x": 1.5 * DummyValues.MEDIA_WIDTH,
                    "y": 0.5 * DummyValues.MEDIA_HEIGHT,
                    "width": 0.1 * DummyValues.MEDIA_WIDTH,
                    "height": 0.5 * DummyValues.MEDIA_HEIGHT,
                    "angle": 0.1,
                },
                "labels": [fxt_segmentation_scored_label_rest_factory(2)],
            }
        ]
    }


@pytest.fixture
def fxt_annotation_scene_rest_polygon_out_of_bounds(
    fxt_segmentation_scored_label_rest_factory,
):
    # annotation with a polygon that is out of bounds
    yield {
        "annotations": [
            {
                "shape": {
                    "type": "POLYGON",
                    "points": [
                        {
                            "x": 10 * DummyValues.MEDIA_WIDTH,
                            "y": 0.4 * DummyValues.MEDIA_HEIGHT,
                        }
                    ],
                },
                "labels": [fxt_segmentation_scored_label_rest_factory(2)],
            }
        ]
    }


@pytest.fixture
def fxt_annotation_scene_detection_non_rectangle(
    fxt_detection_scored_label_rest_factory,
):
    yield {
        "annotations": [
            {
                "shape": {
                    "type": "ELLIPSE",
                    "x": 0.2 * DummyValues.MEDIA_WIDTH,
                    "y": 0.2 * DummyValues.MEDIA_HEIGHT,
                    "width": 0.2 * DummyValues.MEDIA_WIDTH,
                    "height": 0.2 * DummyValues.MEDIA_HEIGHT,
                },
                "labels": [fxt_detection_scored_label_rest_factory(2)],
            }
        ]
    }


@pytest.fixture
def fxt_annotation_scene_classification_not_full_box(
    fxt_classification_scored_label_rest_factory,
):
    yield {
        "annotations": [
            {
                "shape": {
                    "type": "RECTANGLE",
                    "x": 0.2 * DummyValues.MEDIA_WIDTH,
                    "y": 0.2 * DummyValues.MEDIA_HEIGHT,
                    "width": 0.2 * DummyValues.MEDIA_WIDTH,
                    "height": 0.2 * DummyValues.MEDIA_HEIGHT,
                },
                "labels": [fxt_classification_scored_label_rest_factory(2)],
            }
        ]
    }


@pytest.fixture
def fxt_annotation_scene_empty_non_empty_label_coincide(fxt_detection_label, fxt_empty_detection_label):
    yield {
        "annotations": [
            {
                "shape": {
                    "type": "RECTANGLE",
                    "x": 0,
                    "y": 0,
                    "width": DummyValues.MEDIA_WIDTH,
                    "height": DummyValues.MEDIA_HEIGHT,
                },
                "labels": [
                    {
                        "id": str(fxt_empty_detection_label.id_),
                        "name": DummyValues.LABEL_NAME,
                        "probability": DummyValues.LABEL_PROBABILITY,
                        "color": "#ff0000ff",
                    }
                ],
            },
            {
                "shape": {
                    "type": "RECTANGLE",
                    "x": 0.1 * DummyValues.MEDIA_WIDTH,
                    "y": 0.1 * DummyValues.MEDIA_HEIGHT,
                    "width": 0.2 * DummyValues.MEDIA_WIDTH,
                    "height": 0.2 * DummyValues.MEDIA_HEIGHT,
                },
                "labels": [
                    {
                        "id": str(fxt_detection_label.id_),
                        "name": DummyValues.LABEL_NAME,
                        "probability": DummyValues.LABEL_PROBABILITY,
                        "color": "#ff0000ff",
                    }
                ],
            },
        ]
    }


@pytest.fixture
def fxt_annotation_scene_empty_detection_not_full_box(fxt_empty_detection_label):
    yield {
        "annotations": [
            {
                "shape": {
                    "type": "RECTANGLE",
                    "x": 0.2 * DummyValues.MEDIA_WIDTH,
                    "y": 0.2 * DummyValues.MEDIA_HEIGHT,
                    "width": 0.2 * DummyValues.MEDIA_WIDTH,
                    "height": 0.2 * DummyValues.MEDIA_HEIGHT,
                },
                "labels": [
                    {
                        "id": str(fxt_empty_detection_label.id_),
                        "name": DummyValues.LABEL_NAME,
                        "probability": DummyValues.LABEL_PROBABILITY,
                        "color": "#ff0000ff",
                    }
                ],
            }
        ]
    }


@pytest.fixture
def fxt_annotation_scene_rest_duplicate_annotation_id(
    fxt_detection_scored_label_rest_factory,
):
    scored_label = fxt_detection_scored_label_rest_factory(2)
    yield {
        "annotations": [
            {
                "id": DummyValues.UUID,
                "shape": {
                    "type": "RECTANGLE",
                    "x": 0.1 * DummyValues.MEDIA_WIDTH,
                    "y": 0.1 * DummyValues.MEDIA_HEIGHT,
                    "width": 0.1 * DummyValues.MEDIA_WIDTH,
                    "height": 0.1 * DummyValues.MEDIA_HEIGHT,
                },
                "labels": [scored_label],
            },
            {
                "id": DummyValues.UUID,
                "shape": {
                    "type": "RECTANGLE",
                    "x": 0.1 * DummyValues.MEDIA_WIDTH,
                    "y": 0.1 * DummyValues.MEDIA_HEIGHT,
                    "width": 0.1 * DummyValues.MEDIA_WIDTH,
                    "height": 0.1 * DummyValues.MEDIA_HEIGHT,
                },
                "labels": [scored_label],
            },
        ]
    }


@pytest.fixture
def fxt_annotation_scene_rest_anomaly_label_conflict(
    fxt_anomaly_segmentation_labels,
):
    scored_label_normal = {
        "id": str(fxt_anomaly_segmentation_labels[0].id_),
        "name": fxt_anomaly_segmentation_labels[0].name,
        "probability": 1,
        "color": "#ff0000ff",
    }
    scored_label_anomalous = {
        "id": str(fxt_anomaly_segmentation_labels[1].id_),
        "name": fxt_anomaly_segmentation_labels[1].name,
        "probability": 1,
        "color": "#ff0000ff",
    }
    yield {
        "annotations": [
            {
                "id": DummyValues.UUID,
                "shape": {
                    "type": "RECTANGLE",
                    "x": 0 * DummyValues.MEDIA_WIDTH,
                    "y": 0 * DummyValues.MEDIA_HEIGHT,
                    "width": 1 * DummyValues.MEDIA_WIDTH,
                    "height": 1 * DummyValues.MEDIA_HEIGHT,
                },
                "labels": [scored_label_normal],
            },
            {
                "id": DummyValues.UUID,
                "shape": {
                    "type": "RECTANGLE",
                    "x": 0.1 * DummyValues.MEDIA_WIDTH,
                    "y": 0.1 * DummyValues.MEDIA_HEIGHT,
                    "width": 0.1 * DummyValues.MEDIA_WIDTH,
                    "height": 0.1 * DummyValues.MEDIA_HEIGHT,
                },
                "labels": [scored_label_anomalous],
            },
        ]
    }


@pytest.fixture
def fxt_annotation_scene_rest_anomaly_reduced_full_box(
    fxt_anomaly_segmentation_labels,
):
    scored_label_anomalous = {
        "id": str(fxt_anomaly_segmentation_labels[1].id_),
        "name": fxt_anomaly_segmentation_labels[1].name,
        "probability": 1,
        "color": "#ff0000ff",
    }
    yield {
        "annotations": [
            {
                "id": DummyValues.UUID,
                "shape": {
                    "type": "RECTANGLE",
                    "x": 0,
                    "y": 0,
                    "width": DummyValues.MEDIA_WIDTH,
                    "height": DummyValues.MEDIA_HEIGHT,
                },
                "labels": [scored_label_anomalous],
            },
        ]
    }


@pytest.fixture
def fxt_annotation_scene_rest_anomaly_reduced_local_box(
    fxt_anomaly_segmentation_labels,
):
    scored_label_anomalous = {
        "id": str(fxt_anomaly_segmentation_labels[1].id_),
        "name": fxt_anomaly_segmentation_labels[1].name,
        "probability": 1,
        "color": "#ff0000ff",
    }
    yield {
        "annotations": [
            {
                "id": DummyValues.UUID,
                "shape": {
                    "type": "RECTANGLE",
                    "x": 0.1 * DummyValues.MEDIA_WIDTH,
                    "y": 0.1 * DummyValues.MEDIA_HEIGHT,
                    "width": 0.1 * DummyValues.MEDIA_WIDTH,
                    "height": 0.1 * DummyValues.MEDIA_HEIGHT,
                },
                "labels": [scored_label_anomalous],
            },
        ]
    }


@pytest.fixture
def fxt_video_annotation_range_valid(fxt_classification_label_schema):
    label_0, label_1 = fxt_classification_label_schema.get_labels(include_empty=True)[:2]
    yield {
        "range_labels": [
            {"start_frame": 1, "end_frame": 3, "label_ids": [str(label_0.id_)]},
            {"start_frame": 8, "end_frame": 8, "label_ids": [str(label_0.id_)]},
            {"start_frame": 5, "end_frame": 7, "label_ids": [str(label_1.id_)]},
        ]
    }


@pytest.fixture
def fxt_video_annotation_range_invalid_range_1(fxt_classification_label_schema):
    label_0 = fxt_classification_label_schema.get_labels(include_empty=True)[0]
    # invalid because end_frame < start_frame
    yield {"range_labels": [{"start_frame": 5, "end_frame": 4, "label_ids": [str(label_0.id_)]}]}


@pytest.fixture
def fxt_video_annotation_range_invalid_range_2(fxt_classification_label_schema):
    label_0 = fxt_classification_label_schema.get_labels(include_empty=True)[0]
    # invalid because start_frame is negative
    yield {"range_labels": [{"start_frame": -1, "end_frame": 4, "label_ids": [str(label_0.id_)]}]}


@pytest.fixture
def fxt_video_annotation_range_invalid_range_3(fxt_classification_label_schema):
    label_0 = fxt_classification_label_schema.get_labels(include_empty=True)[0]
    # invalid if the video has less than 1000 frames
    yield {"range_labels": [{"start_frame": 3, "end_frame": 999, "label_ids": [str(label_0.id_)]}]}


@pytest.fixture
def fxt_video_annotation_range_nonexisting_labels(fxt_mongo_id):
    yield {"range_labels": [{"start_frame": 1, "end_frame": 3, "label_ids": [str(fxt_mongo_id(12345))]}]}


def label_schema_by_task_for_single_task_project(project, label_schema) -> dict[ID, LabelSchemaView]:
    tasks = project.get_trainable_task_nodes()
    label_schema_view = LabelSchemaView.from_parent(
        parent_schema=label_schema, labels=label_schema.get_labels(True), id_=ID()
    )
    return {tasks[0].id_: label_schema_view}


class TestAnnotationRestValidator:
    def test_validate_annotation_scene_success(
        self,
        fxt_project_with_segmentation_task,
        fxt_segmentation_label_schema_factory,
        fxt_annotation_scene_rest_request,
        fxt_image_identifier_1,
    ) -> None:
        """Test validate_annotation_scene with a valid input"""
        label_schema: LabelSchema = fxt_segmentation_label_schema_factory(num_labels=3)
        label_schema_by_task = label_schema_by_task_for_single_task_project(
            fxt_project_with_segmentation_task, label_schema
        )
        AnnotationRestValidator().validate_annotation_scene(
            annotation_scene_rest=fxt_annotation_scene_rest_request,
            project=fxt_project_with_segmentation_task,
            media_identifier=fxt_image_identifier_1,
            media_width=DummyValues.MEDIA_WIDTH,
            media_height=DummyValues.MEDIA_HEIGHT,
            label_schema_by_task=label_schema_by_task,
        )

    def test_validate_annotation_scene_video_identifier(
        self,
        fxt_annotation_scene_rest_request,
        fxt_project,
        fxt_video_identifier,
        fxt_label_schema,
    ) -> None:
        """Test validate_annotation_scene with an identifier of a video"""
        label_schema_by_task = label_schema_by_task_for_single_task_project(fxt_project, fxt_label_schema)
        with pytest.raises(BadRequestException):
            AnnotationRestValidator().validate_annotation_scene(
                annotation_scene_rest=fxt_annotation_scene_rest_request,
                project=fxt_project,
                media_identifier=fxt_video_identifier,
                media_width=DummyValues.MEDIA_WIDTH,
                media_height=DummyValues.MEDIA_HEIGHT,
                label_schema_by_task=label_schema_by_task,
            )

    def test_validate_annotation_scene_empty_label_success(
        self,
        fxt_project_with_segmentation_task,
        fxt_segmentation_label_schema_factory,
        fxt_annotation_scene_rest_request_empty_label,
        fxt_image_identifier_1,
    ) -> None:
        """Test validate_annotation_scene with a scene containing an empty label"""
        label_schema: LabelSchema = fxt_segmentation_label_schema_factory(num_labels=1)
        label_schema_by_task = label_schema_by_task_for_single_task_project(
            fxt_project_with_segmentation_task, label_schema
        )
        AnnotationRestValidator().validate_annotation_scene(
            annotation_scene_rest=fxt_annotation_scene_rest_request_empty_label,
            project=fxt_project_with_segmentation_task,
            media_identifier=fxt_image_identifier_1,
            media_width=DummyValues.MEDIA_WIDTH,
            media_height=DummyValues.MEDIA_HEIGHT,
            label_schema_by_task=label_schema_by_task,
        )

    def test_validate_annotation_scene_conflicting_labels(
        self,
        fxt_project,
        fxt_segmentation_label_schema_factory,
        fxt_annotation_scene_rest_conflicting_labels,
        fxt_image_identifier_1,
    ) -> None:
        """Test validate_annotation_scene with a scene with multiple exclusive labels"""
        label_schema: LabelSchema = fxt_segmentation_label_schema_factory(num_labels=2)
        label_schema_by_task = label_schema_by_task_for_single_task_project(fxt_project, label_schema)
        with pytest.raises(ConflictingExclusiveLabelsException):
            AnnotationRestValidator().validate_annotation_scene(
                annotation_scene_rest=fxt_annotation_scene_rest_conflicting_labels,
                project=fxt_project,
                media_identifier=fxt_image_identifier_1,
                media_width=DummyValues.MEDIA_WIDTH,
                media_height=DummyValues.MEDIA_HEIGHT,
                label_schema_by_task=label_schema_by_task,
            )

    def test_validate_annotation_scene_invalid_shape_type(
        self,
        fxt_annotation_scene_rest_invalid_shape_type,
        fxt_project,
        fxt_image_identifier_1,
        fxt_label_schema,
    ) -> None:
        """Test validate_annotation_scene with a scene containing invalid shape types"""
        label_schema_by_task = label_schema_by_task_for_single_task_project(fxt_project, fxt_label_schema)
        with pytest.raises(BadRequestException):
            AnnotationRestValidator().validate_annotation_scene(
                annotation_scene_rest=fxt_annotation_scene_rest_invalid_shape_type,
                project=fxt_project,
                media_identifier=fxt_image_identifier_1,
                media_width=DummyValues.MEDIA_WIDTH,
                media_height=DummyValues.MEDIA_HEIGHT,
                label_schema_by_task=label_schema_by_task,
            )

    def test_validate_annotation_scene_invalid_shape(
        self,
        fxt_annotation_scene_rest_invalid_shape,
        fxt_project,
        fxt_image_identifier_1,
        fxt_label_schema,
    ) -> None:
        """Test validate_annotation_scene with a scene containing invalid shapes"""
        label_schema_by_task = label_schema_by_task_for_single_task_project(fxt_project, fxt_label_schema)
        with pytest.raises(jsonschema.exceptions.ValidationError):
            AnnotationRestValidator().validate_annotation_scene(
                annotation_scene_rest=fxt_annotation_scene_rest_invalid_shape,
                project=fxt_project,
                media_identifier=fxt_image_identifier_1,
                media_width=DummyValues.MEDIA_WIDTH,
                media_height=DummyValues.MEDIA_HEIGHT,
                label_schema_by_task=label_schema_by_task,
            )

    def test_validate_annotation_scene_label_not_found(
        self,
        fxt_project,
        fxt_empty_label_schema,
        fxt_annotation_scene_rest_request,
        fxt_image_identifier_1,
    ) -> None:
        """
        Test validate_annotation_scene with a scene containing a label
        that is not part of the schema
        """
        label_schema_by_task = label_schema_by_task_for_single_task_project(fxt_project, fxt_empty_label_schema)
        with pytest.raises(LabelNotFoundException):
            AnnotationRestValidator().validate_annotation_scene(
                annotation_scene_rest=fxt_annotation_scene_rest_request,
                project=fxt_project,
                media_identifier=fxt_image_identifier_1,
                media_width=DummyValues.MEDIA_WIDTH,
                media_height=DummyValues.MEDIA_HEIGHT,
                label_schema_by_task=label_schema_by_task,
            )

    def test_validate_annotation_scene_non_rectangle_in_detection_project(
        self,
        fxt_project_with_detection_task,
        fxt_detection_label_schema_factory,
        fxt_annotation_scene_detection_non_rectangle,
        fxt_image_identifier_1,
        fxt_detection_task,
    ) -> None:
        """
        Test validate_annotation_scene on a detection project with a scene containing
        a detection label that is not rectangular.
        """
        label_schema: LabelSchema = fxt_detection_label_schema_factory(num_labels=2)
        with (
            patch.object(Project, "tasks", new_callable=PropertyMock) as mock_task_list,
            pytest.raises(
                BadRequestException,
                match="Only rectangle annotations are allowed for a detection task.",
            ),
        ):
            mock_task_list.return_value = [fxt_detection_task]
            label_schema_by_task = label_schema_by_task_for_single_task_project(
                fxt_project_with_detection_task, label_schema
            )
            AnnotationRestValidator().validate_annotation_scene(
                annotation_scene_rest=fxt_annotation_scene_detection_non_rectangle,
                project=fxt_project_with_detection_task,
                media_identifier=fxt_image_identifier_1,
                media_width=DummyValues.MEDIA_WIDTH,
                media_height=DummyValues.MEDIA_HEIGHT,
                label_schema_by_task=label_schema_by_task,
            )

    def test_validate_annotation_scene_invalid_classification_shape(
        self,
        fxt_project,
        fxt_classification_label_schema_factory,
        fxt_annotation_scene_classification_not_full_box,
        fxt_image_identifier_1,
        fxt_classification_task,
    ) -> None:
        """
        Test validate_annotation_scene on a classification project with a scene
        containing a classification label whose shape is not the full image.
        """
        label_schema: LabelSchema = fxt_classification_label_schema_factory(num_labels=2)
        with (
            patch.object(Project, "tasks", new_callable=PropertyMock) as mock_task_list,
            pytest.raises(
                BadRequestException,
                match="Only full box rectangle annotations are allowed for a classification label on a full image.",
            ),
        ):
            mock_task_list.return_value = [fxt_classification_task]
            label_schema_by_task = label_schema_by_task_for_single_task_project(fxt_project, label_schema)

            AnnotationRestValidator().validate_annotation_scene(
                annotation_scene_rest=fxt_annotation_scene_classification_not_full_box,
                project=fxt_project,
                media_identifier=fxt_image_identifier_1,
                media_width=DummyValues.MEDIA_WIDTH,
                media_height=DummyValues.MEDIA_HEIGHT,
                label_schema_by_task=label_schema_by_task,
            )

    def test_validate_annotation_scene_invalid_shape_minimum(
        self,
        fxt_project,
        fxt_detection_label_schema_factory,
        fxt_annotation_scene_rest_invalid_shape_minimum,
        fxt_image_identifier_1,
        fxt_detection_task,
    ) -> None:
        """Test validate_annotation_scene with a scene containing out-of-bound shapes"""
        label_schema: LabelSchema = fxt_detection_label_schema_factory(num_labels=2)
        with (
            patch.object(Project, "tasks", new_callable=PropertyMock) as mock_task_list,
            pytest.raises(
                BadRequestException,
                match=("One or more RECTANGLE shapes have invalid width: 0 is less than the minimum of 1."),
            ),
        ):
            mock_task_list.return_value = [fxt_detection_task]
            label_schema_by_task = label_schema_by_task_for_single_task_project(fxt_project, label_schema)

            AnnotationRestValidator().validate_annotation_scene(
                annotation_scene_rest=fxt_annotation_scene_rest_invalid_shape_minimum,
                project=fxt_project,
                media_identifier=fxt_image_identifier_1,
                media_width=DummyValues.MEDIA_WIDTH,
                media_height=DummyValues.MEDIA_HEIGHT,
                label_schema_by_task=label_schema_by_task,
            )

    def test_validate_annotation_scene_shape_out_of_bounds_1(
        self,
        fxt_project,
        fxt_detection_label_schema_factory,
        fxt_annotation_scene_rest_shape_out_of_bounds,
        fxt_image_identifier_1,
        fxt_detection_task,
    ) -> None:
        """Test validate_annotation_scene with a scene containing out-of-bound shapes"""
        label_schema: LabelSchema = fxt_detection_label_schema_factory(num_labels=2)
        with (
            patch.object(Project, "tasks", new_callable=PropertyMock) as mock_task_list,
            pytest.raises(BadRequestException),
        ):
            mock_task_list.return_value = [fxt_detection_task]
            label_schema_by_task = label_schema_by_task_for_single_task_project(fxt_project, label_schema)

            AnnotationRestValidator().validate_annotation_scene(
                annotation_scene_rest=fxt_annotation_scene_rest_shape_out_of_bounds,
                project=fxt_project,
                media_identifier=fxt_image_identifier_1,
                media_width=DummyValues.MEDIA_WIDTH,
                media_height=DummyValues.MEDIA_HEIGHT,
                label_schema_by_task=label_schema_by_task,
            )

    def test_validate_annotation_scene_shape_out_of_bounds_2(
        self,
        fxt_project,
        fxt_detection_label_schema_factory,
        fxt_annotation_scene_rest_shape_out_of_bounds_2,
        fxt_image_identifier_1,
        fxt_detection_task,
    ) -> None:
        """Test validate_annotation_scene with a scene containing out-of-bound shapes"""
        label_schema: LabelSchema = fxt_detection_label_schema_factory(num_labels=2)
        with (
            patch.object(Project, "tasks", new_callable=PropertyMock) as mock_task_list,
            pytest.raises(
                BadRequestException,
                match="Shape out of bounds for annotation with type RECTANGLE and dimensions "
                "x=0, y=288.0, width=641, height=288.0",
            ),
        ):
            mock_task_list.return_value = [fxt_detection_task]
            label_schema_by_task = label_schema_by_task_for_single_task_project(fxt_project, label_schema)

            AnnotationRestValidator().validate_annotation_scene(
                annotation_scene_rest=fxt_annotation_scene_rest_shape_out_of_bounds_2,
                project=fxt_project,
                media_identifier=fxt_image_identifier_1,
                media_width=DummyValues.MEDIA_WIDTH,
                media_height=DummyValues.MEDIA_HEIGHT,
                label_schema_by_task=label_schema_by_task,
            )

    def test_validate_annotation_scene_shape_out_of_bounds_3(
        self,
        fxt_project,
        fxt_segmentation_label_schema_factory,
        fxt_annotation_scene_rest_ellipse_out_of_bounds,
        fxt_image_identifier_1,
        fxt_segmentation_task,
    ) -> None:
        """Test validate_annotation_scene with a scene containing out-of-bound shapes"""
        label_schema: LabelSchema = fxt_segmentation_label_schema_factory(num_labels=2)
        with (
            patch.object(Project, "tasks", new_callable=PropertyMock) as mock_task_list,
            pytest.raises(
                BadRequestException,
                match=f"Shape out of bounds for annotation with type ELLIPSE and dimensions "
                f"x=960.0, y=240.0, width=64.0, height=240.0: "
                f"this shape needs to have at least {MINIMUM_PIXELS_FOR_ANNOTATION} pixels within the image.",
            ),
        ):
            mock_task_list.return_value = [fxt_segmentation_task]
            label_schema_by_task = label_schema_by_task_for_single_task_project(fxt_project, label_schema)

            AnnotationRestValidator().validate_annotation_scene(
                annotation_scene_rest=fxt_annotation_scene_rest_ellipse_out_of_bounds,
                project=fxt_project,
                media_identifier=fxt_image_identifier_1,
                media_width=DummyValues.MEDIA_WIDTH,
                media_height=DummyValues.MEDIA_HEIGHT,
                label_schema_by_task=label_schema_by_task,
            )

    def test_validate_annotation_scene_shape_out_of_bounds_4(
        self,
        fxt_project,
        fxt_segmentation_label_schema_factory,
        fxt_annotation_scene_rest_polygon_out_of_bounds,
        fxt_image_identifier_1,
        fxt_segmentation_task,
    ) -> None:
        """Test validate_annotation_scene with a scene containing out-of-bound shapes"""
        label_schema: LabelSchema = fxt_segmentation_label_schema_factory(num_labels=2)
        with (
            patch.object(Project, "tasks", new_callable=PropertyMock) as mock_task_list,
            pytest.raises(
                BadRequestException,
                match="Polygon point out of bounds with coordinates x=6400, y=192.0",
            ),
        ):
            mock_task_list.return_value = [fxt_segmentation_task]
            label_schema_by_task = label_schema_by_task_for_single_task_project(fxt_project, label_schema)

            AnnotationRestValidator().validate_annotation_scene(
                annotation_scene_rest=fxt_annotation_scene_rest_polygon_out_of_bounds,
                project=fxt_project,
                media_identifier=fxt_image_identifier_1,
                media_width=DummyValues.MEDIA_WIDTH,
                media_height=DummyValues.MEDIA_HEIGHT,
                label_schema_by_task=label_schema_by_task,
            )

    def test_validate_annotation_scene_shape_out_of_bounds_5(
        self,
        fxt_project,
        fxt_segmentation_label_schema_factory,
        fxt_annotation_scene_rest_rotated_rectangle_out_of_bounds,
        fxt_image_identifier_1,
        fxt_segmentation_task,
    ) -> None:
        """Test validate_annotation_scene with a scene containing out-of-bound shapes"""
        label_schema: LabelSchema = fxt_segmentation_label_schema_factory(num_labels=2)
        with (
            patch.object(Project, "tasks", new_callable=PropertyMock) as mock_task_list,
            pytest.raises(
                BadRequestException,
                match=f"Shape out of bounds for annotation with type ROTATED_RECTANGLE and dimensions "
                f"x=960.0, y=240.0, width=64.0, height=240.0, angle=0.1: "
                f"this shape needs to have at least {MINIMUM_PIXELS_FOR_ANNOTATION} pixels within the image.",
            ),
        ):
            mock_task_list.return_value = [fxt_segmentation_task]
            label_schema_by_task = label_schema_by_task_for_single_task_project(fxt_project, label_schema)

            AnnotationRestValidator().validate_annotation_scene(
                annotation_scene_rest=fxt_annotation_scene_rest_rotated_rectangle_out_of_bounds,
                project=fxt_project,
                media_identifier=fxt_image_identifier_1,
                media_width=DummyValues.MEDIA_WIDTH,
                media_height=DummyValues.MEDIA_HEIGHT,
                label_schema_by_task=label_schema_by_task,
            )

    def test_validate_annotation_scene_classification_label_without_detection(
        self,
        fxt_detection_classification_chain_project,
        fxt_detection_classification_label_schema_factory,
        fxt_annotation_scene_classification_not_full_box,
        fxt_image_identifier_1,
    ) -> None:
        """
        Test validate_annotation_scene on a detection->classification chain project
        with an annotation containing a classification label but not a detection one.
        """
        det_task, cls_task = fxt_detection_classification_chain_project.get_trainable_task_nodes()

        def _get_labels_for_task(task_node_id: ID):
            label_schema: LabelSchema = fxt_detection_classification_label_schema_factory()
            domain = Domain.DETECTION if task_node_id == det_task.id_ else Domain.CLASSIFICATION
            return {lbl for lbl in label_schema.get_labels(True) if lbl.domain == domain}

        label_schema_by_task = {
            det_task.id_: LabelSchemaView.from_labels(
                task_node_id=det_task.id_, labels=_get_labels_for_task(det_task.id_)
            ),
            cls_task.id_: LabelSchemaView.from_labels(
                task_node_id=cls_task.id_, labels=_get_labels_for_task(cls_task.id_)
            ),
        }

        with pytest.raises(
            BadRequestException,
            match="Annotation for a global task is missing a label for the preceding task.",
        ):
            AnnotationRestValidator().validate_annotation_scene(
                annotation_scene_rest=fxt_annotation_scene_classification_not_full_box,
                project=fxt_detection_classification_chain_project,
                media_identifier=fxt_image_identifier_1,
                media_width=DummyValues.MEDIA_WIDTH,
                media_height=DummyValues.MEDIA_HEIGHT,
                label_schema_by_task=label_schema_by_task,  # type: ignore
            )

    def test_validate_annotation_scene_empty_detection_label_not_full_box(
        self,
        fxt_detection_classification_chain_project,
        fxt_detection_classification_label_schema_factory,
        fxt_annotation_scene_empty_detection_not_full_box,
        fxt_image_identifier_1,
    ) -> None:
        """
        Test validate_annotation_scene on a detection->classification chain project
        with an annotation containing an empty detection label whose shape is not
        the full image.
        """
        det_task, cls_task = fxt_detection_classification_chain_project.get_trainable_task_nodes()

        def _get_labels_for_task(task_node_id: ID):
            label_schema: LabelSchema = fxt_detection_classification_label_schema_factory()
            domain = Domain.DETECTION if task_node_id == det_task.id_ else Domain.CLASSIFICATION
            return {lbl for lbl in label_schema.get_labels(True) if lbl.domain == domain}

        label_schema_by_task = {
            det_task.id_: LabelSchemaView.from_labels(
                task_node_id=det_task.id_, labels=_get_labels_for_task(det_task.id_)
            ),
            cls_task.id_: LabelSchemaView.from_labels(
                task_node_id=cls_task.id_, labels=_get_labels_for_task(cls_task.id_)
            ),
        }

        with pytest.raises(
            BadRequestException,
            match="Empty label for the first task must be a full box rectangle.",
        ):
            AnnotationRestValidator().validate_annotation_scene(
                annotation_scene_rest=fxt_annotation_scene_empty_detection_not_full_box,
                project=fxt_detection_classification_chain_project,
                media_identifier=fxt_image_identifier_1,
                media_width=DummyValues.MEDIA_WIDTH,
                media_height=DummyValues.MEDIA_HEIGHT,
                label_schema_by_task=label_schema_by_task,  # type: ignore
            )

    def test_validate_annotation_scene_empty_non_empty_labels_overlap(
        self,
        fxt_project_with_detection_task,
        fxt_detection_label_schema_factory,
        fxt_annotation_scene_empty_non_empty_label_coincide,
        fxt_image_identifier_1,
    ) -> None:
        """
        Test validate_annotation_scene on a detection project that contains two
        annotations, one of which is the empty one.
        """
        label_schema: LabelSchema = fxt_detection_label_schema_factory(num_labels=1)
        label_schema_by_task = label_schema_by_task_for_single_task_project(
            fxt_project_with_detection_task, label_schema
        )
        with pytest.raises(
            BadRequestException,
            match="Not allowed to create annotation that overlaps with an empty box annotation.",
        ):
            AnnotationRestValidator().validate_annotation_scene(
                annotation_scene_rest=fxt_annotation_scene_empty_non_empty_label_coincide,
                project=fxt_project_with_detection_task,
                media_identifier=fxt_image_identifier_1,
                media_width=DummyValues.MEDIA_WIDTH,
                media_height=DummyValues.MEDIA_HEIGHT,
                label_schema_by_task=label_schema_by_task,
            )

    def test_validate_annotation_scene_duplicate_annotation_id(
        self,
        fxt_project_with_detection_task,
        fxt_detection_label_schema_factory,
        fxt_annotation_scene_rest_duplicate_annotation_id,
        fxt_image_identifier_1,
    ) -> None:
        """
        Test validate_annotation_scene on a detection project that contains two
        annotations with the same ID.
        """
        label_schema: LabelSchema = fxt_detection_label_schema_factory(num_labels=1)
        label_schema_by_task = label_schema_by_task_for_single_task_project(
            fxt_project_with_detection_task, label_schema
        )
        with pytest.raises(
            DuplicatedAnnotationIDException,
        ):
            AnnotationRestValidator().validate_annotation_scene(
                annotation_scene_rest=fxt_annotation_scene_rest_duplicate_annotation_id,
                project=fxt_project_with_detection_task,
                media_identifier=fxt_image_identifier_1,
                media_width=DummyValues.MEDIA_WIDTH,
                media_height=DummyValues.MEDIA_HEIGHT,
                label_schema_by_task=label_schema_by_task,
            )

    def test_validate_annotation_scene_anomalous_label_conflict(
        self,
        fxt_project_with_anomaly_detection_task,
        fxt_anomaly_segmentation_label_schema,
        fxt_annotation_scene_rest_anomaly_label_conflict,
        fxt_image_identifier_1,
    ) -> None:
        """
        Test validate_annotation_scene on a detection project that contains two
        annotations with the same ID.
        """
        label_schema_by_task = label_schema_by_task_for_single_task_project(
            fxt_project_with_anomaly_detection_task,
            fxt_anomaly_segmentation_label_schema,
        )
        with pytest.raises(
            BadRequestException,
        ):
            AnnotationRestValidator().validate_annotation_scene(
                annotation_scene_rest=fxt_annotation_scene_rest_anomaly_label_conflict,
                project=fxt_project_with_anomaly_detection_task,
                media_identifier=fxt_image_identifier_1,
                media_width=DummyValues.MEDIA_WIDTH,
                media_height=DummyValues.MEDIA_HEIGHT,
                label_schema_by_task=label_schema_by_task,
            )

    def test_validate_annotation_scene_anomalous_global_local(
        self,
        fxt_project_with_anomaly_detection_task,
        fxt_anomaly_segmentation_label_schema,
        fxt_anomaly_segmentation_labels,
        fxt_annotation_scene_rest_anomaly_reduced_full_box,
        fxt_annotation_scene_rest_anomaly_reduced_local_box,
        fxt_image_identifier_1,
        fxt_enable_feature_flag_name,
    ) -> None:
        """
        Test validate_annotation_scene on a detection project that contains two
        annotations with the same ID.
        """
        fxt_enable_feature_flag_name(FeatureFlag.FEATURE_FLAG_ANOMALY_REDUCTION.name)
        label_schema_by_task = label_schema_by_task_for_single_task_project(
            fxt_project_with_anomaly_detection_task,
            fxt_anomaly_segmentation_label_schema,
        )

        AnnotationRestValidator().validate_annotation_scene(
            annotation_scene_rest=fxt_annotation_scene_rest_anomaly_reduced_full_box,
            project=fxt_project_with_anomaly_detection_task,
            media_identifier=fxt_image_identifier_1,
            media_width=DummyValues.MEDIA_WIDTH,
            media_height=DummyValues.MEDIA_HEIGHT,
            label_schema_by_task=label_schema_by_task,
        )

        with pytest.raises(
            BadRequestException,
        ):
            AnnotationRestValidator().validate_annotation_scene(
                annotation_scene_rest=fxt_annotation_scene_rest_anomaly_reduced_local_box,
                project=fxt_project_with_anomaly_detection_task,
                media_identifier=fxt_image_identifier_1,
                media_width=DummyValues.MEDIA_WIDTH,
                media_height=DummyValues.MEDIA_HEIGHT,
                label_schema_by_task=label_schema_by_task,
            )

    def test_validate_annotation_scene_empty_error(self, fxt_project, fxt_image_identifier_1, fxt_label_schema) -> None:
        """
        Test validate_annotation_scene on empty annotation_scene data.
        """
        with (
            patch.object(
                LabelSchemaService,
                "get_latest_label_schema_for_task",
                return_value=fxt_label_schema,
            ),
            pytest.raises(BadRequestException),
        ):
            AnnotationRestValidator().validate_annotation_scene(
                annotation_scene_rest={},
                project=fxt_project,
                media_identifier=fxt_image_identifier_1,
                media_width=DummyValues.MEDIA_WIDTH,
                media_height=DummyValues.MEDIA_HEIGHT,
                label_schema=fxt_label_schema,
            )

    @pytest.mark.parametrize(
        "lazyfxt_var_data,expected_error",
        [
            ("fxt_video_annotation_range_valid", None),
            ("fxt_video_annotation_range_invalid_range_1", BadRequestException),
            ("fxt_video_annotation_range_invalid_range_2", BadRequestException),
            ("fxt_video_annotation_range_invalid_range_3", BadRequestException),
            ("fxt_video_annotation_range_nonexisting_labels", LabelNotFoundException),
        ],
    )
    def test_validate_video_annotation_range(
        self, request, lazyfxt_var_data, expected_error, fxt_classification_label_schema
    ) -> None:
        context = pytest.raises(expected_error) if expected_error else nullcontext()
        with context:
            var_data = request.getfixturevalue(lazyfxt_var_data)
            AnnotationRestValidator().validate_video_annotation_range(
                video_annotation_range_rest=var_data,
                label_schema=fxt_classification_label_schema,
                video_total_frames=999,
            )

    @pytest.mark.parametrize(
        "label_names, label_groups_str, label_graph_str, annotation_scene_rest",
        [
            (
                [
                    "fish",
                    "bird",
                    "flightless",
                    "flying",
                    "mammal",
                    "placental",
                    "marsupial",
                    "monotreme",
                    "quadruped",
                    "biped",
                ],
                [
                    {"name": "class", "labels": ["fish", "bird", "mammal"]},
                    {"name": "legs", "labels": ["quadruped", "biped"]},
                    {
                        "name": "mammal_reproduction",
                        "labels": ["placental", "marsupial", "monotreme"],
                    },
                    {"name": "flight_capability", "labels": ["flightless", "flying"]},
                ],
                {
                    "placental": "mammal",
                    "marsupial": "mammal",
                    "monotreme": "mammal",
                    "quadruped": "mammal",
                    "biped": "mammal",
                    "flightless": "bird",
                    "flying": "bird",
                },
                {
                    "media_identifier": {
                        "type": "image",
                        "image_id": "67769ac3f51672e7347fc720",
                    },
                    "annotations": [
                        {
                            "id": "d797b928-ea59-4c82-8255-fcbe0e03bf18",
                            "shape": {
                                "type": "RECTANGLE",
                                "x": 0,
                                "y": 0,
                                "width": DummyValues.MEDIA_WIDTH,
                                "height": DummyValues.MEDIA_HEIGHT,
                            },
                            "labels": [
                                {"id": "bird", "probability": 1, "hotkey": ""},
                                {"id": "marsupial", "probability": 1, "hotkey": ""},
                            ],
                            "labels_to_revisit": [],
                        }
                    ],
                },
            )
        ],
    )
    def test_hierarchical_label_exclusivity(
        self,
        label_names,
        label_groups_str,
        label_graph_str,
        annotation_scene_rest,
        fxt_image_identifier_1,
        fxt_project_with_classification_task,
    ):
        labels = [Label(name=name, id_=ID(name), domain=Domain.CLASSIFICATION) for name in label_names]
        label_groups = [
            LabelGroup(
                name=group["name"],
                labels=[label for label in labels if label.name in group["labels"]],
            )
            for group in label_groups_str
        ]
        label_map = {label.name: label for label in labels}
        label_tree = LabelTree()
        for label in labels:
            label_tree.add_node(label)
        for v, w in label_graph_str.items():
            label_tree.add_edge(label_map[v], label_map[w])

        label_schema = LabelSchema(
            id_=ID("test_label_schema"),
            label_tree=label_tree,
            label_groups=label_groups,
        )

        label_schema_by_task = label_schema_by_task_for_single_task_project(
            fxt_project_with_classification_task, label_schema
        )
        with (
            patch.object(jsonschema, "validate"),
            pytest.raises(ConflictingExclusiveLabelsException),
        ):
            AnnotationRestValidator().validate_annotation_scene(
                annotation_scene_rest=annotation_scene_rest,
                project=fxt_project_with_classification_task,
                media_identifier=fxt_image_identifier_1,
                media_width=DummyValues.MEDIA_WIDTH,
                media_height=DummyValues.MEDIA_HEIGHT,
                label_schema_by_task=label_schema_by_task,
            )
