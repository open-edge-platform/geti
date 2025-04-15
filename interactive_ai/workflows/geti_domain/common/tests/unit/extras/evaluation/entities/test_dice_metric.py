# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import pytest
from geti_types import ID, ImageIdentifier
from sc_sdk.entities.annotation import Annotation, AnnotationScene, AnnotationSceneKind
from sc_sdk.entities.dataset_item import DatasetItem
from sc_sdk.entities.datasets import Dataset
from sc_sdk.entities.image import Image
from sc_sdk.entities.label import Domain, Label
from sc_sdk.entities.label_schema import LabelGroup, LabelGroupType, LabelSchema
from sc_sdk.entities.media import MediaPreprocessing, MediaPreprocessingStatus
from sc_sdk.entities.metrics import BarMetricsGroup, Performance, ScoreMetric
from sc_sdk.entities.scored_label import ScoredLabel
from sc_sdk.entities.shapes import Rectangle

from jobs_common_extras.evaluation.entities.dice_metric import DiceMetric
from jobs_common_extras.evaluation.entities.performance_metric import MetricAverageMethod


@pytest.fixture
def fxt_empty_label():
    yield Label(name="label_empty", domain=Domain.INSTANCE_SEGMENTATION, is_empty=True, id_=ID("label_empty_id"))


@pytest.fixture
def fxt_labels(fxt_empty_label):
    yield [
        Label(name="label_a", domain=Domain.INSTANCE_SEGMENTATION, id_=ID("label_a_id")),
        Label(name="label_b", domain=Domain.INSTANCE_SEGMENTATION, id_=ID("label_b_id")),
        fxt_empty_label,
    ]


