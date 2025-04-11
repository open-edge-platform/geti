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

import pytest
from geti_types import ID, ImageIdentifier
from sc_sdk.entities.annotation import Annotation, AnnotationScene, AnnotationSceneKind
from sc_sdk.entities.dataset_item import DatasetItem
from sc_sdk.entities.datasets import Dataset
from sc_sdk.entities.image import Image
from sc_sdk.entities.label import Domain, Label
from sc_sdk.entities.label_schema import LabelGroup, LabelSchema
from sc_sdk.entities.media import MediaPreprocessing, MediaPreprocessingStatus
from sc_sdk.entities.metrics import AnomalyLocalizationPerformance
from sc_sdk.entities.scored_label import ScoredLabel
from sc_sdk.entities.shapes import Rectangle

from jobs_common_extras.evaluation.entities.accuracy_metric import AccuracyMetric
from jobs_common_extras.evaluation.entities.anomaly_metrics import (
    AnomalyDetectionScores,
    AnomalyMetric,
    AnomalySegmentationScores,
)
from jobs_common_extras.evaluation.entities.dice_metric import DiceMetric
from jobs_common_extras.evaluation.entities.f_measure_metric import FMeasureMetric


def create_full_box_dataset_item(media: Image, scored_label: ScoredLabel, kind: AnnotationSceneKind) -> DatasetItem:
    full_box_rec = Rectangle(x1=0.0, y1=0.0, x2=1.0, y2=1.0)
    return DatasetItem(
        id_=ID("dataset_item_id"),
        media=media,
        annotation_scene=AnnotationScene(
            kind=kind,
            media_identifier=ImageIdentifier(image_id=ID("image_id")),
            media_height=media.height,
            media_width=media.width,
            id_=ID("annotation_scene_id"),
            annotations=[Annotation(shape=full_box_rec, labels=[scored_label])],
        ),
    )


@pytest.fixture
def fxt_labels():
    yield [
        Label(name="label_a", domain=Domain.ANOMALY_DETECTION, id_=ID("label_a_id"), is_anomalous=True),
        Label(name="label_b", domain=Domain.ANOMALY_DETECTION, id_=ID("label_b_id"), is_anomalous=False),
    ]


@pytest.fixture
def fxt_label_schema(fxt_labels):
    label_schema = LabelSchema(id_=ID("label_schema_id"))
    label_a, label_b = fxt_labels
    label_group = LabelGroup(labels=[label_a, label_b], name="dummy label group")
    label_schema.add_group(label_group)
    yield label_schema


@pytest.fixture
def fxt_media_factory():
    def media_factory(index: int):
        return Image(
            name=f"dummy_image_{index}.jpg",
            uploader_id=f"dummy_name_{index}",
            id=ID(f"image_id_{index}"),
            width=100,
            height=100,
            size=100,
            preprocessing=MediaPreprocessing(status=MediaPreprocessingStatus.FINISHED),
        )

    yield media_factory


@pytest.fixture
def fxt_generate_prediction_bbox():
    """
    Generated prediction given the center point and size of the box.
    """

    def generate_prediction_rec_box(center_x: float, center_y: float, width: float, height: float, label: Label):
        scored_label = ScoredLabel(label_id=label.id_, is_empty=label.is_empty, probability=0.8)
        return Annotation(
            shape=Rectangle(
                x1=center_x - width / 2,
                y1=center_y - height / 2,
                x2=center_x + width / 2,
                y2=center_y + height / 2,
            ),
            labels=[scored_label],
        )

    return generate_prediction_rec_box


@pytest.fixture
def fxt_ground_truth_dataset(fxt_labels, fxt_media_factory):
    """
    Ground truth dataset contains 10 dataset items with 2 labels:
        - 5 items with centered bbox with label_a
        - 5 items with centered bbox with label_b

    Note: dice metric automatically converts bbox rectangles to polygons.
    """
    label_a = fxt_labels[0]
    label_b = fxt_labels[1]
    dataset_items = []
    # global annotations [normal vs anomalous]
    scored_label_a = ScoredLabel(label_id=label_a.id_, is_empty=label_a.is_empty, probability=1.0)
    scored_label_b = ScoredLabel(label_id=label_b.id_, is_empty=label_b.is_empty, probability=1.0)
    for i in range(5):
        item = create_full_box_dataset_item(
            media=fxt_media_factory(i),
            scored_label=scored_label_a,
            kind=AnnotationSceneKind.ANNOTATION,
        )
        dataset_items.append(item)
    for i in range(5, 10):
        item = create_full_box_dataset_item(
            media=fxt_media_factory(i),
            scored_label=scored_label_b,
            kind=AnnotationSceneKind.ANNOTATION,
        )
        dataset_items.append(item)
    # add local annotations [detection/segmentation shapes], only one per label
    local_anno = Annotation(shape=Rectangle(x1=0.25, y1=0.25, x2=0.75, y2=0.75), labels=[scored_label_a])
    dataset_items[0].annotation_scene.annotations.append(local_anno)
    dataset_items[1].annotation_scene.annotations.append(local_anno)
    yield Dataset(id=ID("ground_truth_dataset_id"), items=dataset_items)


