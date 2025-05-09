# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import copy

import pytest

from communication.views.annotation_rest_views import RestShapeType
from tests.fixtures.values import DummyValues

from geti_types import ID, MediaIdentifierEntity
from iai_core.entities import shapes
from iai_core.entities.annotation import Annotation, AnnotationScene
from iai_core.entities.annotation_scene_state import AnnotationSceneState, AnnotationState
from iai_core.entities.scored_label import ScoredLabel
from iai_core.entities.shapes import Keypoint, Rectangle
from iai_core.repos import AnnotationSceneStateRepo


@pytest.fixture
def fxt_label_only_annotation_rest(fxt_scored_label_rest):
    yield {
        "id": DummyValues.UUID,
        "modified": DummyValues.MODIFICATION_DATE_1.isoformat(),
        "labels": [fxt_scored_label_rest],
        "labels_to_revisit": [fxt_scored_label_rest["id"]],
    }


@pytest.fixture
def fxt_annotation_scene_1(
    fxt_mongo_id,
    fxt_media_identifier_1,
    fxt_rectangle_annotation,
    fxt_ellipse_annotation,
    fxt_polygon_annotation,
):
    yield AnnotationScene(
        kind=DummyValues.ANNOTATION_SCENE_KIND,
        media_identifier=fxt_media_identifier_1,
        media_height=DummyValues.MEDIA_HEIGHT,
        media_width=DummyValues.MEDIA_WIDTH,
        id_=fxt_mongo_id(),
        last_annotator_id=DummyValues.ANNOTATION_EDITOR_NAME,
        creation_date=DummyValues.MODIFICATION_DATE_1,
        annotations=[
            fxt_rectangle_annotation,
            fxt_ellipse_annotation,
            fxt_polygon_annotation,
        ],
    )


@pytest.fixture
def fxt_annotation_scene_keypoint(
    fxt_mongo_id,
    fxt_media_identifier_1,
    fxt_keypoint_annotation,
):
    yield AnnotationScene(
        kind=DummyValues.ANNOTATION_SCENE_KIND,
        media_identifier=fxt_media_identifier_1,
        media_height=DummyValues.MEDIA_HEIGHT,
        media_width=DummyValues.MEDIA_WIDTH,
        id_=fxt_mongo_id(),
        last_annotator_id=DummyValues.ANNOTATION_EDITOR_NAME,
        creation_date=DummyValues.MODIFICATION_DATE_1,
        annotations=[
            fxt_keypoint_annotation,
        ],
    )


@pytest.fixture
def fxt_annotation_scene_anomaly_reduced(
    fxt_mongo_id,
    fxt_media_identifier_1,
    fxt_rectangle_annotation,
    fxt_rectangle_full_box_annotation,
    fxt_ellipse_annotation,
    fxt_polygon_annotation,
):
    yield AnnotationScene(
        kind=DummyValues.ANNOTATION_SCENE_KIND,
        media_identifier=fxt_media_identifier_1,
        media_height=DummyValues.MEDIA_HEIGHT,
        media_width=DummyValues.MEDIA_WIDTH,
        id_=fxt_mongo_id(),
        last_annotator_id=DummyValues.ANNOTATION_EDITOR_NAME,
        creation_date=DummyValues.MODIFICATION_DATE_1,
        annotations=[
            fxt_rectangle_annotation,
            fxt_rectangle_full_box_annotation,
            fxt_ellipse_annotation,
            fxt_polygon_annotation,
        ],
    )


@pytest.fixture
def fxt_annotation_scene_empty(
    fxt_mongo_id,
    fxt_media_identifier_1,
    fxt_empty_annotation,
):
    yield AnnotationScene(
        kind=DummyValues.ANNOTATION_SCENE_KIND,
        media_identifier=fxt_media_identifier_1,
        media_height=DummyValues.MEDIA_HEIGHT,
        media_width=DummyValues.MEDIA_WIDTH,
        id_=fxt_mongo_id(),
        last_annotator_id=DummyValues.ANNOTATION_EDITOR_NAME,
        creation_date=DummyValues.MODIFICATION_DATE_1,
        annotations=[
            fxt_empty_annotation,
        ],
    )


