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

from entities.dataset_item_count import DatasetItemCount, LabelData


@pytest.fixture
def fxt_empty_dataset_item_count(fxt_mongo_id, fxt_label, fxt_dataset_item):
    return DatasetItemCount(
        task_node_id=fxt_mongo_id(),
        n_dataset_items=0,
        task_label_data=[LabelData.from_label(fxt_label)],
        n_items_per_label={fxt_label.id_: 0},
        unassigned_dataset_items=[],
    )


@pytest.fixture
def fxt_empty_anomaly_dataset_item_count(fxt_mongo_id, fxt_label, fxt_anomalous_label, fxt_dataset_item):
    fxt_label.id_ = fxt_mongo_id(0)
    fxt_anomalous_label.id_ = fxt_mongo_id(1)
    return DatasetItemCount(
        task_node_id=fxt_mongo_id(),
        n_dataset_items=0,
        task_label_data=[
            LabelData.from_label(fxt_label),
            LabelData.from_label(fxt_anomalous_label),
        ],
        n_items_per_label={fxt_label.id_: 0, fxt_anomalous_label.id_: 0},
        unassigned_dataset_items=[],
    )
