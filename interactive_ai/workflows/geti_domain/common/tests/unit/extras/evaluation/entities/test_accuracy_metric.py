# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import itertools
from collections.abc import Sequence
from typing import cast

import numpy as np
import pytest
from geti_types import ID, ImageIdentifier
from iai_core_py.entities.annotation import Annotation, AnnotationScene, AnnotationSceneKind
from iai_core_py.entities.dataset_item import DatasetItem
from iai_core_py.entities.datasets import Dataset
from iai_core_py.entities.image import Image
from iai_core_py.entities.label import Domain, Label
from iai_core_py.entities.label_schema import LabelGroup, LabelGroupType, LabelSchema, LabelSchemaView, LabelTree
from iai_core_py.entities.media import MediaPreprocessing, MediaPreprocessingStatus
from iai_core_py.entities.metrics import BarMetricsGroup, MatrixMetric, MatrixMetricsGroup, ScoreMetric
from iai_core_py.entities.scored_label import ScoredLabel
from iai_core_py.entities.shapes import Rectangle
from iai_core_py.repos import LabelRepo, LabelSchemaRepo

from jobs_common_extras.evaluation.entities.accuracy_metric import AccuracyMetric


def decode_label_schema(label_schema_str: str, project_id: ID | None) -> LabelSchema:
    """
    Given a string encoded representation of a label schema, decode it to build the
    equivalent LabelSchema object.

    Encoding format:
      - <groups>;<connections>
      - <groups> = <group1>|<group2>|...
      - <group> = <name>,<domain>,<label1>,<label2>,...
      - <connections> = <connection1>,<connection2>
      - <connection> = <parent>><child>

    To create an empty label, define one with the name 'empty'.

    :param label_schema_str: string encoded label schema
    :param project_id: ID of the project
    :return: LabelSchema
    """
    groups_full_str, connections_str = label_schema_str.split(";")[:2]
    label_names_by_group_name: dict[str, tuple[str, ...]] = {}
    domain_by_label_name: dict[str, Domain] = {}

    # parse groups
    for group_str in groups_full_str.split("|"):
        group_name, domain_str, labels_str = group_str.split(",", maxsplit=2)
        label_names = tuple(labels_str.split(","))
        for label_name in label_names:
            domain_by_label_name[label_name] = Domain[domain_str.upper()]
        label_names_by_group_name[group_name] = label_names

    # parse connections
    connections: tuple[list[str], ...] = tuple(
        connection_str.split(">") for connection_str in connections_str.split(",") if connection_str
    )

    # create labels
    label_by_name: dict[str, Label] = {
        label_name: Label(
            name=label_name,
            domain=domain_by_label_name[label_name],
            is_empty=(label_name == "empty"),
            id_=LabelRepo.generate_id(),
        )
        for label_name in itertools.chain.from_iterable(label_names_by_group_name.values())
    }

    # create groups
    groups: list[LabelGroup] = [
        LabelGroup(
            name=group_name,
            labels=[label_by_name[label_name] for label_name in group_labels],
            group_type=(
                LabelGroupType.EMPTY_LABEL
                if any(label_by_name[lbl].is_empty for lbl in group_labels)
                else LabelGroupType.EXCLUSIVE
            ),
        )
        for group_name, group_labels in label_names_by_group_name.items()
    ]

    # create label tree
    label_tree = LabelTree()
    for parent_name, child_name in connections:
        label_tree.add_child(
            parent=label_by_name[parent_name],
            child=label_by_name[child_name],
        )

    # create label schema
    return LabelSchema(
        id_=LabelSchemaRepo.generate_id(), label_tree=label_tree, label_groups=groups, project_id=project_id
    )