@pytest.fixture
def fxt_annotation_scene_2(
    fxt_mongo_id,
    fxt_media_identifier_1,
    fxt_rectangle_annotation_2,
):
    yield AnnotationScene(
        kind=DummyValues.ANNOTATION_SCENE_KIND,
        media_identifier=fxt_media_identifier_1,
        media_height=DummyValues.MEDIA_HEIGHT,
        media_width=DummyValues.MEDIA_WIDTH,
        id_=fxt_mongo_id(),
        last_annotator_id=DummyValues.ANNOTATION_EDITOR_NAME,
        creation_date=DummyValues.MODIFICATION_DATE_1,
        annotations=[fxt_rectangle_annotation_2],
    )


@pytest.fixture
def fxt_annotation_scene_no_annotations(
    fxt_mongo_id,
    fxt_media_identifier_1,
):
    yield AnnotationScene(
        kind=DummyValues.ANNOTATION_SCENE_KIND,
        media_identifier=fxt_media_identifier_1,
        media_height=DummyValues.MEDIA_HEIGHT,
        media_width=DummyValues.MEDIA_WIDTH,
        id_=fxt_mongo_id(),
        last_annotator_id=DummyValues.ANNOTATION_EDITOR_NAME,
        creation_date=DummyValues.MODIFICATION_DATE_1,
        annotations=[],
    )


@pytest.fixture
def fxt_annotation_scene(fxt_annotation_scene_1):
    yield fxt_annotation_scene_1


@pytest.fixture
def fxt_annotation_scene_state(fxt_annotation_scene_state_1):
    yield fxt_annotation_scene_state_1


@pytest.fixture
def fxt_annotation_scene_state_1(fxt_annotation_scene, fxt_rectangle_annotation):
    yield AnnotationSceneState(
        media_identifier=fxt_annotation_scene.media_identifier,
        annotation_scene_id=fxt_annotation_scene.id_,
        annotation_state_per_task={},
        unannotated_rois={},
        labels_to_revisit_full_scene=fxt_rectangle_annotation.get_label_ids(),
        labels_to_revisit_per_annotation={
            fxt_rectangle_annotation.id_: fxt_rectangle_annotation.get_label_ids(),
        },
        id_=AnnotationSceneStateRepo.generate_id(),
    )


@pytest.fixture
def fxt_annotation_scene_state_2(fxt_annotation_scene_2, fxt_rectangle_annotation_2):
    yield AnnotationSceneState(
        media_identifier=fxt_annotation_scene_2.media_identifier,
        annotation_scene_id=fxt_annotation_scene_2.id_,
        annotation_state_per_task={},
        unannotated_rois={},
        labels_to_revisit_full_scene=[],
        labels_to_revisit_per_annotation={},
        id_=AnnotationSceneStateRepo.generate_id(),
    )


@pytest.fixture
def fxt_annotation_scene_rest_response_1(
    fxt_mongo_id,
    fxt_media_identifier_rest,
    fxt_rectangle_annotation_rest,
    fxt_ellipse_annotation_rest,
    fxt_polygon_annotation_rest,
):
    yield {
        "id": str(fxt_mongo_id()),
        "kind": str(DummyValues.ANNOTATION_SCENE_KIND).lower(),
        "modified": DummyValues.MODIFICATION_DATE_1.isoformat(),
        "media_identifier": fxt_media_identifier_rest,
        "annotations": [
            fxt_rectangle_annotation_rest,
            fxt_ellipse_annotation_rest,
            fxt_polygon_annotation_rest,
        ],
        "labels_to_revisit_full_scene": [fxt_rectangle_annotation_rest["labels"][0]["id"]],
        "annotation_state_per_task": [],
    }


@pytest.fixture
def fxt_annotation_scene_rest_response_2(
    fxt_mongo_id,
    fxt_media_identifier_rest,
    fxt_rectangle_annotation_rest_2,
):
    yield {
        "id": str(fxt_mongo_id()),
        "kind": str(DummyValues.ANNOTATION_SCENE_KIND).lower(),
        "modified": DummyValues.MODIFICATION_DATE_1.isoformat(),
        "media_identifier": fxt_media_identifier_rest,
        "annotations": [
            fxt_rectangle_annotation_rest_2,
        ],
        "labels_to_revisit_full_scene": [],
        "annotation_state_per_task": [],
    }


