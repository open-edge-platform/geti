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
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from geti_types import ID
from model_api.models import Contour
from model_api.models.utils import (
    AnomalyResult,
    ClassificationResult,
    DetectedKeypoints,
    Detection,
    DetectionResult,
    ImageResultWithSoftPrediction,
    InstanceSegmentationResult,
    PredictedMask,
    SegmentedObject,
    ZSLVisualPromptingResult,
)
from sc_sdk.entities.label import Domain, Label
from sc_sdk.entities.label_schema import LabelGroup, LabelSchema
from sc_sdk.entities.shapes import Ellipse, Point, Polygon, Rectangle

from jobs_common_extras.evaluation.services.prediction_to_annotation_converter import (
    AnomalyToAnnotationConverter,
    ClassificationToAnnotationConverter,
    DetectionToAnnotationConverter,
    KeypointToAnnotationConverter,
    RotatedRectToAnnotationConverter,
    SemanticSegmentationToAnnotationConverter,
    VisualPromptingToAnnotationConverter,
)


@pytest.mark.JobsComponent
class TestPredictionToAnnotationConverter:
    def test_classification_to_annotation_converter(self, fxt_label_schema_factory):
        # Arrange
        label_schema = fxt_label_schema_factory(Domain.CLASSIFICATION)
        labels = label_schema.get_labels(include_empty=False)
        labels_str = [label.name for label in labels]
        raw_prediction = ClassificationResult(
            top_labels=[(1, labels[1].name, 0.81)], raw_scores=[0.19, 0.81], saliency_map=None, feature_vector=None
        )

        # Act
        converter = ClassificationToAnnotationConverter(label_schema=label_schema, model_api_labels=labels_str)
        annotations = converter.convert_to_annotations(raw_prediction)

        # Assert
        assert converter.labels == label_schema.get_labels(include_empty=True)
        assert len(annotations) == 1
        predicted_label = annotations[0].get_labels()[0]
        assert predicted_label.id_ == labels[1].id_
        assert predicted_label.probability == 0.81

    @pytest.mark.parametrize("use_ellipse_shapes", [True, False])
    def test_detection_to_annotation_converter(self, use_ellipse_shapes, fxt_label_schema_factory):
        # Arrange
        label_schema = fxt_label_schema_factory(Domain.DETECTION)
        labels = label_schema.get_labels(include_empty=False)
        labels_str = [label.name for label in labels]
        coords = [12.0, 41.0, 12.5, 45.5]
        raw_prediction = DetectionResult(
            objects=[Detection(*coords, score=0.51, id=0)],
            saliency_map=None,
            feature_vector=None,
        )

        # Act
        converter = DetectionToAnnotationConverter(
            label_schema=label_schema,
            configuration={"use_ellipse_shapes": use_ellipse_shapes},
            model_api_labels=labels_str,
        )
        annotations = converter.convert_to_annotations(raw_prediction)

        # Assert
        for label in labels:
            assert label in converter.labels
        assert len(annotations) == 1
        shape = annotations[0].shape
        assert isinstance(shape, Ellipse) if use_ellipse_shapes else isinstance(shape, Rectangle)
        assert [shape.x1, shape.y1, shape.x2, shape.y2] == coords
        assert annotations[0].get_labels()[0].id_ == labels[0].id_

    @pytest.mark.parametrize("use_ellipse_shapes", [True, False])
    def test_rotated_rect_to_annotation_converter(self, use_ellipse_shapes, fxt_label_schema_factory):
        # Arrange
        label_schema = fxt_label_schema_factory(Domain.ROTATED_DETECTION)
        labels = label_schema.get_labels(include_empty=False)
        labels_str = [lbl.name for lbl in labels]
        coords = [1, 1, 4, 4]
        mask = np.array(
            [
                [0, 0, 0, 0, 0],
                [0, 1, 1, 1, 0],
                [0, 0, 1, 1, 0],
                [0, 0, 1, 1, 0],
                [0, 0, 0, 0, 0],
            ]
        )
        raw_prediction = InstanceSegmentationResult(
            segmentedObjects=[SegmentedObject(*coords, mask=mask, score=0.51, id=1, str_label="")],
            saliency_map=None,
            feature_vector=None,
        )
        height, width = mask.shape
        metadata = {"original_shape": (height, width, 3)}
        expected_ellipse_points = [1 / width, 1 / height, 4 / width, 4 / height]
        expected_polygon_points = [
            Point(x=1 / width, y=1 / height),
            Point(x=3 / width, y=1 / height),
            Point(x=3 / width, y=3 / height),
            Point(x=1 / width, y=3 / height),
        ]

        # Act
        converter = RotatedRectToAnnotationConverter(
            label_schema, configuration={"use_ellipse_shapes": use_ellipse_shapes}, model_api_labels=labels_str
        )
        annotations = converter.convert_to_annotations(raw_prediction, metadata=metadata)

        # Assert
        for label in labels:
            assert label in converter.labels
        assert len(annotations) == 1
        shape = annotations[0].shape
        if use_ellipse_shapes:
            assert isinstance(shape, Ellipse)
            for p1, p2 in zip([shape.x1, shape.y1, shape.x2, shape.y2], expected_ellipse_points):
                assert p1 == pytest.approx(p2, 0.01)
            assert next(label for label in labels if label.id_ == annotations[0].get_labels()[0].id_).name == "ellipse"
        else:
            assert isinstance(shape, Polygon)
            for p1, p2 in zip(shape.points, expected_polygon_points):
                assert p1.x == pytest.approx(p2.x, 0.01)
                assert p1.y == pytest.approx(p2.y, 0.01)
            assert next(label for label in labels if label.id_ == annotations[0].get_labels()[0].id_).name == "ellipse"

    def test_semantic_segmentation_to_annotation_converter(self, fxt_segmentation_labels):
        # Arrange
        seg_labels = [fxt_segmentation_labels[0]]
        label_schema = LabelSchema(id_=ID("dummy_segmentation_label_schema"))
        label_group = LabelGroup(labels=seg_labels, name="dummy segmentation label group")
        label_schema.add_group(label_group)
        labels = label_schema.get_labels(include_empty=False)
        labels_str = [label.name for label in labels]
        result_image = np.array(
            [
                [0, 0, 0],
                [0, 1, 0],
                [1, 1, 1],
            ]
        )
        soft_predictions = np.array(
            [
                [[0.9, 0.1, 0.1], [0.7, 0.1, 0.2], [0.9, 0.1, 0.1]],
                [[0.9, 0.0, 0.1], [0.9, 0.0, 0.1], [0.9, 0.0, 0.0]],
                [[0.2, 0.2, 0.6], [0.1, 0.2, 0.7], [0.2, 0.2, 0.6]],
            ]
        )
        raw_prediction = ImageResultWithSoftPrediction(
            resultImage=result_image,
            soft_prediction=soft_predictions,
            saliency_map=np.zeros_like(result_image),
            feature_vector=np.zeros((result_image.shape[0], result_image.shape[1], 2)),
        )
        expected_shape = Polygon(points=[Point(0.5, 0.5), Point(0.0, 1.0), Point(0.5, 1.0), Point(1.0, 1.0)])
        seg_model = MagicMock()
        seg_model.labels = labels_str

        def get_contours(_: ImageResultWithSoftPrediction):
            return [Contour(labels_str[0], 0.8, shape=np.array([[(1, 1), (0, 3), (1, 3), (3, 3)]]))]

        seg_model.get_contours = get_contours

        # Act
        converter = SemanticSegmentationToAnnotationConverter(label_schema, model=seg_model)
        annotations = converter.convert_to_annotations(raw_prediction)

        # Assert
        assert converter.labels == labels
        assert len(annotations) == 1
        assert annotations[0].get_labels()[0].label_id == labels[0].id_
        assert isinstance(annotations[0].shape, Polygon)
        for p1, p2 in zip(annotations[0].shape.points, expected_shape.points):
            assert p1.x == pytest.approx(p2.x, 0.01)
            assert p1.y == pytest.approx(p2.y, 0.01)

    @pytest.mark.parametrize(
        "domain", [Domain.ANOMALY_CLASSIFICATION, Domain.ANOMALY_SEGMENTATION, Domain.ANOMALY_DETECTION]
    )
    def test_anomaly_to_annotation_converter(self, domain, fxt_label_schema_factory):
        # Arrange
        label_schema = fxt_label_schema_factory(domain)
        labels = label_schema.get_labels(include_empty=False)
        anomaly_map = np.ones((2, 2))
        pred_boxes = np.array([[2, 2, 4, 4]])
        pred_mask = np.ones((2, 2))
        raw_prediction = AnomalyResult(
            anomaly_map=anomaly_map,
            pred_boxes=pred_boxes,
            pred_mask=pred_mask,
            pred_label="Anomalous",
            pred_score=1.0,
        )

        # Act
        converter = AnomalyToAnnotationConverter(label_schema)
        annotations = converter.convert_to_annotations(raw_prediction)

        # Assert
        assert converter.labels == labels
        assert len(annotations) == 1 if domain == Domain.ANOMALY_CLASSIFICATION else 2
        anomalous_label_id = next(label.id_ for label in labels if label.is_anomalous)
        assert anomalous_label_id in annotations[0].get_label_ids()
        assert Rectangle.is_full_box(annotations[0].shape)
        if domain == Domain.ANOMALY_SEGMENTATION:
            expected_polygon = Polygon(points=[Point(0.0, 0.0), Point(0.0, 1.0), Point(1.0, 1.0), Point(1.0, 0.0)])
            for p1, p2 in zip(annotations[1].shape.points, expected_polygon.points):
                assert p1.x == pytest.approx(p2.x, 0.01)
                assert p1.y == pytest.approx(p2.y, 0.01)
        elif domain == Domain.ANOMALY_DETECTION:
            expected_bbox = Rectangle(1, 1, 2, 2)
            assert annotations[1].shape.x1 == pytest.approx(expected_bbox.x1, 0.01)
            assert annotations[1].shape.y1 == pytest.approx(expected_bbox.y1, 0.01)
            assert annotations[1].shape.x2 == pytest.approx(expected_bbox.x2, 0.01)
            assert annotations[1].shape.y2 == pytest.approx(expected_bbox.y2, 0.01)

    def test_keypoint_to_annotation_converter(self, fxt_label_schema_factory):
        # Arrange
        label_schema = fxt_label_schema_factory(Domain.KEYPOINT_DETECTION)
        labels = label_schema.get_labels(include_empty=False)
        labels_str = [label.name for label in labels]
        keypoints = [[10, 20], [30, 40]]
        scores = [0.8, 0.9]
        metadata = {"original_shape": (100, 100, 3)}
        raw_prediction = DetectedKeypoints(keypoints=keypoints, scores=scores)

        # Act
        converter = KeypointToAnnotationConverter(label_schema, model_api_labels=labels_str)
        annotations = converter.convert_to_annotations(raw_prediction, metadata=metadata)

        # Assert
        assert converter.labels == labels
        assert len(annotations) == 2
        assert annotations[0].shape.x == 0.1
        assert annotations[0].shape.y == 0.2
        assert annotations[0].shape.is_visible
        assert annotations[1].shape.x == 0.3
        assert annotations[1].shape.y == 0.4
        assert annotations[1].shape.is_visible

    @pytest.mark.parametrize("domain", [Domain.DETECTION, Domain.ROTATED_DETECTION, Domain.SEGMENTATION])
    def test_visual_prompting_to_annotation_converter(self, domain, fxt_label_schema_factory):
        # Arrange
        label_schema = fxt_label_schema_factory(domain)
        labels = label_schema.get_labels(include_empty=False)
        labels_str = [label.name for label in labels]
        idx_to_label_map = {0: labels[0]}
        mask = np.array(
            [
                [0, 0, 0, 0, 0],
                [0, 1, 1, 1, 0],
                [0, 0, 1, 1, 0],
                [0, 0, 1, 1, 0],
                [0, 0, 0, 0, 0],
            ]
        )
        raw_prediction = ZSLVisualPromptingResult(
            data={0: PredictedMask(mask=[mask], points=np.array([[1, 1], [4, 1], [4, 4], [1, 4]]), scores=[0.51])}
        )
        height, width = mask.shape
        metadata = {"original_shape": (height, width, 3)}
        expected_rotated_bbox_polygon_points = [
            Point(x=1 / width, y=1 / height),
            Point(x=3 / width, y=1 / height),
            Point(x=3 / width, y=3 / height),
            Point(x=1 / width, y=3 / height),
        ]
        expected_polygon_points = [
            Point(x=1 / width, y=1 / height),
            Point(x=2 / width, y=2 / height),
            Point(x=2 / width, y=3 / height),
            Point(x=3 / width, y=3 / height),
            Point(x=3 / width, y=1 / height),
        ]

        # Act
        converter = VisualPromptingToAnnotationConverter(label_schema=label_schema, model_api_labels=labels_str)
        annotations = converter.convert_to_annotations(
            raw_prediction, idx_to_label_map=idx_to_label_map, metadata=metadata
        )

        # Assert
        assert len(annotations) == 1
        shape = annotations[0].shape

        match domain:
            case Domain.DETECTION:
                assert isinstance(shape, Rectangle)
                assert [shape.x1, shape.y1, shape.x2, shape.y2] == [0.2, 0.2, 0.8, 0.8]
            case Domain.ROTATED_DETECTION:
                assert isinstance(shape, Polygon)
                assert len(shape.points) == 4
                for p1, p2 in zip(shape.points, expected_rotated_bbox_polygon_points):
                    assert p1.x == pytest.approx(p2.x, 0.01)
                    assert p1.y == pytest.approx(p2.y, 0.01)
            case Domain.SEGMENTATION:
                assert isinstance(shape, Polygon)
                assert len(shape.points) == 5
                for p1, p2 in zip(shape.points, expected_polygon_points):
                    assert p1.x == pytest.approx(p2.x, 0.01)
                    assert p1.y == pytest.approx(p2.y, 0.01)
        assert annotations[0].get_labels()[0].id_ == labels[0].id_

    @pytest.mark.parametrize(
        "label_names, model_api_labels",
        [
            (["foo bar", "foo_bar"], ["foo_bar", "foo_bar"]),
            (["label 1", "label 2"], ["label_1", "label_2"]),
            (["?", "@"], ["@", "?"]),
            (["c", "b", "a", "empty"], ["a", "b", "c"]),
            (["1"], [1]),
        ],
    )
    def test_legacy_label_conversion(self, label_names, model_api_labels, fxt_label_schema):
        # Arrange
        labels = [Label(id_=f"{i}", name=name, domain=Domain.CLASSIFICATION) for i, name in enumerate(label_names)]

        # Act
        with patch.object(LabelSchema, "get_labels", return_value=labels):
            conv = ClassificationToAnnotationConverter(label_schema=fxt_label_schema, model_api_labels=model_api_labels)

        # Assert
        # check all model api labels correspond to a distinct geti label
        seen_labels = set()
        for i, name in enumerate(model_api_labels):
            name = str(name)
            label = conv.get_label_by_idx(i)
            assert label.name.replace(" ", "_") == name
            assert label not in seen_labels
            seen_labels.add(label)
