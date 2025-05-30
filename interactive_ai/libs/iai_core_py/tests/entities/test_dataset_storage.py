"""This module tests the DatasetStorage class"""

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from iai_core.entities.dataset_storage import DatasetStorage, NullDatasetStorage
from iai_core.repos import DatasetStorageRepo


class TestDatasetStorage:
    def test_datastorage_equality(self, fxt_ote_id) -> None:
        """
        <b>Description:</b>
        Check that DatasetStorage equality works correctly

        <b>Input data:</b>
        DatasetStorage instances

        <b>Expected results:</b>
        == and != operations work correctly for various inputs

        <b>Steps</b>
        1. Test DatasetStorage equality
        2. Test NullDatasetStorage equality
        """
        project_id = fxt_ote_id(1)
        ds1 = DatasetStorage(
            name="ds1",
            project_id=project_id,
            _id=DatasetStorageRepo.generate_id(),
            use_for_training=True,
        )
        ds1_clone = DatasetStorage(
            name="ds1_clone",
            project_id=ds1.id_,
            _id=ds1.id_,
            use_for_training=True,
        )
        ds2 = DatasetStorage(
            name="ds2",
            project_id=project_id,
            _id=DatasetStorageRepo.generate_id(),
            use_for_training=True,
        )

        assert ds1 == ds1_clone
        assert ds1 != ds2
        assert ds1 != NullDatasetStorage()
        assert NullDatasetStorage() == NullDatasetStorage()
