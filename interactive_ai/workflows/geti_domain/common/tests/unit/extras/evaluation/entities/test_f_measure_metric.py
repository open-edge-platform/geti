# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import pytest
from geti_types import ID, ImageIdentifier
from iai_core_py.entities.annotation import Annotation, AnnotationScene, AnnotationSceneKind
from iai_core_py.entities.dataset_item import DatasetItem
from iai_core_py.entities.datasets import Dataset
from iai_core_py.entities.image import Image
from iai_core_py.entities.label import Domain, Label
from iai_core_py.entities.label_schema import LabelGroup, LabelGroupType, LabelSchema
from iai_core_py.entities.media import MediaPreprocessing, MediaPreprocessingStatus
from iai_core_py.entities.metrics import BarMetricsGroup, MultiScorePerformance, ScoreMetric
from iai_core_py.entities.scored_label import ScoredLabel
from iai_core_py.entities.shapes import Rectangle

from jobs_common_extras.evaluation.entities.f_measure_metric import FMeasureMetric


@pytest.fixture
def fxt_empty_label():
    yield Label(name="label_empty", domain=Domain.DETECTION, is_empty=True, id_=ID("label_empty_id"))


@pytest.fixture
def fxt_labels(fxt_empty_label):
    yield [
        Label(name="label_a", domain=Domain.DETECTION, id_=ID("label_a_id")),
        Label(name="label_b", domain=Domain.DETECTION, id_=ID("label_b_id")),
        fxt_empty_label,
    ]


@pytest.fixture
def fxt_label_schema(fxt_labels):
    label_schema = LabelSchema(id_=ID("label_schema_id"))
    label_a, label_b, empty_label = fxt_labels
    label_group = LabelGroup(labels=[label_a, label_b], name="dummy detection label group")
    label_schema.add_group(label_group)
    empty_label_group = LabelGroup(
        labels=[empty_label], name="dummy detection empty group", group_type=LabelGroupType.EMPTY_LABEL
    )
    label_schema.add_group(empty_label_group)
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
def fxt_no_object_dataset_item_factory(fxt_empty_label):
    """
    Generates annotation with no objects
    """

    def no_object_item_factory(media: Image, prob: float = 1.0) -> DatasetItem:
        scored_label = ScoredLabel(label_id=fxt_empty_label.id_, is_empty=True, probability=prob)
        annotation = Annotation(shape=Rectangle.generate_full_box(), labels=[scored_label])
        return DatasetItem(
            id_=ID(f"dataset_item_id_{media.id_}"),
            media=media,
            annotation_scene=AnnotationScene(
                kind=AnnotationSceneKind.ANNOTATION,
                media_identifier=media.media_identifier,
                media_height=media.height,
                media_width=media.width,
                id_=ID("annotation_scene_id"),
                annotations=[annotation],
            ),
        )

    yield no_object_item_factory


@pytest.fixture
def fxt_centered_rec_box_dataset_item_factory():
    """
    Generates annotation with a centered rectangle box (0.25, 0.25, 0.75, 0.75) and a single label with probability 1.0
    """

    def centered_rec_box_item_factory(media: Image, scored_label: ScoredLabel) -> DatasetItem:
        annotation = Annotation(shape=Rectangle(x1=0.25, y1=0.25, x2=0.75, y2=0.75), labels=[scored_label])
        return DatasetItem(
            id_=ID(f"dataset_item_id_{media.id_}"),
            media=media,
            annotation_scene=AnnotationScene(
                kind=AnnotationSceneKind.ANNOTATION,
                media_identifier=ImageIdentifier(image_id=ID("image_id")),
                media_height=media.height,
                media_width=media.width,
                id_=ID("annotation_scene_id"),
                annotations=[annotation],
            ),
        )

    yield centered_rec_box_item_factory


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
def fxt_predicted_bbox(fxt_labels, fxt_generate_prediction_bbox):
    label_a, label_b, _ = fxt_labels
    yield [
        # label_a
        fxt_generate_prediction_bbox(0.5, 0.5, 0.5, 0.5, label_a),  # iou = 1.0
        fxt_generate_prediction_bbox(0.5, 0.5, 0.52, 0.48, label_a),  # iou = 0.92
        fxt_generate_prediction_bbox(0.4, 0.5, 0.5, 0.5, label_a),  # iou = 0.67
        fxt_generate_prediction_bbox(0.6, 0.5, 0.5, 0.5, label_a),  # iou = 0.67
        fxt_generate_prediction_bbox(0.75, 0.5, 0.5, 0.5, label_a),  # iou = 0.33
        # label_b
        fxt_generate_prediction_bbox(0.5, 0.5, 0.52, 0.48, label_b),  # iou = 0.92
        fxt_generate_prediction_bbox(0.5, 0.5, 0.45, 0.55, label_b),  # iou = 0.83
        fxt_generate_prediction_bbox(0.5, 0.5, 0.6, 0.6, label_b),  # iou = 0.7
        None,  # false negative
        fxt_generate_prediction_bbox(0.5, 0.5, 0.5, 0.5, label_a),  # false positive
    ]