@pytest.fixture
def fxt_annotation_scene_keypoint_rest_response(
    fxt_mongo_id,
    fxt_media_identifier_rest,
    fxt_keypoint_annotation_rest,
):
    yield {
        "id": str(fxt_mongo_id()),
        "kind": str(DummyValues.ANNOTATION_SCENE_KIND).lower(),
        "modified": DummyValues.MODIFICATION_DATE_1.isoformat(),
        "media_identifier": fxt_media_identifier_rest,
        "annotations": [
            fxt_keypoint_annotation_rest,
        ],
        "labels_to_revisit_full_scene": [fxt_keypoint_annotation_rest["labels"][0]["id"]],
        "annotation_state_per_task": [],
    }


@pytest.fixture
def fxt_annotation_scene_anomaly_reduced_rest_response(
    fxt_mongo_id,
    fxt_media_identifier_rest,
    fxt_rectangle_annotation_rest,
    fxt_rectangle_annotation_rest_anomaly_reduced,
    fxt_ellipse_annotation_rest,
    fxt_polygon_annotation_rest,
):
    yield {
        "id": str(fxt_mongo_id()),
        "kind": str(DummyValues.ANNOTATION_SCENE_KIND).lower(),
        "modified": DummyValues.MODIFICATION_DATE_1.isoformat(),
        "media_identifier": fxt_media_identifier_rest,
        "annotations": [
            fxt_rectangle_annotation_rest,
            fxt_rectangle_annotation_rest_anomaly_reduced,
            fxt_ellipse_annotation_rest,
            fxt_polygon_annotation_rest,
        ],
        "labels_to_revisit_full_scene": [fxt_rectangle_annotation_rest_anomaly_reduced["labels"][0]["id"]],
        "annotation_state_per_task": [],
    }


@pytest.fixture
def fxt_annotation_scene_rest_response(fxt_annotation_scene_rest_response_1):
    yield fxt_annotation_scene_rest_response_1


@pytest.fixture
def fxt_annotation_scene_rest_request(
    fxt_media_identifier_rest,
    fxt_rectangle_segmentation_annotation_rest,
    fxt_ellipse_segmentation_annotation_rest,
    fxt_polygon_segmentation_annotation_rest,
    fxt_rotated_rect_annotation_rest,
):
    yield {
        "modified": DummyValues.MODIFICATION_DATE_1.isoformat(),
        "media_identifier": fxt_media_identifier_rest,
        "annotations": [
            fxt_rectangle_segmentation_annotation_rest,
            fxt_ellipse_segmentation_annotation_rest,
            fxt_polygon_segmentation_annotation_rest,
            fxt_rotated_rect_annotation_rest,
        ],
        "labels_to_revisit_full_scene": [fxt_rectangle_segmentation_annotation_rest["labels"][0]["id"]],
    }


@pytest.fixture
def fxt_annotation_scene_rest_request_empty_label(
    fxt_media_identifier_rest, fxt_empty_segmentation_label, fxt_full_box_shape_rest
):
    yield {
        "modified": DummyValues.MODIFICATION_DATE_1.isoformat(),
        "media_identifier": fxt_media_identifier_rest,
        "annotations": [
            {
                "id": DummyValues.UUID,
                "modified": DummyValues.MODIFICATION_DATE_1.isoformat(),
                "shape": fxt_full_box_shape_rest,
                "labels": [
                    {
                        "id": str(fxt_empty_segmentation_label.id_),
                        "name": DummyValues.LABEL_NAME,
                        "probability": DummyValues.LABEL_PROBABILITY,
                        "color": "#ff0000ff",
                        "source": {
                            "type": "N/A",
                            "id": "N/A",
                        },
                    }
                ],
                "labels_to_revisit": [],
            }
        ],
        "labels_to_revisit_full_scene": [],
    }


@pytest.fixture
def fxt_annotation_scene_label_only(fxt_annotation_scene_2):
    yield fxt_annotation_scene_2


@pytest.fixture
def fxt_annotation_scene_rest_label_only(
    fxt_mongo_id,
    fxt_media_identifier_rest,
    fxt_label_only_annotation_rest,
):
    yield {
        "id": fxt_mongo_id(),
        "kind": str(DummyValues.ANNOTATION_SCENE_KIND).lower(),
        "modified": DummyValues.MODIFICATION_DATE_1.isoformat(),
        "media_identifier": fxt_media_identifier_rest,
        "annotations": [fxt_label_only_annotation_rest],
        "labels_to_revisit_full_scene": [fxt_label_only_annotation_rest["labels"][0]["id"]],
        "annotation_state_per_task": [],
    }


