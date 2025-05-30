# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import pytest

from coordination.dataset_manager.missing_annotations_helper import MissingAnnotations
from entities.dataset_item_count import LabelData


@pytest.fixture
def fxt_missing_annotations(fxt_label):
    yield MissingAnnotations(
        total_missing_annotations_auto_training=10,
        missing_annotations_per_label={fxt_label.id_: 10},
        task_label_data=[LabelData.from_label(fxt_label)],
        n_new_annotations=5,
        total_missing_annotations_manual_training=3,
    )


@pytest.fixture
def fxt_missing_annotations_zero_missing(fxt_label):
    yield MissingAnnotations(
        total_missing_annotations_auto_training=0,
        total_missing_annotations_manual_training=0,
        missing_annotations_per_label={fxt_label.id_: 0},
        task_label_data=[LabelData.from_label(fxt_label)],
        n_new_annotations=5,
    )