@pytest.fixture
def fxt_prediction_dataset(fxt_media_factory, fxt_ground_truth_dataset, fxt_labels, fxt_generate_prediction_bbox):
    """
    Prediction dataset contains corresponding predictions to fxt_ground_truth_dataset with fixed probability.
    Anomaly metrics is composed of a global and local metric, depending on the local task we have the following:
        - Anomaly detection:
            - global metric: accuracy -> 7 / 10
            - local metric: f-measure -> 1.0
        - Anomaly segmentation:
            - global metric: accuracy -> 7 / 10
            - local metric: dice score -> 0.90


    Note: all prediction dataset contains local prediction for all media, but metric should filter based on
        the ground truth annotations.
    """
    label_a = fxt_labels[0]
    label_b = fxt_labels[1]
    num_a_correct = 4
    num_b_correct = 3
    pred_dataset_items = []

    for i, gt_item in enumerate(fxt_ground_truth_dataset):
        label_id = list(gt_item.annotation_scene.get_label_ids())[0]
        if label_id == label_a.id_:
            pred_label = label_a if num_a_correct > 0 else label_b
            num_a_correct -= 1
        else:
            pred_label = label_b if num_b_correct > 0 else label_a
            num_b_correct -= 1
        pred_item = create_full_box_dataset_item(
            media=fxt_media_factory(i),
            scored_label=ScoredLabel(label_id=pred_label.id_, is_empty=pred_label.is_empty, probability=0.8),
            kind=AnnotationSceneKind.PREDICTION,
        )
        local_pred = fxt_generate_prediction_bbox(0.5, 0.5, 0.45, 0.55, label_a)
        pred_item.annotation_scene.annotations.append(local_pred)
        pred_dataset_items.append(pred_item)
    yield Dataset(id=ID("prediction_dataset_id"), items=pred_dataset_items)


@pytest.mark.JobsComponent
class TestAnomalyMetrics:
    def test_global_subsets(self, fxt_ground_truth_dataset, fxt_prediction_dataset):
        gt_subset = AnomalyMetric.get_global_subset(fxt_ground_truth_dataset)
        pred_subset = AnomalyMetric.get_global_subset(fxt_prediction_dataset)

        # Global subset should contain all dataset items
        assert len(gt_subset) == 10
        assert len(pred_subset) == 10
        # Check all dataset items contain only full box annoation
        for gt_item, pred_item in zip(gt_subset, pred_subset):
            assert len(gt_item.annotation_scene.annotations) == 1
            assert len(pred_item.annotation_scene.annotations) == 1
            assert Rectangle.is_full_box(gt_item.annotation_scene.annotations[0].shape)
            assert Rectangle.is_full_box(pred_item.annotation_scene.annotations[0].shape)

    def test_local_subsets(self, fxt_ground_truth_dataset, fxt_prediction_dataset, fxt_label_schema):
        local_items_indices = AnomalyMetric._locally_annotated_indices(
            dataset=fxt_ground_truth_dataset, label_schema=fxt_label_schema
        )
        gt_subset = AnomalyMetric.get_local_subset(fxt_ground_truth_dataset, local_indices=local_items_indices)
        pred_subset = AnomalyMetric.get_local_subset(fxt_prediction_dataset, local_indices=local_items_indices)

        # Global subset should contain only 2 dataset items
        assert len(gt_subset) == 2
        assert len(pred_subset) == 2
        # Check all dataset items contain only one local annotation
        for gt_item, pred_item in zip(gt_subset, pred_subset):
            assert len(gt_item.annotation_scene.annotations) == 1
            assert len(pred_item.annotation_scene.annotations) == 1
            assert not Rectangle.is_full_box(gt_item.annotation_scene.annotations[0].shape)
            assert not Rectangle.is_full_box(pred_item.annotation_scene.annotations[0].shape)

    def test_anomaly_detection_scores(self, fxt_ground_truth_dataset, fxt_prediction_dataset, fxt_label_schema) -> None:
        metric = AnomalyDetectionScores(
            ground_truth_dataset=fxt_ground_truth_dataset,
            prediction_dataset=fxt_prediction_dataset,
            label_schema=fxt_label_schema,
            use_local_metric=True,
        )

        assert isinstance(metric.global_metric, AccuracyMetric)
        assert isinstance(metric.local_metric, FMeasureMetric)
        performance = metric.get_performance()
        assert isinstance(performance, AnomalyLocalizationPerformance)
        assert performance.global_score.score == 0.7
        assert performance.local_score.score == 1.0

    def test_anomaly_segmentation_scores(
        self, fxt_ground_truth_dataset, fxt_prediction_dataset, fxt_label_schema
    ) -> None:
        metric = AnomalySegmentationScores(
            ground_truth_dataset=fxt_ground_truth_dataset,
            prediction_dataset=fxt_prediction_dataset,
            label_schema=fxt_label_schema,
            use_local_metric=True,
        )

        assert isinstance(metric.global_metric, AccuracyMetric)
        assert isinstance(metric.local_metric, DiceMetric)
        performance = metric.get_performance()
        assert isinstance(performance, AnomalyLocalizationPerformance)
        assert performance.global_score.score == 0.7
        assert performance.local_score.score == pytest.approx(0.9, 0.01)