@pytest.fixture
def fxt_annotation_scene_rest_no_id_and_date(
    fxt_rectangle_annotation_rest_no_id_and_date,
):
    yield {
        "annotations": [
            fxt_rectangle_annotation_rest_no_id_and_date,
        ],
    }


@pytest.fixture
def fxt_ann_scenes_list(fxt_annotation_scene_1, fxt_annotation_scene_2):
    yield [fxt_annotation_scene_1, fxt_annotation_scene_2]


@pytest.fixture
def fxt_ann_scene_states_list(fxt_annotation_scene_state_1, fxt_annotation_scene_state_2):
    yield [fxt_annotation_scene_state_1, fxt_annotation_scene_state_2]


@pytest.fixture
def fxt_ann_scene_states_list_label_only(fxt_annotation_scene_label_only):
    annotation = fxt_annotation_scene_label_only.annotations[0]
    annotation_scene_state = AnnotationSceneState(
        media_identifier=fxt_annotation_scene_label_only.media_identifier,
        annotation_scene_id=fxt_annotation_scene_label_only.id_,
        annotation_state_per_task={},
        unannotated_rois={},
        labels_to_revisit_full_scene=fxt_annotation_scene_label_only.get_label_ids(),
        labels_to_revisit_per_annotation={annotation.id_: annotation.get_label_ids()},
        id_=AnnotationSceneStateRepo.generate_id(),
    )
    yield [annotation_scene_state]


@pytest.fixture
def fxt_ann_scenes_list_rest(fxt_annotation_scene_rest_response_1, fxt_annotation_scene_rest_response_2):
    yield {
        "video_annotations": [
            fxt_annotation_scene_rest_response_1,
            fxt_annotation_scene_rest_response_2,
        ]
    }


@pytest.fixture
def fxt_ann_scenes_list_label_only(fxt_annotation_scene_label_only):
    yield [fxt_annotation_scene_label_only]


@pytest.fixture
def fxt_ann_scenes_list_rest_label_only(fxt_annotation_scene_rest_label_only):
    yield {"video_annotations": [fxt_annotation_scene_rest_label_only]}


@pytest.fixture
def fxt_rectangle_shape_1():
    yield Rectangle(
        x1=DummyValues.X,
        x2=DummyValues.X + DummyValues.WIDTH,
        y1=DummyValues.Y,
        y2=DummyValues.Y + DummyValues.HEIGHT,
        modification_date=DummyValues.MODIFICATION_DATE_1,
    )


@pytest.fixture
def fxt_rectangle_shape_2():
    x, y = DummyValues.X / 2.0, DummyValues.Y / 2.0
    w, h = DummyValues.WIDTH / 2.0, DummyValues.HEIGHT / 2.0
    yield Rectangle(
        x1=x,
        x2=x + w,
        y1=y,
        y2=y + h,
        modification_date=DummyValues.MODIFICATION_DATE_1,
    )


@pytest.fixture
def fxt_rectangle_shape_full_box():
    yield Rectangle(
        x1=0,
        x2=1,
        y1=0,
        y2=1,
        modification_date=DummyValues.MODIFICATION_DATE_1,
    )


@pytest.fixture
def fxt_rectangle_shape(fxt_rectangle_shape_1):
    yield fxt_rectangle_shape_1


@pytest.fixture
def fxt_rectangle_shape_rest_1():
    yield {
        "type": RestShapeType.RECTANGLE.name,
        "x": DummyValues.X * DummyValues.MEDIA_WIDTH,
        "y": DummyValues.Y * DummyValues.MEDIA_HEIGHT,
        "width": DummyValues.WIDTH * DummyValues.MEDIA_WIDTH,  # float calculations are not exact
        "height": DummyValues.HEIGHT * DummyValues.MEDIA_HEIGHT,  # float calculations are not exact
    }


@pytest.fixture
def fxt_full_box_shape_rest():
    yield {
        "type": RestShapeType.RECTANGLE.name,
        "x": 0,
        "y": 0,
        "width": DummyValues.MEDIA_WIDTH,
        "height": DummyValues.MEDIA_HEIGHT,
    }


