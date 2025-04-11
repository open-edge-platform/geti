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

import numpy as np
import pytest
from geti_types import ID, ImageIdentifier
from sc_sdk.entities.annotation import Annotation, AnnotationScene, AnnotationSceneKind
from sc_sdk.entities.dataset_item import DatasetItem
from sc_sdk.entities.datasets import Dataset
from sc_sdk.entities.image import Image
from sc_sdk.entities.label import Domain, Label
from sc_sdk.entities.label_schema import LabelGroup, LabelSchema
from sc_sdk.entities.media import MediaPreprocessing, MediaPreprocessingStatus
from sc_sdk.entities.metrics import BarMetricsGroup, Performance, ScoreMetric, TextMetricsGroup
from sc_sdk.entities.scored_label import ScoredLabel
from sc_sdk.entities.shapes import Keypoint

from jobs_common_extras.evaluation.entities.percentage_of_correct_keypoints_metric import (
    PercentageCorrectKeypointsMetric,
)


@pytest.fixture
def fxt_empty_label():
    yield Label(
        name="label_empty",
        domain=Domain.KEYPOINT_DETECTION,
        id_=ID("label_empty_id"),
        is_empty=True,
    )


@pytest.fixture
def fxt_labels(fxt_empty_label):
    yield [
        Label(
            name="label_top_left",
            domain=Domain.KEYPOINT_DETECTION,
            id_=ID("label_tl_id"),
        ),
        Label(
            name="label_top_right",
            domain=Domain.KEYPOINT_DETECTION,
            id_=ID("label_tr_id"),
        ),
        Label(
            name="label_bottom_left",
            domain=Domain.KEYPOINT_DETECTION,
            id_=ID("label_bl_id"),
        ),
        Label(
            name="label_bottom_right",
            domain=Domain.KEYPOINT_DETECTION,
            id_=ID("label_br_id"),
        ),
    ]


@pytest.fixture
def fxt_label_schema(fxt_labels):
    label_schema = LabelSchema(id_=ID("label_schema_id"))
    label_top_left, label_top_right, label_bottom_left, label_bottom_right = fxt_labels
    label_group = LabelGroup(
        labels=[label_top_left, label_top_right, label_bottom_left, label_bottom_right],
        name="dummy keypoint detection label group",
    )
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
def fxt_annotation_factory(fxt_labels):
    """
    Generates an annotation with 4 keypoints at specified coordinates.
    """

    def annotation_factory(label, coordinates: tuple[float, float], is_visible: bool = True) -> Annotation:
        return Annotation(
            shape=Keypoint(x=coordinates[0], y=coordinates[1], is_visible=is_visible),
            labels=[ScoredLabel(label_id=label.id_, is_empty=label.is_empty, probability=1.0)],
        )

    yield annotation_factory


@pytest.fixture
def fxt_keypoints_dataset_item_factory(fxt_labels, fxt_annotation_factory):
    """
    Generates a DatasetItem with 4 keypoints at specified coordinates.
    """

    def keypoints_item_factory(
        media: Image, coordinates: list[tuple[float, float]], is_visible: list[int] = [0, 1, 2, 3]
    ) -> DatasetItem:
        label_top_left, label_top_right, label_bottom_left, label_bottom_right = fxt_labels

        annotations = [
            fxt_annotation_factory(label_top_left, coordinates[0], is_visible=0 in is_visible),  # top-left
            fxt_annotation_factory(label_top_right, coordinates[1], is_visible=1 in is_visible),  # top-right
            fxt_annotation_factory(label_bottom_left, coordinates[2], is_visible=2 in is_visible),  # bottom-left
            fxt_annotation_factory(label_bottom_right, coordinates[3], is_visible=3 in is_visible),  # bottom-right
        ]
        return DatasetItem(
            id_=ID(f"dataset_item_id_{media.id_}"),
            media=media,
            annotation_scene=AnnotationScene(
                id_=ID("annotation_scene_id"),
                kind=AnnotationSceneKind.ANNOTATION,
                media_identifier=ImageIdentifier(image_id=ID("image_id")),
                media_height=media.height,
                media_width=media.width,
                annotations=annotations,
            ),
        )

    yield keypoints_item_factory


@pytest.fixture
def fxt_keypoint_annotation_factory(fxt_labels):
    """
    Generates an annotation with 4 keypoint at specified coordinates.
    """

    def keypoint_annotation_factory(label, coordinates: tuple[float, float], is_visible: bool = True) -> Annotation:
        return Annotation(
            shape=Keypoint(x=coordinates[0], y=coordinates[1], is_visible=is_visible),
            labels=[ScoredLabel(label_id=label.id_, is_empty=label.is_empty, probability=1.0)],
        )

    yield keypoint_annotation_factory


