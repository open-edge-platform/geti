# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
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