@pytest.fixture
def fxt_rectangle_shape_rest_2():
    x, y = DummyValues.X / 2.0, DummyValues.Y / 2.0
    w, h = DummyValues.WIDTH / 2.0, DummyValues.HEIGHT / 2.0
    yield {
        "type": RestShapeType.RECTANGLE.name,
        "x": x * DummyValues.MEDIA_WIDTH,
        "y": y * DummyValues.MEDIA_HEIGHT,
        "width": w * DummyValues.MEDIA_WIDTH,
        "height": h * DummyValues.MEDIA_HEIGHT,
    }


@pytest.fixture
def fxt_rectangle_shape_rest(fxt_rectangle_shape_rest_1):
    yield fxt_rectangle_shape_rest_1


@pytest.fixture
def fxt_empty_annotation(fxt_empty_detection_label):
    scored_label = ScoredLabel(
        label_id=fxt_empty_detection_label.id_,
        is_empty=True,
        probability=DummyValues.LABEL_PROBABILITY,
    )
    yield Annotation(shape=Rectangle.generate_full_box(), labels=[scored_label], id_=DummyValues.UUID)


@pytest.fixture
def fxt_rectangle_annotation(fxt_rectangle_shape_1, fxt_scored_label):
    yield Annotation(shape=fxt_rectangle_shape_1, labels=[fxt_scored_label], id_=DummyValues.UUID)


@pytest.fixture
def fxt_rectangle_annotation_2(fxt_rectangle_shape_2, fxt_scored_label):
    yield Annotation(shape=fxt_rectangle_shape_2, labels=[fxt_scored_label], id_=DummyValues.UUID)


@pytest.fixture
def fxt_rectangle_full_box_annotation(fxt_rectangle_shape_full_box, fxt_scored_label):
    yield Annotation(
        shape=fxt_rectangle_shape_full_box,
        labels=[fxt_scored_label],
        id_=DummyValues.UUID,
    )


@pytest.fixture
def fxt_rectangle_annotation_rest_1(fxt_rectangle_shape_rest_1, fxt_scored_label_rest):
    yield {
        "id": DummyValues.UUID,
        "modified": DummyValues.MODIFICATION_DATE_1.isoformat(),
        "shape": fxt_rectangle_shape_rest_1,
        "labels": [fxt_scored_label_rest],
        "labels_to_revisit": [fxt_scored_label_rest["id"]],
    }


@pytest.fixture
def fxt_rectangle_annotation_rest_2(fxt_rectangle_shape_rest_2, fxt_scored_label_rest):
    yield {
        "id": DummyValues.UUID,
        "modified": DummyValues.MODIFICATION_DATE_1.isoformat(),
        "shape": fxt_rectangle_shape_rest_2,
        "labels": [fxt_scored_label_rest],
        "labels_to_revisit": [],
    }


@pytest.fixture
def fxt_rectangle_annotation_rest_anomaly_reduced(fxt_full_box_shape_rest, fxt_scored_label_rest):
    yield {
        "id": DummyValues.UUID,
        "modified": DummyValues.MODIFICATION_DATE_1.isoformat(),
        "shape": fxt_full_box_shape_rest,
        "labels": [fxt_scored_label_rest],
        "labels_to_revisit": [fxt_scored_label_rest["id"]],
    }


@pytest.fixture
def fxt_rectangle_annotation_rest(fxt_rectangle_annotation_rest_1):
    yield fxt_rectangle_annotation_rest_1


@pytest.fixture
def fxt_rectangle_segmentation_annotation_rest(fxt_rectangle_shape_rest_1, fxt_segmentation_scored_label_rest_factory):
    scored_label_rest_0 = fxt_segmentation_scored_label_rest_factory(num_labels=2, idx=0)
    yield {
        "id": DummyValues.UUID,
        "modified": DummyValues.MODIFICATION_DATE_1.isoformat(),
        "shape": fxt_rectangle_shape_rest_1,
        "labels": [scored_label_rest_0],
        "labels_to_revisit": [scored_label_rest_0["id"]],
    }


@pytest.fixture
def fxt_rectangle_annotation_rest_no_id_and_date(fxt_rectangle_shape_rest, fxt_scored_label_rest):
    yield {
        "shape": fxt_rectangle_shape_rest,
        "labels": [fxt_scored_label_rest, copy.deepcopy(fxt_scored_label_rest)],
    }


