# INTEL CONFIDENTIAL
#
# Copyright (C) 2023 Intel Corporation
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

import itertools
import logging
import random
from collections import Counter
from collections.abc import Mapping, Sequence

import numpy as np
import pytest

from active_learning.algorithms import (
    FeatureReconstructionError,
    FeatureReconstructionErrorClassAgnostic,
    ScoringFunctionRequirements,
)

from geti_types import ID, MediaIdentifierEntity
from sc_sdk.entities.annotation import Annotation, AnnotationScene, AnnotationSceneKind
from sc_sdk.entities.dataset_item import DatasetItem
from sc_sdk.entities.datasets import Dataset, NullDataset
from sc_sdk.entities.label import Label
from sc_sdk.entities.metadata import MetadataItem
from sc_sdk.entities.scored_label import ScoredLabel
from sc_sdk.entities.shapes import Rectangle
from sc_sdk.entities.subset import Subset
from sc_sdk.entities.tensor import Tensor

logger = logging.getLogger(__name__)
random.seed("6371")


def pairwise(iterable):
    """
    Implementation of itertools.pairwise()
    s -> (s0,s1), (s1,s2), (s2, s3), ...
    """
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)


def assert_stratified_active_set_equivalent(
    active_set_1: Sequence[MediaIdentifierEntity],
    active_set_2: Sequence[MediaIdentifierEntity],
    predicted_label_per_media: Mapping[MediaIdentifierEntity, ID],
    train_labels: set[ID],
):
    """
    Check the equivalence of two active sets obtained through stratified sampling.

    Two active sets are equivalent if all the elements are in the same order except
    for potential permutations of elements within each sampling block.

    In other words, the i-th media with label X always precedes the (i+1)-th media
    with (same or different) label Y.

    Examples:
        - These two sets are equivalent
            A1 B1 C1 D1 | A2 B2 C2 D2
            B1 C1 A1 D1 | C2 D2 A2 B2

        - These two sets are not equivalent (B2 comes before D1)
            A1 B1 C1 D1 | A2 B2 C2 D2
            B1 C1 A1 B2 | D1 A2 C2 D2
    """
    assert len(active_set_1) == len(active_set_2)
    assert set(active_set_1) == set(active_set_2)

    # Do not check media whose predicted label does not appear in training set,
    # because their active score is set to a default value hence their stratification
    # order is non-deterministic.
    media_with_unseen_labels: set[MediaIdentifierEntity] = {
        media for media, label in predicted_label_per_media.items() if label not in train_labels
    }
    if media_with_unseen_labels:
        logger.info("Media with unseen labels: %s", media_with_unseen_labels)

    # Determine the delimiters of sampling blocks as the indices where the max frequency
    # across all items increases by 1.
    freq_counter: Counter = Counter()
    max_freq_at_index = []
    for media in active_set_1:
        label = predicted_label_per_media[media]
        freq_counter[label] += 1
        max_freq_at_index.append(freq_counter.most_common()[0][1])
    split_indices = (
        [0]
        + [i for i in range(1, len(max_freq_at_index)) if max_freq_at_index[i] != max_freq_at_index[i - 1]]
        + [len(max_freq_at_index)]
    )

    # Verify that each block contains the same elements, in any order
    for i, (start, end) in enumerate(pairwise(split_indices)):
        logger.info("Checking equivalence of the %d-th sampling block", i)
        active_set_1_block = set(active_set_1[start:end]) - media_with_unseen_labels
        active_set_2_block = set(active_set_2[start:end]) - media_with_unseen_labels
        assert active_set_1_block == active_set_2_block


@pytest.fixture
def fxt_dataset_item_factory(fxt_image_entity_factory, fxt_ote_id):
    def _build_item(
        index: int,
        label: Label,
        annotation_kind: AnnotationSceneKind,
        feature_vector: np.ndarray | None = None,
    ) -> DatasetItem:
        image = fxt_image_entity_factory(index=index)
        annotation = Annotation(
            shape=Rectangle(0, 0, 1, 1),
            labels=[ScoredLabel(label_id=label.id_, is_empty=label.is_empty, probability=1.0)],
            id_=fxt_ote_id(index),
        )
        ann_scene = AnnotationScene(
            kind=annotation_kind,
            media_identifier=image.media_identifier,
            media_height=100,
            media_width=100,
            id_=fxt_ote_id(1000 + index),
            annotations=[annotation],
        )
        dataset_item_id = fxt_ote_id(4000 + index)
        metadata_items: list[MetadataItem] = []
        if feature_vector is not None:
            metadata = Tensor(
                name="representation_vector",
                numpy=feature_vector,
            )
            metadata_item = MetadataItem(
                data=metadata,
                dataset_item_id=dataset_item_id,
                media_identifier=image.media_identifier,
                model=fxt_ote_id(500),
                id=fxt_ote_id(3000 + index),
            )
            metadata_items.append(metadata_item)
        return DatasetItem(
            media=fxt_image_entity_factory(index=index),
            annotation_scene=ann_scene,
            roi=annotation,
            subset=Subset.TRAINING,
            id_=dataset_item_id,
            metadata=metadata_items,
        )

    yield _build_item