@pytest.fixture
def fxt_ground_truth_dataset(fxt_labels, fxt_media_factory, fxt_keypoints_dataset_item_factory):
    """
    Ground truth dataset contains 10 dataset items with 4 keypoints:
        - 1 item with keypoints at (.1, .1), (.9, .1), (.1, .9), (.9, .9)
        - 1 item with keypoints at (.2, .2), invisible (.8, .2), (.2, .8), (.8, .8)
    """
    dataset_items = []
    for i in range(4):
        dataset_items.append(
            fxt_keypoints_dataset_item_factory(
                media=fxt_media_factory(i),
                coordinates=[(0.1, 0.1), (0.9, 0.1), (0.1, 0.9), (0.9, 0.9)],
            )
        )
    # 1 item with 1 invisible keypoint
    for i in range(2):
        dataset_items.append(
            fxt_keypoints_dataset_item_factory(
                media=fxt_media_factory(i + 6),
                coordinates=[(0.2, 0.2), (0.8, 0.2), (0.2, 0.8), (0.8, 0.8)],
                is_visible=[0, 2, 3],
            )
        )
    yield Dataset(id=ID("ground_truth_dataset_id"), items=dataset_items)


@pytest.fixture
def fxt_prediction_dataset(
    fxt_labels,
    fxt_media_factory,
    fxt_annotation_factory,
    fxt_keypoint_annotation_factory,
    fxt_keypoints_dataset_item_factory,
):
    """
    - 1 item with 4 correct keypoints at (.1, .1), (.9, .1), (.1, .9), (.9, .9)  | 100%
    - 1 item with 4 correct keypoints at (.15, .15), (.95, .15), (.15, .95), (.95, .95)  | 100%
    - 1 item with 2 correct keypoints at (.1, .1), (.9, .1), (.1, .2), (.2, .2) | 50%  (bl and br are incorrect)
    - 1 item with 3/4 correct keypoints with 3 predictions at (.1, .1), (.9, .1), (.1, .9) | 75% (br is missing)

    - 1 item with 3/3 correct keypoints with 3 predictions at (.2, .2), (x,x), (.2, .8), (.8, .8) | 100%
    - 1 item with 3/3 correct keypoints with 4 predictions at (.2, .2), (0, 0), (.2, .8), (.8, .8) | 100%
    """

    dataset_items = []
    dataset_items.append(
        fxt_keypoints_dataset_item_factory(
            media=fxt_media_factory(0),
            coordinates=[(0.1, 0.1), (0.9, 0.1), (0.1, 0.9), (0.9, 0.9)],
        )
    )
    dataset_items.append(
        fxt_keypoints_dataset_item_factory(
            media=fxt_media_factory(1),
            coordinates=[(0.15, 0.15), (0.95, 0.15), (0.15, 0.95), (0.95, 0.95)],
        )
    )
    dataset_items.append(
        fxt_keypoints_dataset_item_factory(
            media=fxt_media_factory(2),
            coordinates=[(0.1, 0.1), (0.9, 0.1), (0.1, 0.2), (0.2, 0.2)],
        )
    )
    # item with 3/4 correct keypoints because of 1 missing prediction (bottom right)
    p3_missing1 = fxt_keypoints_dataset_item_factory(
        media=fxt_media_factory(3),
        coordinates=[(0.1, 0.1), (0.9, 0.1), (0.1, 0.9), (0, 0)],
    )
    p3_missing1.annotation_scene.annotations.pop(3)
    dataset_items.append(p3_missing1)

    # item with 3/3 correct keypoints with 3 predictions
    p3_all = fxt_keypoints_dataset_item_factory(
        media=fxt_media_factory(4),
        coordinates=[(0.2, 0.2), (0, 0), (0.2, 0.8), (0.8, 0.8)],
    )
    # remove the second keypoint
    p3_all.annotation_scene.annotations.pop(1)
    dataset_items.append(p3_all)

    # item with 3/3 correct keypoints with 4 predictions (one more than needed)
    dataset_items.append(
        fxt_keypoints_dataset_item_factory(
            media=fxt_media_factory(5),
            coordinates=[(0.2, 0.2), (0, 0), (0.2, 0.8), (0.8, 0.8)],
        )
    )
    yield Dataset(id=ID("prediction_dataset_id"), items=dataset_items)


@pytest.fixture
def fxt_true_scores(fxt_labels):
    label_top_left, label_top_right, label_bottom_left, label_bottom_right = fxt_labels
    yield {
        label_top_left: 1,
        label_top_right: 1,
        label_bottom_left: 5 / 6,
        label_bottom_right: 4 / 6,
        "per_media_pck_values": [1, 1, 0.5, 0.75, 1, 1],
        "pck_value": 19 / 22,
    }


