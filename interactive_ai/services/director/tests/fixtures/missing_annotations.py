# INTEL CONFIDENTIAL
#
# Copyright (C) 2022 Intel Corporation
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