class TestFeatureReconstructionError:
    def test_requirements(self) -> None:
        reqs: ScoringFunctionRequirements = FeatureReconstructionError.requirements
        assert not reqs.seen_dataset_with_predictions
        assert reqs.seen_dataset_with_annotations
        assert reqs.unseen_dataset_features
        assert reqs.seen_dataset_features

    def test_sampling(self, fxt_classification_label_factory, fxt_dataset_item_factory, fxt_ote_id) -> None:
        """
        Verify that FRE effectively ranks and samples items based on feature diversity.

        Scenario
         - Two classes A and B
         - Bi-dimensional feature space x-y (see the plot)
         - Each class is represented by 3 points in the training set (upper-case points)
         - Each class is returned by 2 predictions on unlabeled set (lower-case points)
         - Class A has most of its variance along the x-axis
         - Class B has most of its variance along the y-axis

        Expected
         - For class A, FRE assigns better score to predictions far from the x-axis
         - For class B, FRE assigns better score to predictions far from the y-axis

        . . . . . B . . . . .
        . . . . . + a . . . .
        . . . . . + . b . . .
        . . . . . + . . a . .
        . . . . . A . . . b .
        A + + + + 0 B + + + A
        . . . . . + . . . . .
        . . . . . + . . . . .
        . . . . . + . . . . .
        . . . . . + . . . . .
        . . . . . B . . . . .
        """
        # fmt: off
        label_A = fxt_classification_label_factory(1)
        label_B = fxt_classification_label_factory(2)
        seen_dataset_items_with_annotations = [
            fxt_dataset_item_factory(index=0, label=label_A, annotation_kind=AnnotationSceneKind.ANNOTATION),
            fxt_dataset_item_factory(index=1, label=label_A, annotation_kind=AnnotationSceneKind.ANNOTATION),
            fxt_dataset_item_factory(index=2, label=label_A, annotation_kind=AnnotationSceneKind.ANNOTATION),
            fxt_dataset_item_factory(index=3, label=label_B, annotation_kind=AnnotationSceneKind.ANNOTATION),
            fxt_dataset_item_factory(index=4, label=label_B, annotation_kind=AnnotationSceneKind.ANNOTATION),
            fxt_dataset_item_factory(index=5, label=label_B, annotation_kind=AnnotationSceneKind.ANNOTATION),
        ]
        unseen_dataset_items_with_predictions = [  # points ordered left-to-right, top-to-bottom
            fxt_dataset_item_factory(index=10, label=label_A, annotation_kind=AnnotationSceneKind.PREDICTION),
            fxt_dataset_item_factory(index=11, label=label_B, annotation_kind=AnnotationSceneKind.PREDICTION),
            fxt_dataset_item_factory(index=12, label=label_A, annotation_kind=AnnotationSceneKind.PREDICTION),
            fxt_dataset_item_factory(index=13, label=label_B, annotation_kind=AnnotationSceneKind.PREDICTION),
        ]
        Dataset(id=fxt_ote_id(1), items=seen_dataset_items_with_annotations)
        unseen_dataset_with_predictions = Dataset(
            id=fxt_ote_id(2), items=unseen_dataset_items_with_predictions
        )
        seen_dataset_features = np.array(
            [[-5, 0], [0, 0.1], [5, 0], [0, -5], [0.1, 0], [0, 5]]
        )
        unseen_dataset_features = np.array(
            [[1, 4], [2, 3], [3, 2], [4, 1]]
        )
        # fmt: on

        al_scores = FeatureReconstructionError.compute_scores(
            unseen_dataset_with_predictions=unseen_dataset_with_predictions,
            seen_dataset_items_with_predictions=(),
            seen_dataset_items_with_annotations=tuple(seen_dataset_items_with_annotations),
            unseen_dataset_features=unseen_dataset_features,
            seen_dataset_features=seen_dataset_features,
        )

        # Note: the scores are ordered as the points in unseen dataset
        assert np.array_equal(al_scores, np.array([0, 0.5, 0.5, 0], dtype=float))


class TestFeatureReconstructionErrorClassAgnostic:
    def test_requirements(self) -> None:
        reqs: ScoringFunctionRequirements = FeatureReconstructionErrorClassAgnostic.requirements
        assert not reqs.seen_dataset_with_predictions
        assert not reqs.seen_dataset_with_annotations
        assert reqs.unseen_dataset_features
        assert reqs.seen_dataset_features

    def test_sampling(self, fxt_dataset_item_factory) -> None:
        """
        Verify that FRE (class-agnostic) effectively ranks and samples items based
        on feature diversity.

        Scenario
         - Bi-dimensional feature space x-y (see the plot)
         - 3 points in the training set (upper-case points)
         - 5 predictions on the unlabeled set (lower-case points)
         - Most of the training set variance is along the x-axis

        Expected
         - FRE assigns better scores to predictions far from the x-axis

        . . . . . + a . . . .
        . . . a . + . . . . .
        . . . . . + . a . . .
        . a . . . + . . . . .
        . . . . . A . . . a .
        A + + + + 0 + + + + A
        . . . . . + . . . . .
        . . . . . + . . . . .
        . . . . . + . . . . .
        . . . . . + . . . . .
        . . . . . + . . . . .
        """
        seen_dataset_features = np.array([[-5, 0], [0, 0.1], [5, 0]])
        unseen_dataset_features = np.array([[-4, 2], [-2, 4], [1, 5], [2, 3], [4, 1]])

        al_scores = FeatureReconstructionErrorClassAgnostic.compute_scores(
            unseen_dataset_with_predictions=NullDataset(),
            seen_dataset_items_with_predictions=(),
            seen_dataset_items_with_annotations=(),
            unseen_dataset_features=unseen_dataset_features,
            seen_dataset_features=seen_dataset_features,
        )

        # Note: the scores are ordered as the points in unseen dataset feature space
        assert np.array_equal(al_scores, np.array([0.6, 0.2, 0, 0.4, 0.8], dtype=float))