@pytest.fixture
def fxt_ellipse_shape():
    yield shapes.ellipse.Ellipse(
        x1=DummyValues.X,
        x2=DummyValues.X + DummyValues.WIDTH,
        y1=DummyValues.Y,
        y2=DummyValues.Y + DummyValues.HEIGHT,
        modification_date=DummyValues.MODIFICATION_DATE_2,
    )


@pytest.fixture
def fxt_ellipse_shape_rest():
    yield {
        "type": RestShapeType.ELLIPSE.name,
        "x": DummyValues.X * DummyValues.MEDIA_WIDTH,
        "y": DummyValues.Y * DummyValues.MEDIA_HEIGHT,
        "width": DummyValues.WIDTH * DummyValues.MEDIA_WIDTH,
        "height": DummyValues.HEIGHT * DummyValues.MEDIA_HEIGHT,
    }


@pytest.fixture
def fxt_ellipse_annotation(fxt_ellipse_shape, fxt_scored_label):
    yield Annotation(shape=fxt_ellipse_shape, labels=[fxt_scored_label], id_=DummyValues.UUID_2)


@pytest.fixture
def fxt_ellipse_annotation_rest(fxt_ellipse_shape_rest, fxt_scored_label_rest):
    yield {
        "id": DummyValues.UUID_2,
        "modified": DummyValues.MODIFICATION_DATE_2.isoformat(),
        "shape": fxt_ellipse_shape_rest,
        "labels": [fxt_scored_label_rest],
        "labels_to_revisit": [],
    }


@pytest.fixture
def fxt_ellipse_segmentation_annotation_rest(fxt_ellipse_shape_rest, fxt_segmentation_scored_label_rest_factory):
    scored_label_rest_0 = fxt_segmentation_scored_label_rest_factory(num_labels=2, idx=0)
    yield {
        "id": DummyValues.UUID_2,
        "modified": DummyValues.MODIFICATION_DATE_2.isoformat(),
        "shape": fxt_ellipse_shape_rest,
        "labels": [scored_label_rest_0],
        "labels_to_revisit": [],
    }


@pytest.fixture
def fxt_point_1():
    yield shapes.polygon.Point(x=0.125, y=0.125)


@pytest.fixture
def fxt_point_1_rest():
    yield {"x": 0.125 * DummyValues.MEDIA_WIDTH, "y": 0.125 * DummyValues.MEDIA_HEIGHT}


@pytest.fixture
def fxt_point_2():
    yield shapes.polygon.Point(x=0.3125, y=0.375)


@pytest.fixture
def fxt_point_2_rest():
    yield {"x": 0.3125 * DummyValues.MEDIA_WIDTH, "y": 0.375 * DummyValues.MEDIA_HEIGHT}


@pytest.fixture
def fxt_point_3():
    yield shapes.polygon.Point(x=0.5, y=0.75)


@pytest.fixture
def fxt_point_3_rest():
    yield {"x": 0.5 * DummyValues.MEDIA_WIDTH, "y": 0.75 * DummyValues.MEDIA_HEIGHT}


@pytest.fixture
def fxt_polygon_shape(fxt_point_1, fxt_point_2, fxt_point_3):
    yield shapes.polygon.Polygon(
        points=[fxt_point_1, fxt_point_2, fxt_point_3],
        modification_date=DummyValues.MODIFICATION_DATE_1,
    )


@pytest.fixture
def fxt_polygon_shape_rest(fxt_point_1_rest, fxt_point_2_rest, fxt_point_3_rest):
    yield {
        "type": RestShapeType.POLYGON.name,
        "points": [fxt_point_1_rest, fxt_point_2_rest, fxt_point_3_rest],
    }


@pytest.fixture
def fxt_rotated_rect_rest():
    yield {
        "x": 0.5 * DummyValues.MEDIA_WIDTH,
        "y": 0.5 * DummyValues.MEDIA_HEIGHT,
        "width": 0.3 * DummyValues.MEDIA_WIDTH,
        "height": 0.4 * DummyValues.MEDIA_HEIGHT,
        "angle": 77,
        "type": RestShapeType.ROTATED_RECTANGLE.name,
    }


@pytest.fixture
def fxt_polygon_annotation(fxt_polygon_shape, fxt_scored_label):
    yield Annotation(shape=fxt_polygon_shape, labels=[fxt_scored_label], id_=DummyValues.UUID_3)