@pytest.fixture
def fxt_label_schema(fxt_labels):
    label_schema = LabelSchema(id_=ID("label_schema_id"))
    label_a, label_b, empty_label = fxt_labels
    label_group = LabelGroup(labels=[label_a, label_b], name="dummy segmentation label group")
    label_schema.add_group(label_group)
    empty_label_group = LabelGroup(
        labels=[empty_label], name="dummy segmentation empty group", group_type=LabelGroupType.EMPTY_LABEL
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
def fxt_overall_scores(fxt_labels):
    # See fxt_predicted_bbox amd fxt_prediction_dataset for details.
    label_a, label_b, _ = fxt_labels
    yield {
        MetricAverageMethod.MICRO: 0.664,
        MetricAverageMethod.MACRO: 0.668,
        label_a: 0.703,
        label_b: 0.620,
    }


@pytest.fixture
def fxt_per_media_scores():
    # See fxt_predicted_bbox for details.
    # Format: (media_dice_score, label_a_score, label_b_score)
    yield [
        # label_a scores
        (1.0, 1.0, 0.0),
        (0.8, 0.8, 0.0),
        (0.8, 0.8, 0.0),
        (0.78, 0.78, 0.0),
        (0.50, 0.50, 0.0),
        # label_b scores
        (0.9, 0.0, 0.9),
        (0.82, 0.0, 0.82),
        (0.685, 0.0, 0.685),
        (0.0, 0.0, 0.0),
        (0.0, 0.0, 0.0),
    ]


@pytest.fixture
def fxt_predicted_bbox(fxt_labels, fxt_generate_prediction_bbox):
    label_a, label_b, _ = fxt_labels
    # Fixed image shape: (100, 100)
    yield [
        # label_a
        # A ∩ B = 2500, |A| + |B| = 5000, dice = 1.0
        fxt_generate_prediction_bbox(0.5, 0.5, 0.5, 0.5, label_a),
        # A ∩ B = 2000, |A| + |B| = 5000, dice = 0.80
        fxt_generate_prediction_bbox(0.4, 0.5, 0.5, 0.5, label_a),
        # A ∩ B = 2000, |A| + |B| = 5000, dice = 0.80
        fxt_generate_prediction_bbox(0.6, 0.5, 0.5, 0.5, label_a),
        # A ∩ B = 1600, |A| + |B| = 4100, dice = 0.78
        fxt_generate_prediction_bbox(0.5, 0.5, 0.4, 0.4, label_a),
        # A ∩ B = 1250, |A| + |B| = 5000, dice = 0.50
        fxt_generate_prediction_bbox(0.76, 0.5, 0.5, 0.5, label_a),
        # label_b
        # A ∩ B = 2250, |A| + |B| = 4975, dice = 0.90
        fxt_generate_prediction_bbox(0.5, 0.5, 0.45, 0.55, label_b),
        # A ∩ B = 2500, |A| + |B| = 6100, dice = 0.82
        fxt_generate_prediction_bbox(0.5, 0.5, 0.6, 0.6, label_b),
        # A ∩ B = 2500, |A| + |B| = 7300, dice = 0.68
        fxt_generate_prediction_bbox(0.5, 0.5, 0.6, 0.8, label_b),
        # A ∩ B = 0, |A| + |B| = 2500, dice = 0.0
        None,
        # A ∩ B = 0, |A| + |B| = 2500, dice = 0.0 -> union will be summed to total union for label_a
        fxt_generate_prediction_bbox(0.5, 0.5, 0.5, 0.5, label_a),
    ]


@pytest.fixture
def fxt_ground_truth_dataset(fxt_labels, fxt_media_factory, fxt_centered_rec_box_dataset_item_factory):
    """
    Ground truth dataset contains 10 dataset items with 2 labels:
        - 5 items with centered bbox with label_a
        - 5 items with centered bbox with label_b

    Note: dice metric automatically converts bbox rectangles to polygons.
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
def fxt_prediction_dataset(fxt_media_factory, fxt_predicted_bbox):
    """
    Prediction dataset contains corresponding predictions to fxt_ground_truth_dataset with fixed probability.
    Dice score (intersection over union of pixel maps): 2 * |A ∩ B| / (|A| + |B|)
    Average dice score:
        - label_a = 0.703
        - label_b = 0.620
        - overall average:
            - MICRO (all pixels have same weight): (2 * 16600) / (49975) = 0.664
            - MACRO (average of per-label score): (0.78 + 0.48) / 2 = 0.668

    Note:
        - dice metric automatically converts bbox rectangles to polygons.
        - depending on how the bbox is converted to pixel map, an extra column/row of pixels might be included.
        This means that the precise score might slightly vary with a tolerance of 1e-03.
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
class TestDiceMetric:
    @pytest.mark.parametrize("average", (MetricAverageMethod.MICRO, MetricAverageMethod.MACRO))
    def test_dice_metric_basic(
        self,
        average,
        fxt_ground_truth_dataset,
        fxt_prediction_dataset,
        fxt_label_schema,
        fxt_labels,
        fxt_overall_scores,
    ) -> None:
        label_a, label_b, _ = fxt_labels
        metric = DiceMetric(
            ground_truth_dataset=fxt_ground_truth_dataset,
            prediction_dataset=fxt_prediction_dataset,
            label_schema=fxt_label_schema,
            average=average,
        )

        assert metric.overall_dice.score == pytest.approx(fxt_overall_scores[average], 0.01)
        assert metric.dice_per_label[label_a].score == pytest.approx(fxt_overall_scores[label_a], 0.01)
        assert metric.dice_per_label[label_b].score == pytest.approx(fxt_overall_scores[label_b], 0.01)

    def test_get_performance(
        self, fxt_ground_truth_dataset, fxt_prediction_dataset, fxt_label_schema, fxt_labels, fxt_overall_scores
    ) -> None:
        # Arrange
        label_a, label_b, _ = fxt_labels
        metric = DiceMetric(
            ground_truth_dataset=fxt_ground_truth_dataset,
            prediction_dataset=fxt_prediction_dataset,
            label_schema=fxt_label_schema,
        )

        # Act
        performance = metric.get_performance()

        # Assert
        assert isinstance(performance, Performance)
        assert performance.score.score == pytest.approx(fxt_overall_scores[MetricAverageMethod.MACRO], 0.01)
        assert performance.dashboard_metrics is not None
        assert isinstance(performance.dashboard_metrics[0], BarMetricsGroup)
        metrics = performance.dashboard_metrics[0].metrics
        per_label_metrics = {m.label_id: m.score for m in metrics if isinstance(m, ScoreMetric)}
        assert per_label_metrics[label_a.id_] == pytest.approx(fxt_overall_scores[label_a], 0.01)
        assert per_label_metrics[label_b.id_] == pytest.approx(fxt_overall_scores[label_b], 0.01)

    def test_get_per_media_scores(
        self,
        fxt_ground_truth_dataset,
        fxt_prediction_dataset,
        fxt_label_schema,
        fxt_labels,
        fxt_media_factory,
        fxt_per_media_scores,
    ) -> None:
        # Arrange
        label_a, label_b, _ = fxt_labels
        metric = DiceMetric(
            ground_truth_dataset=fxt_ground_truth_dataset,
            prediction_dataset=fxt_prediction_dataset,
            label_schema=fxt_label_schema,
        )

        # Act
        per_media_scores = metric.get_per_media_scores()

        # Assert
        # Each media has 3 scores:
        #   - media dice score
        #   - dice score for label_a
        #   - dice score for label_b
        # Check correct predictions scores
        for i, (media_score, label_a_score, label_b_score) in enumerate(fxt_per_media_scores):
            media_id = fxt_media_factory(i).media_identifier
            media_metric_score, label_a_metric_score, label_b_metric_score = per_media_scores[media_id]
            assert media_metric_score.value == pytest.approx(media_score, 0.01)
            assert label_a_metric_score.value == pytest.approx(label_a_score, 0.01)
            assert label_b_metric_score.value == pytest.approx(label_b_score, 0.01)

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
        label_a, label_b, _ = fxt_labels
        metric = DiceMetric(
            ground_truth_dataset=fxt_ground_truth_dataset,
            prediction_dataset=fxt_prediction_dataset,
            label_schema=fxt_label_schema,
        )

        # Act
        per_label_scores = metric.get_per_label_scores()

        # Assert
        # Each label has a score for each label
        score_label_a, score_label_b = per_label_scores
        assert score_label_a.label_id == label_a.id_
        assert score_label_a.score == pytest.approx(fxt_overall_scores[label_a], 0.01)
        assert score_label_b.label_id == label_b.id_
        assert score_label_b.score == pytest.approx(fxt_overall_scores[label_b], 0.01)

    def test_score_with_no_object_class(
        self, fxt_no_object_dataset_item_factory, fxt_media_factory, fxt_label_schema
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
        metric = DiceMetric(
            ground_truth_dataset=gt_dataset,
            prediction_dataset=pred_dataset,
            label_schema=fxt_label_schema,
        )

        # Act
        performance = metric.get_performance()

        # Assert
        # Dice score is only computed on non-empty labels and annotated labels
        assert performance.score.score == 0.0
        assert not metric.get_per_label_scores()
