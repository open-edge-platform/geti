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


from entities.dataset_item_count import DeletedDatasetItemCountData, NewDatasetItemCountData
from storage.repos import DatasetItemCountRepo


class TestDatasetItemCountRepo:
    def test_update_count_data(self, request, fxt_dataset_storage, fxt_ote_id, fxt_empty_dataset_item_count) -> None:
        # Arrange
        repo = DatasetItemCountRepo(dataset_storage_identifier=fxt_dataset_storage.identifier)
        request.addfinalizer(lambda: repo.delete_by_id(fxt_empty_dataset_item_count.id_))
        labels = [fxt_ote_id(1), fxt_ote_id(2)]
        new_dataset_item_ids = [fxt_ote_id(10), fxt_ote_id(11)]
        deleted_dataset_item_ids = [fxt_ote_id(100)]
        assigned_dataset_item_ids = [fxt_ote_id(1000)]
        fxt_empty_dataset_item_count.n_dataset_items = 5
        fxt_empty_dataset_item_count.n_items_per_label = {labels[0]: 4, labels[1]: 1}
        fxt_empty_dataset_item_count.unassigned_dataset_items = deleted_dataset_item_ids + assigned_dataset_item_ids
        repo.save(fxt_empty_dataset_item_count)
        new_dataset_item_count_data = NewDatasetItemCountData(
            count=1,
            dataset_item_ids=new_dataset_item_ids,
            per_label_count={labels[1]: 1},  # Add label_1 once
        )
        deleted_dataset_item_count_data = DeletedDatasetItemCountData(
            count=2,
            dataset_item_ids=deleted_dataset_item_ids,
            per_label_count={labels[0]: 2},  # Delete label_0 twice
        )

        # Act
        repo.update_count_data(
            id_=fxt_empty_dataset_item_count.id_,
            new_dataset_item_count_data=new_dataset_item_count_data,
            deleted_dataset_item_count_data=deleted_dataset_item_count_data,
            assigned_dataset_items=assigned_dataset_item_ids,
        )

        # Assert
        update_ds_item_counter = repo.get_by_id(fxt_empty_dataset_item_count.id_)
        assert update_ds_item_counter.n_dataset_items == 4
        assert update_ds_item_counter.n_items_per_label == {labels[0]: 2, labels[1]: 2}
        assert update_ds_item_counter.n_dataset_items == sum(update_ds_item_counter.n_items_per_label.values())
        assert update_ds_item_counter.unassigned_dataset_items == new_dataset_item_ids