@pytest.fixture
def fxt_ground_truth_dataset(fxt_labels, fxt_media_factory, fxt_centered_rec_box_dataset_item_factory):
    """
    Ground truth dataset contains 10 dataset items with 2 labels:
        - 5 items with centered bbox with label_a
        - 5 items with centered bbox with label_b
    """
    label_a = fxt_labels[0]
    label_b = fxt_labels[1]
    dataset_items = []
    for i in range(5):
        item = fxt_centered_rec_box_dataset_item_factory(
            media=fxt_media_factory(i),
            scored_label=ScoredLabel(label_id=label_a.id_, is_empty=label_a.is_empty, probability=1.0),
        )
        dataset_items.append(item)
    for i in range(5, 10):
        item = fxt_centered_rec_box_dataset_item_factory(
            media=fxt_media_factory(i),
            scored_label=ScoredLabel(label_id=label_b.id_, is_empty=label_b.is_empty, probability=1.0),
        )
        dataset_items.append(item)
    yield Dataset(id=ID("ground_truth_dataset_id"), items=dataset_items)


@pytest.fixture
def fxt_overall_scores(fxt_labels):
    # see fxt_prediction_dataset for details
    label_a, label_b, empty_label = fxt_labels
    yield {
        "f_measure": 0.74,
        "precision": 7 / 9,
        "recall": 7 / 10,
        label_a: 0.73,
        label_b: 0.75,
        empty_label: 0.0,
    }


@pytest.fixture
def fxt_prediction_dataset(fxt_media_factory, fxt_predicted_bbox):
    """
    Prediction dataset contains corresponding predictions to fxt_ground_truth_dataset with fixed probability (0.8):
        - label_a: 4 bbox with iou > 0.5
        - label_b: 3 bbox wit iou > 0.5, 1 false negative and 1 false positive
        - metrics:
            - f_measure ~ 0.74        -> (label_a: ~0.73), (label_b: ~0.75)
            - precision ~ 0.78 (7/9)  -> (label_a: 4/6), (label_b: 3/3)
            - recall ~ 0.7 (7/10)     -> (label_a: 4/5), (label_b: 3/5)
    """
    dataset_items = []
    for i, bbox in enumerate(fxt_predicted_bbox):
        media = fxt_media_factory(i)
        dataset_item = DatasetItem(
            id_=ID(f"prediction_dataset_item_id_{media.id_}"),
            media=media,
            annotation_scene=AnnotationScene(
                kind=AnnotationSceneKind.ANNOTATION,
                media_identifier=ImageIdentifier(image_id=ID("image_id")),
                media_height=media.height,
                media_width=media.width,
                id_=ID("annotation_scene_id"),
                annotations=[bbox] if bbox else [],
            ),
        )
        dataset_items.append(dataset_item)
    yield Dataset(id=ID("prediction_dataset_id"), items=dataset_items)


