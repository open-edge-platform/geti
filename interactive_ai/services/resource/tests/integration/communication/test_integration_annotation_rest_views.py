# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from testfixtures import compare
from tests.utils.test_helpers import create_empty_segmentation_project

from communication.rest_views.annotation_rest_views import AnnotationRESTViews

from geti_types import ID, ImageIdentifier
from iai_core_py.entities.annotation import AnnotationSceneKind
from iai_core_py.entities.annotation_scene_state import AnnotationSceneState
from iai_core_py.repos import LabelSchemaRepo


class TestAnnotationRESTViews:
    def test_ellipse_rest_view(self, request, fxt_label):
        """
        <b>Description:</b>
        Verify that the shapes remain consistent when converting from json > annotation object > json

        <b>Input data:</b>
        A random annotated project

        <b>Expected results:</b>
        Test passes if shape remains consistent with original json after conversion

        <b>Steps</b>
        1. Create a project.
        2. Create an annotation object using pre-made json from test_helpers.py
        3. Generate output by putting reverting the generated annotation object back to json / dict
        4. Check if shapes have remained consistent.
        """
        project = create_empty_segmentation_project(test_case=request)

        project_label_schema = LabelSchemaRepo(project.identifier).get_latest()
        input_json = get_ellipse_annotation_json(
            id=project_label_schema.get_labels(include_empty=False)[0].id_,
            name="object",
            color="'#ffff00ff'",
        )

        label_ids = AnnotationRESTViews.get_label_ids_from_rest(input_json)
        label_per_id = dict.fromkeys(label_ids, fxt_label)

        (
            annotation,
            annotation_state,
        ) = AnnotationRESTViews.media_2d_annotation_from_rest(
            annotation_dict=input_json,
            label_per_id=label_per_id,
            kind=AnnotationSceneKind.ANNOTATION,
            last_annotator_id="test",
            media_identifier=ImageIdentifier(ID()),
            media_height=480,
            media_width=640,
        )

        output_json = AnnotationRESTViews.media_2d_annotation_to_rest(
            annotation_scene=annotation,
            annotation_scene_state=AnnotationSceneState(
                annotation_scene_id=annotation.id_,
                annotation_state_per_task={},
                media_identifier=annotation.media_identifier,
                unannotated_rois={},
                id_=ID(),
            ),
            tasks_to_revisit=[],
        )

        for i in range(3):
            compare(
                input_json["annotations"][i]["shape"],
                output_json["annotations"][i]["shape"],
                ignore_eq=True,
            )


def get_ellipse_annotation_json(color, id, name):
    return {
        "annotations": [
            {
                "id": "e42cf382-5f7b-4fda-980a-fa0fab00243c",
                "labels": [
                    {
                        "color": color,
                        "id": id,
                        "name": name,
                        "probability": 1,
                        "source": {"id": "N/A", "type": "N/A"},
                    }
                ],
                "modified": "2021-07-14T13:29:45.650000+00:00",
                "shape": {
                    "height": 96,
                    "type": "ELLIPSE",
                    "width": 128,
                    "x": 128,
                    "y": 96,
                },
            },
            {
                "id": "67f38b1e-f464-11eb-9a03-0242ac130003",
                "labels": [
                    {
                        "color": color,
                        "id": id,
                        "name": name,
                        "probability": 1,
                        "source": {"id": "N/A", "type": "N/A"},
                    }
                ],
                "modified": "2021-07-14T13:29:45.653000+00:00",
                "shape": {
                    "height": 120,
                    "type": "ELLIPSE",
                    "width": 160,
                    "x": 160,
                    "y": 120,
                },
            },
            {
                "id": "67f388da-f464-11eb-9a03-0242ac130003",
                "labels": [
                    {
                        "color": color,
                        "id": id,
                        "name": name,
                        "probability": 1,
                        "source": {"id": "N/A", "type": "N/A"},
                    }
                ],
                "modified": "2021-07-14T13:29:45.655000+00:00",
                "shape": {
                    "height": 144,
                    "type": "ELLIPSE",
                    "width": 240,
                    "x": 240,
                    "y": 144,
                },
            },
        ],
        "media_identifier": {"image_id": "60eee56304c0ea5cd01bcb0b", "type": "image"},
        "modified": "2021-07-14T13:29:45.655000+00:00",
    }