def create_label_schema_view_for_task(label_schema: LabelSchema, task_id: ID, domain: Domain) -> LabelSchemaView:
    task_labels = [cast(Label, lbl) for lbl in label_schema.get_labels(True) if lbl.domain == domain]
    return LabelSchemaView.from_parent(
        parent_schema=label_schema,
        labels=task_labels,
        task_node_id=task_id,
        id_=LabelSchemaRepo.generate_id(),
    )


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
def fxt_classification_gt_pred_datasets_factory(fxt_ote_id, fxt_image_entity_factory):
    def _build_datasets(
        media_gt_pred_list: Sequence[tuple[str, Sequence[str], Sequence[str]]],
        label_schema: LabelSchema,
    ) -> tuple[Dataset, Dataset]:
        label_by_name = {label.name: label for label in label_schema.get_labels(True)}
        media_by_name: dict[str, Image] = {}
        gt_scene_by_media_name: dict[str, AnnotationScene] = {}
        pred_scene_by_media_name: dict[str, AnnotationScene] = {}
        gt_dataset_items: list[DatasetItem] = []
        pred_dataset_items: list[DatasetItem] = []
        full_box = Rectangle(0, 0, 1, 1)
        for media_name, gt_labels_names, pred_labels_names in media_gt_pred_list:
            if media_name in media_by_name:
                media = media_by_name[media_name]
                gt_scene = gt_scene_by_media_name[media_name]
                pred_scene = pred_scene_by_media_name[media_name]
            else:
                media = fxt_image_entity_factory(index=hash(media_name), name=media_name)
                media_by_name[media_name] = media
                gt_scene = AnnotationScene(
                    kind=AnnotationSceneKind.ANNOTATION,
                    media_identifier=media.media_identifier,
                    media_height=100,
                    media_width=100,
                    id_=fxt_ote_id(hash(media_name + "_gt_scene")),
                    annotations=[],
                )
                pred_scene = AnnotationScene(
                    kind=AnnotationSceneKind.PREDICTION,
                    media_identifier=media.media_identifier,
                    media_height=100,
                    media_width=100,
                    id_=fxt_ote_id(hash(media_name + "_pred_scene")),
                    annotations=[],
                )
                gt_scene_by_media_name[media_name] = gt_scene
                pred_scene_by_media_name[media_name] = pred_scene

            gt_labels = [
                ScoredLabel(label_id=label_by_name[name].id_, is_empty=label_by_name[name].is_empty, probability=1.0)
                for name in gt_labels_names
            ]
            gt_annotation = Annotation(shape=full_box, labels=gt_labels)
            gt_scene.append_annotation(gt_annotation)
            gt_dataset_item = DatasetItem(
                id_=fxt_ote_id(hash(media_name + "_gt_item")), media=media, annotation_scene=gt_scene, roi=gt_annotation
            )
            gt_dataset_items.append(gt_dataset_item)

            pred_labels = [
                ScoredLabel(label_id=label_by_name[name].id_, is_empty=label_by_name[name].is_empty, probability=1.0)
                for name in pred_labels_names
            ]
            pred_annotation = Annotation(shape=full_box, labels=pred_labels)
            pred_scene.append_annotation(pred_annotation)
            pred_dataset_item = DatasetItem(
                media=media,
                annotation_scene=pred_scene,
                roi=pred_annotation,
                id_=fxt_ote_id(hash(media_name + "_pred_item")),
            )
            pred_dataset_items.append(pred_dataset_item)

        gt_dataset = Dataset(items=gt_dataset_items, id=fxt_ote_id(hash("gt_dataset")))
        pred_dataset = Dataset(items=pred_dataset_items, id=fxt_ote_id(hash("pred_dataset")))
        return gt_dataset, pred_dataset

    yield _build_datasets


@pytest.fixture
def fxt_labels():
    yield [
        Label(name="label_a", domain=Domain.CLASSIFICATION, id_=ID("label_a_id")),
        Label(name="label_b", domain=Domain.CLASSIFICATION, id_=ID("label_b_id")),
        Label(name="label_empty", domain=Domain.CLASSIFICATION, is_empty=True, id_=ID("label_empty_id")),
    ]