@pytest.mark.JobsComponent
class TestFMeasureMetric:
    def test_f_measure_metric_basic(
        self, fxt_ground_truth_dataset, fxt_prediction_dataset, fxt_label_schema, fxt_overall_scores
    ) -> None:
        metric = FMeasureMetric(
            ground_truth_dataset=fxt_ground_truth_dataset,
            prediction_dataset=fxt_prediction_dataset,
            label_schema=fxt_label_schema,
        )
        assert metric.f_measure.score == pytest.approx(fxt_overall_scores["f_measure"], 0.01)

    def test_get_performance(
        self, fxt_ground_truth_dataset, fxt_prediction_dataset, fxt_label_schema, fxt_labels, fxt_overall_scores
    ) -> None:
        # Arrange
        label_a, label_b, _ = fxt_labels
        metric = FMeasureMetric(
            ground_truth_dataset=fxt_ground_truth_dataset,
            prediction_dataset=fxt_prediction_dataset,
            label_schema=fxt_label_schema,
        )

        # Act
        performance = metric.get_performance()

        # Assert
        assert isinstance(performance, MultiScorePerformance)
        assert performance.primary_score.name == FMeasureMetric.metric_name
        assert performance.primary_score.score == pytest.approx(fxt_overall_scores["f_measure"], 0.01)
        precision_score, recall_score = performance.additional_scores
        assert precision_score.name.lower() == "precision"
        assert precision_score.score == pytest.approx(fxt_overall_scores["precision"], 0.01)
        assert recall_score.name.lower() == "recall"
        assert recall_score.score == pytest.approx(fxt_overall_scores["recall"], 0.01)

        assert len(performance.dashboard_metrics) == 1
        (f_measure_per_label,) = performance.dashboard_metrics
        # f-measure per label
        assert isinstance(f_measure_per_label, BarMetricsGroup)
        f_measure_label_a, f_measure_label_b = f_measure_per_label.metrics
        assert isinstance(f_measure_label_a, ScoreMetric)
        assert isinstance(f_measure_label_b, ScoreMetric)
        assert f_measure_label_a.score == pytest.approx(fxt_overall_scores[label_a], 0.01)
        assert f_measure_label_b.score == pytest.approx(fxt_overall_scores[label_b], 0.01)

    def test_get_per_media_scores(
        self, fxt_ground_truth_dataset, fxt_prediction_dataset, fxt_label_schema, fxt_labels, fxt_media_factory
    ) -> None:
        # Arrange
        metric = FMeasureMetric(
            ground_truth_dataset=fxt_ground_truth_dataset,
            prediction_dataset=fxt_prediction_dataset,
            label_schema=fxt_label_schema,
        )

        # Act
        per_media_scores = metric.get_per_media_scores()

        # Assert
        # Each media has 3 scores:
        #   - media f-measure
        #   - f_measure for label_a
        #   - f_measure for label_b
        # Check correct predictions scores
        media_indices_with_correct_predictions = [0, 1, 2, 3, 5, 6, 7]
        for i in media_indices_with_correct_predictions:
            gt_item = fxt_ground_truth_dataset[i]
            pred_item = fxt_prediction_dataset[i]
            gt_label_id = next(iter(gt_item.annotation_scene.get_label_ids()))
            pred_label_id = next(iter(pred_item.annotation_scene.get_label_ids()))
            media_id = fxt_media_factory(i).media_identifier
            media_f_measure, empty_label_score, label_a_score, label_b_score = per_media_scores[media_id]
            assert media_f_measure.value == (1 if gt_label_id == pred_label_id else 0)
            assert label_a_score.value == (
                1 if gt_label_id == label_a_score.label_id and pred_label_id == label_a_score.label_id else 0
            )
            assert label_b_score.value == (
                1 if gt_label_id == label_b_score.label_id and pred_label_id == label_b_score.label_id else 0
            )
            assert empty_label_score.value == (
                1 if gt_label_id == empty_label_score.label_id and pred_label_id == empty_label_score.label_id else 0
            )

        # Check incorrect predictions (indices [4, 8, 9])
        incorrect_pred_media_scores = [per_media_scores[fxt_media_factory(i).media_identifier] for i in [4, 8, 9]]
        for media_f_measure, label_a_score, label_b_score, empty_label_score in incorrect_pred_media_scores:
            assert media_f_measure.value == 0
            assert label_a_score.value == 0
            assert label_b_score.value == 0
            assert empty_label_score.value == 0

    def test_get_per_label_scores(
        self,
        fxt_ground_truth_dataset,
        fxt_prediction_dataset,
        fxt_label_schema,
        fxt_labels,
        fxt_media_factory,
        fxt_overall_scores,
    ) -> None:
        # Arrange
        label_a, label_b, empty_label = fxt_labels
        metric = FMeasureMetric(
            ground_truth_dataset=fxt_ground_truth_dataset,
            prediction_dataset=fxt_prediction_dataset,
            label_schema=fxt_label_schema,
        )

        # Act
        per_label_scores = metric.get_per_label_scores()

        # Assert
        # Each label has a score for each label
        score_label_a, score_label_b, empty_label_score = per_label_scores
        assert score_label_a.label_id == label_a.id_
        assert score_label_a.score == pytest.approx(fxt_overall_scores[label_a], 0.01)
        assert score_label_b.label_id == label_b.id_
        assert score_label_b.score == pytest.approx(fxt_overall_scores[label_b], 0.01)
        assert empty_label_score.label_id == empty_label.id_
        assert empty_label_score.score == pytest.approx(fxt_overall_scores[empty_label], 0.01)

    def test_score_with_no_object_class(
        self, fxt_no_object_dataset_item_factory, fxt_media_factory, fxt_label_schema, fxt_empty_label
    ) -> None:
        # Arrange
        # Create ground truth and prediction datasets with 10 items with no objects class
        gt_dataset_items = []
        pred_dataset_items = []
        for i in range(10):
            media = fxt_media_factory(i)
            gt_dataset_items.append(fxt_no_object_dataset_item_factory(media=media, prob=1.0))
            pred_dataset_items.append(fxt_no_object_dataset_item_factory(media=media, prob=0.8))
        gt_dataset = Dataset(id=ID("ground_truth_dataset_id"), items=gt_dataset_items)
        pred_dataset = Dataset(id=ID("prediction_dataset_id"), items=pred_dataset_items)
        metric = FMeasureMetric(
            ground_truth_dataset=gt_dataset,
            prediction_dataset=pred_dataset,
            label_schema=fxt_label_schema,
        )

        # Act
        performance = metric.get_performance()
        per_media_scores = metric.get_per_media_scores()
        per_label_scores = metric.get_per_label_scores()

        # Assert
        assert performance.primary_score.score == 0.0  # no object class is ignored in the global performance
        assert len(performance.additional_scores) == 2
        assert performance.additional_scores[0].score == 1.0  # precision
        assert performance.additional_scores[1].score == 0.0  # recall
        for _, media_scores in per_media_scores.items():
            for score_metric in media_scores:
                # assert that global media score is 0.0 and empty label score is 1.0, else 0.0
                if score_metric.label_id == fxt_empty_label.id_:
                    assert score_metric.value == 1.0
                else:
                    assert score_metric.value == 0.0
        for score_metric in per_label_scores:
            if score_metric.label_id == fxt_empty_label.id_:
                assert score_metric.score == 1.0
            else:
                assert score_metric.score == 0.0