@pytest.mark.JobsComponent
class TestPercentageCorrectKeypointsMetric:
    def test_get_performance(self, fxt_ground_truth_dataset, fxt_prediction_dataset, fxt_label_schema, fxt_true_scores):
        """
        Validate if the average percentage of correct keypoints is computed correctly over given images.
        """
        # Arrange
        ground_truth_dataset = fxt_ground_truth_dataset
        prediction_dataset = fxt_prediction_dataset
        metric = PercentageCorrectKeypointsMetric(
            ground_truth_dataset=ground_truth_dataset,
            prediction_dataset=prediction_dataset,
            label_schema=fxt_label_schema,
        )

        # Act
        performance = metric.get_performance()

        # Assert
        assert isinstance(performance, Performance)
        assert performance.score.name == PercentageCorrectKeypointsMetric.metric_name
        # 2 items with correct keypoints, 1 item with 2/4 correct keypoints, 1 item with 3/4 correct keypoints
        assert performance.score.value == pytest.approx(fxt_true_scores["pck_value"], 0.01)
        assert len(performance.dashboard_metrics) == 2
        (average_pck_value, acc_per_label) = performance.dashboard_metrics

        assert isinstance(average_pck_value, TextMetricsGroup)
        assert average_pck_value.metrics[0].score == pytest.approx(fxt_true_scores["pck_value"], 0.01)

        assert isinstance(acc_per_label, BarMetricsGroup)

    def test_get_per_label_scores(
        self, fxt_ground_truth_dataset, fxt_prediction_dataset, fxt_label_schema, fxt_labels, fxt_true_scores
    ):
        """
        Validate if the accuracy computed per unique keypoint (label) is correct.
        """
        # Arrange
        ground_truth_dataset = fxt_ground_truth_dataset
        prediction_dataset = fxt_prediction_dataset
        label_top_left, label_top_right, label_bottom_left, label_bottom_right = fxt_labels
        metric = PercentageCorrectKeypointsMetric(
            ground_truth_dataset=ground_truth_dataset,
            prediction_dataset=prediction_dataset,
            label_schema=fxt_label_schema,
        )

        # Act
        per_label_scores = metric.get_per_label_scores()

        # Assert
        assert len(per_label_scores) == 4
        true_score_per_id = {
            label_top_left.id_: fxt_true_scores[label_top_left],
            label_top_right.id_: fxt_true_scores[label_top_right],
            label_bottom_left.id_: fxt_true_scores[label_bottom_left],
            label_bottom_right.id_: fxt_true_scores[label_bottom_right],
        }
        for score in per_label_scores:
            assert isinstance(score, ScoreMetric)
            assert score.label_id in true_score_per_id
            assert score.value == pytest.approx(true_score_per_id[score.label_id], 0.01)

    def test_get_per_media_scores(
        self, fxt_ground_truth_dataset, fxt_prediction_dataset, fxt_label_schema, fxt_true_scores
    ):
        """
        Validate if the percentage of correct keypoints is computed correctly for each image.
        """
        # Arrange
        ground_truth_dataset = fxt_ground_truth_dataset
        prediction_dataset = fxt_prediction_dataset
        metric = PercentageCorrectKeypointsMetric(
            ground_truth_dataset=ground_truth_dataset,
            prediction_dataset=prediction_dataset,
            label_schema=fxt_label_schema,
        )

        # Act
        per_media_scores = metric.get_per_media_scores()

        # Assert
        assert len(per_media_scores) == len(ground_truth_dataset)
        for idx, (media_id, scores) in enumerate(per_media_scores.items()):
            assert scores[0].value == pytest.approx(fxt_true_scores["per_media_pck_values"][idx], 0.01)

    def test_threshold(self, fxt_ground_truth_dataset, fxt_prediction_dataset, fxt_label_schema):
        """
        Validate if the bounding box of the keypoint is computed correctly.
        """
        relative_threshold = 0.1
        metric = PercentageCorrectKeypointsMetric(
            ground_truth_dataset=fxt_ground_truth_dataset,
            prediction_dataset=fxt_prediction_dataset,
            label_schema=fxt_label_schema,
            relative_distance_threshold=relative_threshold,
        )

        keypoints = [
            Keypoint(x=0.1, y=0.1, is_visible=True),
            Keypoint(x=0.9, y=0.1, is_visible=True),
            Keypoint(x=0.1, y=0.9, is_visible=True),
            Keypoint(x=0.9, y=0.9, is_visible=True),
        ]
        true_diagonal = np.sqrt(2) * 0.8

        # Act
        threshold = metric._compute_threshold([(k.x, k.y, "", k.is_visible) for k in keypoints])

        # Assert
        assert threshold == pytest.approx(true_diagonal * relative_threshold, 0.01)

        ## Test with keypoints that are not visible
        keypoints = [
            Keypoint(x=0.1, y=0.1, is_visible=False),
            Keypoint(x=0.9, y=0.1, is_visible=True),
            Keypoint(x=0.1, y=0.9, is_visible=True),
            Keypoint(x=0.9, y=0.9, is_visible=True),
        ]
        threshold = metric._compute_threshold([(k.x, k.y, "", k.is_visible) for k in keypoints])
        assert threshold == pytest.approx(true_diagonal * relative_threshold, 0.01)