@pytest.fixture
def fxt_polygon_annotation_rest(fxt_polygon_shape_rest, fxt_scored_label_rest):
    yield {
        "id": DummyValues.UUID_3,
        "modified": DummyValues.MODIFICATION_DATE_1.isoformat(),
        "shape": fxt_polygon_shape_rest,
        "labels": [fxt_scored_label_rest],
        "labels_to_revisit": [],
    }


@pytest.fixture
def fxt_polygon_segmentation_annotation_rest(fxt_polygon_shape_rest, fxt_segmentation_scored_label_rest_factory):
    scored_label_rest_0 = fxt_segmentation_scored_label_rest_factory(num_labels=2, idx=0)
    yield {
        "id": DummyValues.UUID_3,
        "modified": DummyValues.MODIFICATION_DATE_1.isoformat(),
        "shape": fxt_polygon_shape_rest,
        "labels": [scored_label_rest_0],
        "labels_to_revisit": [],
    }


@pytest.fixture
def fxt_rotated_rect_annotation_rest(fxt_rotated_rect_rest, fxt_segmentation_scored_label_rest_factory):
    scored_label_rest_0 = fxt_segmentation_scored_label_rest_factory(num_labels=3, idx=0)
    yield {
        "id": DummyValues.UUID_4,
        "modified": DummyValues.MODIFICATION_DATE_1.isoformat(),
        "shape": fxt_rotated_rect_rest,
        "labels": [scored_label_rest_0],
        "labels_to_revisit": [],
    }


@pytest.fixture
def fxt_keypoint_shape():
    yield Keypoint(
        x=0.5,
        y=0.1,
        is_visible=True,
        modification_date=DummyValues.MODIFICATION_DATE_1,
    )


@pytest.fixture
def fxt_keypoint_shape_rest():
    yield {
        "type": RestShapeType.KEYPOINT.name,
        "x": 0.5 * DummyValues.MEDIA_WIDTH,
        "y": 0.1 * DummyValues.MEDIA_HEIGHT,
        "is_visible": True,
    }


@pytest.fixture
def fxt_keypoint_annotation(fxt_keypoint_shape, fxt_scored_label):
    yield Annotation(shape=fxt_keypoint_shape, labels=[fxt_scored_label], id_=DummyValues.UUID)


@pytest.fixture
def fxt_keypoint_annotation_rest(fxt_keypoint_shape_rest, fxt_scored_label_rest):
    yield {
        "id": DummyValues.UUID,
        "modified": DummyValues.MODIFICATION_DATE_1.isoformat(),
        "shape": fxt_keypoint_shape_rest,
        "labels": [fxt_scored_label_rest],
        "labels_to_revisit": [fxt_scored_label_rest["id"]],
    }


@pytest.fixture
def fxt_states_by_annotation_scene(
    fxt_mongo_id, fxt_detection_task, fxt_image_identifier_1, fxt_video_frame_identifier
):
    states: list[AnnotationSceneState] = []
    for i in range(DummyValues.N_ANNOTATED_IMAGES):
        states.append(
            AnnotationSceneState(
                annotation_scene_id=fxt_mongo_id(i),
                media_identifier=fxt_image_identifier_1,
                annotation_state_per_task={fxt_detection_task.id_: AnnotationState.ANNOTATED},
                unannotated_rois={fxt_detection_task.id_: []},
                id_=AnnotationSceneStateRepo.generate_id(),
            )
        )
    for i in range(DummyValues.N_ANNOTATED_FRAMES):
        states.append(
            AnnotationSceneState(
                annotation_scene_id=fxt_mongo_id(i + DummyValues.N_ANNOTATED_IMAGES),
                media_identifier=fxt_video_frame_identifier,
                annotation_state_per_task={fxt_detection_task.id_: AnnotationState.ANNOTATED},
                unannotated_rois={fxt_detection_task.id_: []},
                id_=AnnotationSceneStateRepo.generate_id(),
            )
        )
    yield states


@pytest.fixture
def fxt_annotation_scene_state_factory():
    def _factory(media_identifier: MediaIdentifierEntity):
        return AnnotationSceneState(
            media_identifier=media_identifier,
            annotation_scene_id=ID(),
            annotation_state_per_task={ID(): AnnotationState.NONE},
            unannotated_rois={ID(): [ID()]},
            id_=ID(),
        )

    yield _factory
