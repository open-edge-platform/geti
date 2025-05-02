# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from unittest.mock import patch

from testfixtures import compare

from communication.views.prediction_rest_views import PredictionRESTViews
from communication.views.scored_label_rest_views import ScoredLabelRESTViews

from iai_core_py.entities.annotation import AnnotationSceneKind


class TestPredictionRESTViews:
    def test_media_2d_prediction_to_rest(
        self,
        fxt_scored_label_rest,
        fxt_annotation_scene,
        fxt_project,
        fxt_label_schema,
    ) -> None:
        # Arrange
        fxt_annotation_scene.kind = AnnotationSceneKind.PREDICTION
        expected_result = {
            "annotations": [
                {
                    "id": "92497df6-f45a-11eb-9a03-0242ac130003",
                    "labels": [
                        {
                            "id": "60d31793d5f1fb7e6e3c1a50",
                            "probability": 0.97,
                            "source": {
                                "model_id": "60d31793d5f1fb7e6e3c1a50",
                                "model_storage_id": "60d31793d5f1fb7e6e3c1a51",
                                "user_id": "dummy_user",
                            },
                        },
                    ],
                    "modified": "2021-07-15T00:00:00",
                    "shape": {
                        "height": 60,
                        "type": "RECTANGLE",
                        "width": 160,
                        "x": 240,
                        "y": 120,
                    },
                },
                {
                    "id": "92497df6-f45a-11eb-9a03-0242ac130004",
                    "labels": [
                        {
                            "id": "60d31793d5f1fb7e6e3c1a50",
                            "probability": 0.97,
                            "source": {
                                "model_id": "60d31793d5f1fb7e6e3c1a50",
                                "model_storage_id": "60d31793d5f1fb7e6e3c1a51",
                                "user_id": "dummy_user",
                            },
                        },
                    ],
                    "modified": "2020-09-01T00:00:00",
                    "shape": {
                        "height": 60,
                        "type": "ELLIPSE",
                        "width": 160,
                        "x": 240,
                        "y": 120,
                    },
                },
                {
                    "id": "92497df6-f45a-11eb-9a03-0242ac130005",
                    "labels": [
                        {
                            "id": "60d31793d5f1fb7e6e3c1a50",
                            "probability": 0.97,
                            "source": {
                                "model_id": "60d31793d5f1fb7e6e3c1a50",
                                "model_storage_id": "60d31793d5f1fb7e6e3c1a51",
                                "user_id": "dummy_user",
                            },
                        },
                    ],
                    "modified": "2021-07-15T00:00:00",
                    "shape": {
                        "points": [{"x": 80, "y": 60}, {"x": 200, "y": 180}, {"x": 320, "y": 360}],
                        "type": "POLYGON",
                    },
                },
            ],
            "id": "60d31793d5f1fb7e6e3c1a4f",
            "kind": "prediction",
            "media_identifier": {"image_id": "60d31793d5f1fb7e6e3c1a4f", "type": "image"},
            "modified": "2021-07-15T00:00:00",
        }

        # Act
        with patch.object(
            ScoredLabelRESTViews,
            "scored_label_to_rest",
            return_value=fxt_scored_label_rest,
        ) as mock_label_rest:
            result = PredictionRESTViews.media_2d_prediction_to_rest(
                prediction=fxt_annotation_scene,
                project=fxt_project,
                label_schema=fxt_label_schema,
            )

        # Assert
        mock_label_rest.assert_called()
        compare(result, expected_result, ignore_eq=True)

    def test_media_2d_prediction_to_rest_inference_gateway(
        self,
        fxt_scored_label_rest,
        fxt_annotation_scene,
        fxt_project,
        fxt_label_schema,
    ) -> None:
        # Arrange
        fxt_annotation_scene.kind = AnnotationSceneKind.PREDICTION
        expected_result = {
            "created": "2021-07-15T00:00:00",
            "media_identifier": {"image_id": "60d31793d5f1fb7e6e3c1a4f", "type": "image"},
            "predictions": [
                {
                    "labels": [{"id": "60d31793d5f1fb7e6e3c1a50", "probability": 0.97}],
                    "shape": {"height": 60, "type": "RECTANGLE", "width": 160, "x": 240, "y": 120},
                },
                {
                    "labels": [{"id": "60d31793d5f1fb7e6e3c1a50", "probability": 0.97}],
                    "shape": {"height": 60, "type": "ELLIPSE", "width": 160, "x": 240, "y": 120},
                },
                {
                    "labels": [{"id": "60d31793d5f1fb7e6e3c1a50", "probability": 0.97}],
                    "shape": {
                        "points": [{"x": 80, "y": 60}, {"x": 200, "y": 180}, {"x": 320, "y": 360}],
                        "type": "POLYGON",
                    },
                },
            ],
        }

        # Act
        with patch.object(
            ScoredLabelRESTViews,
            "scored_label_to_rest",
            return_value=fxt_scored_label_rest,
        ) as mock_label_rest:
            result = PredictionRESTViews.media_2d_prediction_to_rest(
                prediction=fxt_annotation_scene,
                project=fxt_project,
                label_schema=fxt_label_schema,
                update_response_for_inference_gateway=True,
            )

        # Assert
        mock_label_rest.assert_called()
        compare(result, expected_result, ignore_eq=True)