@pytest.fixture
def fxt_label_schema(fxt_labels):
    label_schema = LabelSchema(id_=ID("label_schema_id"))
    label_a, label_b, empty_label = fxt_labels
    label_group = LabelGroup(labels=[label_a, label_b], name="dummy classification label group")
    label_schema.add_group(label_group)
    empty_label_group = LabelGroup(
        labels=[empty_label], name="dummy classification empty group", group_type=LabelGroupType.EMPTY_LABEL
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
def fxt_gt_pred_labels(fxt_labels):
    """
    - label_a is predicted 4/7 correctly
    - label_b is predicted 3/6 correctly
    - metrics:
        - accuracy = (4 + 3) / 10 = 0.7
        - precision_label_a = 4 / (4 + 1) = 4 / 5
        - precision_label_b = 3 / (3 + 2) = 3 / 5
        - recall_label_a = 4 / (4 + 2) = 4 / 6
        - recall_label_b = 3 / (3 + 1) = 3 / 4
    - Confusion matrix (prediction on column):
        |   | a | b |
        |---|---|---|
        | a | 4 | 2 |
        | b | 1 | 3 |
    """
    label_a, label_b, _ = fxt_labels
    # (gt_label, pred_label)
    yield [
        (label_a, label_a),
        (label_a, label_a),
        (label_a, label_a),
        (label_a, label_a),
        (label_a, label_b),
        (label_a, label_b),
        (label_b, label_b),
        (label_b, label_b),
        (label_b, label_b),
        (label_b, label_a),
    ]


@pytest.fixture
def fxt_ground_truth_dataset(fxt_gt_pred_labels, fxt_media_factory):
    """
    Ground truth dataset contains 10 dataset items with 2 labels:
        - 5 items with label_a
        - 5 items with label_b
    """
    dataset_items = []
    for i, (gt_label, _) in enumerate(fxt_gt_pred_labels):
        item = create_full_box_dataset_item(
            media=fxt_media_factory(i),
            scored_label=ScoredLabel(label_id=gt_label.id_, is_empty=gt_label.is_empty, probability=1.0),
            kind=AnnotationSceneKind.ANNOTATION,
        )
        dataset_items.append(item)
    yield Dataset(id=ID("ground_truth_dataset_id"), items=dataset_items)


@pytest.fixture
def fxt_prediction_dataset(fxt_gt_pred_labels, fxt_media_factory, fxt_ground_truth_dataset):
    """
    Prediction dataset contains corresponding predictions to fxt_ground_truth_dataset with fixed probability (0.8)
    """
    pred_dataset_items = []

    for i, (_, pred_label) in enumerate(fxt_gt_pred_labels):
        item = create_full_box_dataset_item(
            media=fxt_media_factory(i),
            scored_label=ScoredLabel(label_id=pred_label.id_, is_empty=pred_label.is_empty, probability=1.0),
            kind=AnnotationSceneKind.PREDICTION,
        )
        pred_dataset_items.append(item)
    yield Dataset(id=ID("prediction_dataset_id"), items=pred_dataset_items)


@pytest.mark.JobsComponent
class TestAccuracyMetric:
    def test_accuracy_metric_basic(self, fxt_ground_truth_dataset, fxt_prediction_dataset, fxt_label_schema) -> None:
        metric = AccuracyMetric(
            ground_truth_dataset=fxt_ground_truth_dataset,
            prediction_dataset=fxt_prediction_dataset,
            label_schema=fxt_label_schema,
        )

        assert metric.accuracy.score == 0.7

    def test_get_performance(
        self, fxt_ground_truth_dataset, fxt_prediction_dataset, fxt_labels, fxt_label_schema
    ) -> None:
        # Arrange
        label_a, label_b, empty_label = fxt_labels
        label_group = fxt_label_schema.get_groups()[0]
        label_names = [label.name for label in label_group.labels]
        normalized_confusion_matrix = MatrixMetric(
            name=f"{label_group.name}",
            matrix_values=np.array([[4, 2], [1, 3]], dtype=np.single),
            row_labels=label_names,
            column_labels=label_names,
        )
        normalized_confusion_matrix.normalize()
        precision_per_class = [
            ScoreMetric(name=label_a.name, value=4 / 5),
            ScoreMetric(name=label_b.name, value=3 / 5),
            ScoreMetric(name=empty_label.name, value=1),
        ]
        recall_per_class = [
            ScoreMetric(name=label_a.name, value=4 / 6),
            ScoreMetric(name=label_b.name, value=3 / 4),
            ScoreMetric(name=empty_label.name, value=1),
        ]

        # Act
        metric = AccuracyMetric(
            ground_truth_dataset=fxt_ground_truth_dataset,
            prediction_dataset=fxt_prediction_dataset,
            label_schema=fxt_label_schema,
        )

        # Assert
        performance = metric.get_performance()
        assert performance.score.name == AccuracyMetric.metric_name
        assert performance.score.score == 0.7
        assert isinstance(performance.dashboard_metrics[0], MatrixMetricsGroup)
        matrix_metric = performance.dashboard_metrics[0].metrics[0]
        assert matrix_metric.name == normalized_confusion_matrix.name
        assert matrix_metric.row_labels == normalized_confusion_matrix.row_labels
        assert matrix_metric.column_labels == normalized_confusion_matrix.column_labels
        for v1, v2 in zip(matrix_metric.matrix_values.flatten(), normalized_confusion_matrix.matrix_values.flatten()):
            assert v1 == pytest.approx(v2)
        assert isinstance(performance.dashboard_metrics[1], BarMetricsGroup)
        precision_per_class_metrics = performance.dashboard_metrics[1].metrics
        for actual, expected in zip(precision_per_class_metrics, precision_per_class):
            assert actual.name == expected.name
            assert actual.value == pytest.approx(expected.value)
        assert isinstance(performance.dashboard_metrics[2], BarMetricsGroup)
        recall_per_class_metrics = performance.dashboard_metrics[2].metrics
        for actual, expected in zip(recall_per_class_metrics, recall_per_class):
            assert actual.name == expected.name
            assert actual.value == pytest.approx(expected.value)

    def test_get_per_media_scores(
        self, fxt_ground_truth_dataset, fxt_prediction_dataset, fxt_label_schema, fxt_labels
    ) -> None:
        # Arrange
        label_a, label_b, empty_label = fxt_labels
        metric = AccuracyMetric(
            ground_truth_dataset=fxt_ground_truth_dataset,
            prediction_dataset=fxt_prediction_dataset,
            label_schema=fxt_label_schema,
        )

        # Act
        per_media_scores = metric.get_per_media_scores()

        # Assert
        # Each media has 4 scores:
        #   - media accuracy (correct / total predictions)
        #   - accuracy for label_a
        #   - accuracy for label_b
        #   - accuracy for empty label
        for gt_item, pred_item in zip(fxt_ground_truth_dataset, fxt_prediction_dataset):
            media_id = gt_item.media_identifier
            media_accuracy, *label_scores = per_media_scores[media_id]
            gt_label_id = next(iter(gt_item.annotation_scene.get_label_ids()))
            pred_label_id = next(iter(pred_item.annotation_scene.get_label_ids()))
            expected_scores = {
                label_a.id_: (1 if gt_label_id == label_a.id_ and pred_label_id == label_a.id_ else 0),
                label_b.id_: (1 if gt_label_id == label_b.id_ and pred_label_id == label_b.id_ else 0),
                empty_label.id_: (1 if gt_label_id == empty_label.id_ and pred_label_id == empty_label.id_ else 0),
            }
            assert media_accuracy.value == (1 if gt_label_id == pred_label_id else 0)
            for label_score in label_scores:
                assert label_score.value == expected_scores[label_score.label_id]

    def test_get_per_label_scores(
        self, fxt_ground_truth_dataset, fxt_prediction_dataset, fxt_label_schema, fxt_labels
    ) -> None:
        # Arrange
        label_a, label_b, empty_label = fxt_labels
        metric = AccuracyMetric(
            ground_truth_dataset=fxt_ground_truth_dataset,
            prediction_dataset=fxt_prediction_dataset,
            label_schema=fxt_label_schema,
        )

        # Act
        per_label_scores = metric.get_per_label_scores()

        # Assert
        # Each label has a score for each label
        score_label_a, score_label_b, score_empty_label = per_label_scores
        assert score_label_a.label_id == label_a.id_
        assert score_label_a.score == pytest.approx(4 / 7, 0.01)
        assert score_label_b.label_id == label_b.id_
        assert score_label_b.score == pytest.approx(0.5, 0.01)
        assert score_empty_label.label_id == empty_label.id_
        assert score_empty_label.score == 1.0

    @pytest.mark.parametrize(
        "encoded_label_schema,media_gt_pred_list,media_acc,label_acc,dataset_acc",
        [
            (
                "grp1,classification,a,b,c;",
                (
                    ("m1", ["a"], ["a"]),
                    ("m2", ["b"], ["b"]),
                    ("m3", ["c"], ["c"]),
                ),
                {"m1": 1.0, "m2": 1.0, "m3": 1.0},
                {"a": 1.0, "b": 1.0, "c": 1.0},
                1.0,
            ),
            (
                "grp1,classification,a,b,c;",
                (
                    ("m1", ["a"], ["a"]),
                    ("m2", ["a"], ["b"]),
                    ("m3", ["a"], ["c"]),
                    ("m4", ["b"], ["b"]),
                    ("m5", ["b"], ["c"]),
                ),
                {"m1": 1.0, "m2": 0, "m3": 0, "m4": 1.0, "m5": 0},
                {"a": 0.33, "b": 0.33, "c": 0},
                0.4,
            ),
            (
                "grp1,classification,a,b,c;",
                (
                    ("m1", ["a"], ["a"]),
                    ("m2", ["a"], ["b"]),
                    ("m3", ["b"], ["b"]),
                ),
                {"m1": 1.0, "m2": 0, "m3": 1.0},
                {"a": 0.5, "b": 0.5, "c": 1.0},
                0.67,
            ),
            (
                "grp0,detection,det0|grp1,classification,a,b,c;",
                (
                    ("m1", ["a"], ["a"]),
                    ("m1", ["a"], ["b"]),
                    ("m1", ["b"], ["c"]),
                    ("m2", ["b"], ["b"]),
                    ("m2", ["b"], ["c"]),
                ),
                {"m1": 0.33, "m2": 0.5},
                {"a": 0.5, "b": 0.25, "c": 0},
                0.4,
            ),
            (
                "grp0,detection,det0|grp1,classification,a,b;",
                (
                    ("m1", ["a"], ["a"]),
                    ("m1", ["b"], ["a"]),
                    ("m1", ["b"], ["a"]),
                    ("m1", ["b"], ["a"]),
                    ("m1", ["b"], ["a"]),
                    ("m1", ["b"], ["b"]),
                ),
                {"m1": 0.33},
                {"a": 0.2, "b": 0.2},
                0.33,
            ),
            (
                "grp0,detection,det0|grp1,classification,a,b,c;",
                (
                    ("m1", ["a"], ["a"]),
                    ("m1", ["b"], ["a"]),
                    ("m1", ["b"], ["a"]),
                    ("m1", ["b"], ["a"]),
                    ("m1", ["b"], ["a"]),
                    ("m1", ["b"], ["b"]),
                ),
                {"m1": 0.33},
                {"a": 0.2, "b": 0.2, "c": 1.0},
                0.33,
            ),
            (
                "grp1,classification,a|grp2,classification,b|grp3,classification,c|grp4,classification,empty;",
                (
                    ("m1", ["a"], ["a"]),
                    ("m2", ["a", "b"], ["a", "b"]),
                    ("m3", ["a", "b", "c"], ["a", "b", "c"]),
                    ("m4", ["b", "c"], ["b", "c"]),
                    ("m5", ["empty"], ["empty"]),
                ),
                {"m1": 1.0, "m2": 1.0, "m3": 1.0, "m4": 1.0, "m5": 1.0},
                {"a": 1.0, "b": 1.0, "c": 1.0, "empty": 1.0},
                1.0,
            ),
            (
                "grp1,classification,a|grp2,classification,b|grp3,classification,c|grp4,classification,empty;",
                (
                    ("m1", ["a"], ["a"]),
                    ("m2", ["a", "b"], ["a", "b"]),
                    ("m3", ["a", "c"], ["c"]),
                    ("m4", ["b", "c"], ["empty"]),
                    ("m5", ["empty"], ["b"]),
                    ("m5", ["empty"], ["empty"]),
                ),
                {"m1": 1.0, "m2": 1.0, "m3": 0.5, "m4": 0, "m5": 0},
                {"a": 0.67, "b": 0.33, "c": 0.5, "empty": 0.33},
                0.5,
            ),
            (
                "grp1,classification,a|grp2,classification,b|grp3,classification,c|"
                "grp4,classification,d|grp5,classification,empty;",
                (
                    ("m1", ["a"], ["a"]),
                    ("m2", ["a", "b"], ["a", "b"]),
                    ("m3", ["a", "c"], ["b", "c"]),
                ),
                {"m1": 1.0, "m2": 1.0, "m3": 0.33},
                {"a": 0.67, "b": 0.5, "c": 1.0, "d": 1.0, "empty": 1.0},
                0.67,
            ),
            (
                "grp0,detection,det|grp1,classification,a|grp2,classification,b|"
                "grp3,classification,c|grp4,classification,empty;",
                (
                    ("m1", ["a"], ["a", "b"]),
                    ("m1", ["b"], ["c"]),
                    ("m2", ["a", "c"], ["a", "b", "c"]),
                    ("m2", ["a", "b"], ["empty"]),
                    ("m2", ["empty"], ["a"]),
                ),
                {"m1": 0.25, "m2": 0.33},
                {"a": 0.5, "b": 0, "c": 0.5, "empty": 0},
                0.3,
            ),
            (
                "grp0,detection,det|grp1,classification,a,b|grp2,classification,c,d|grp3,classification,e;",
                (
                    ("m1", ["a", "c", "e"], ["a", "c", "e"]),
                    ("m1", ["a", "d", "e"], ["b", "c", "e"]),
                    ("m1", ["b", "c"], ["b", "d"]),
                    ("m2", ["b", "c"], ["b", "c", "e"]),
                    ("m2", ["b", "d", "e"], ["a", "c"]),
                ),
                {"m1": 0.63, "m2": 0.33},
                {"a": 0.33, "b": 0.5, "c": 0.4, "d": 0, "e": 0.5},
                0.5,
            ),
            (
                "grp0,detection,det|grp1,classification,a,b|grp2,classification,c|"
                "grp1_1,classification,d,e|grp1_2,classification,f|"
                "grp2_1,classification,g,h|grp2_2,classification,i;"
                "a>d,a>e,a>f,c>g,c>h,c>i",
                (
                    ("m1", ["a", "d"], ["a", "d"]),
                    ("m2", ["b"], ["b"]),
                    ("m3", ["b", "c", "h"], ["b", "c", "h"]),
                    ("m4", ["a", "e", "c", "i"], ["a", "e", "c", "i"]),
                ),
                {"m1": 1.0, "m2": 1.0, "m3": 1.0, "m4": 1.0},
                {"a": 1.0, "b": 1.0, "c": 1.0, "d": 1.0, "e": 1.0, "f": 1.0, "g": 1.0, "h": 1.0, "i": 1.0},
                1.0,
            ),
            (
                "grp0,detection,det|grp1,classification,a,b|grp2,classification,c|"
                "grp1_1,classification,d,e|grp1_2,classification,f|"
                "grp2_1,classification,g,h|grp2_2,classification,i;"
                "a>d,a>e,a>f,c>g,c>h,c>i",
                (
                    ("m1", ["a", "d"], ["a", "e"]),
                    ("m1", ["b"], ["b", "c"]),
                    ("m1", ["b"], ["a", "d", "c", "g"]),
                    ("m2", ["a", "e", "c", "g", "i"], ["a", "d", "c", "g"]),
                    ("m2", ["b", "c", "g", "i"], ["b", "c", "g", "i"]),
                    ("m3", ["a", "e", "c", "h", "i"], ["a", "d", "f", "c", "h", "i"]),
                    ("m3", ["b", "c", "h", "i"], ["b"]),
                ),
                {"m1": 0.25, "m2": 0.78, "m3": 0.55},
                {"a": 0.75, "b": 0.75, "c": 0.5, "d": 0, "e": 0, "f": 0, "g": 0.67, "h": 0.5, "i": 0.5},
                0.54,
            ),
        ],
        ids=[
            "multiclass, perfect classifier",
            "multiclass, mixed data",
            "multiclass, unrepresented label",
            "multiclass, task chain, mixed data",
            "binary multiclass, task chain",
            "non-binary multiclass, multi-item, unrepresented label",
            "multilabel, perfect classifier",
            "multilabel, mixed data",
            "multilabel, unrepresented label",
            "multilabel, task chain, mixed data",
            "hybrid multiclass multilabel, mixed data, task chain",
            "hierarchical hybrid multiclass multilabel, task chain, perfect classifier",
            "hierarchical hybrid multiclass multilabel, task chain, mixed data",
        ],
    )
    def test_compute_accuracy_correctness(
        self,
        encoded_label_schema,
        media_gt_pred_list,
        media_acc,
        label_acc,
        dataset_acc,
        fxt_classification_gt_pred_datasets_factory,
    ) -> None:
        label_schema = decode_label_schema(label_schema_str=encoded_label_schema, project_id=ID("dummy_project_id"))
        task_label_schema = create_label_schema_view_for_task(
            label_schema=label_schema,
            domain=Domain.CLASSIFICATION,
            task_id=ID("dummy_task_id"),
        )
        gt_dataset, pred_dataset = fxt_classification_gt_pred_datasets_factory(
            media_gt_pred_list=media_gt_pred_list,
            label_schema=label_schema,
        )
        media_name_by_identifier = {item.media_identifier: item.media.name for item in gt_dataset}

        # Act
        metric = AccuracyMetric(
            ground_truth_dataset=gt_dataset,
            prediction_dataset=pred_dataset,
            label_schema=task_label_schema,
        )

        # Check the 'per-media' and 'per-media per-label' scores
        num_media = len({item.media_identifier for item in gt_dataset})
        per_media_scores = metric.get_per_media_scores()
        assert len(per_media_scores) == num_media
        for media_identifier, media_scores in per_media_scores.items():
            media_name = media_name_by_identifier[media_identifier]
            # Check that exactly one per-media score is present for this media
            assert sum(score_point.label_id is None for score_point in media_scores) == 1, (
                f"Missing score for media {media_name}"
            )
            # Check that at least 1 per-media per-label score is present
            assert sum(score_point.label_id is not None for score_point in media_scores) >= 1, (
                f"Missing per-label scores for media {media_name}"
            )
            # Check the score values
            for score_point in media_scores:
                assert score_point.name == AccuracyMetric.metric_name
                if score_point.label_id is None:  # per-media accuracy
                    assert score_point.score == pytest.approx(media_acc[media_name], abs=0.01), (
                        f"Wrong score for media {media_name}"
                    )
                else:  # per-media per-label
                    assert 0 <= score_point.score <= 1.0, f"Invalid per-label score for media {media_name}"

        # Check the per-dataset
        assert metric.accuracy.value == pytest.approx(dataset_acc, abs=0.01), "Wrong score for dataset"

        # Check per-label accuracy
        per_label_scores = metric.get_per_label_scores()
        for score_point in per_label_scores:
            assert score_point.name == AccuracyMetric.metric_name
            assert score_point.label_id is not None
            label = label_schema.get_label_by_id(score_point.label_id)
            assert label is not None
            assert score_point.score == pytest.approx(label_acc[label.name], abs=0.01), (
                f"Wrong score for label {label.name}"
            )
