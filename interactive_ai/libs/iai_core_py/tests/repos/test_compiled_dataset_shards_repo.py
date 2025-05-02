# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from testfixtures import compare

from iai_core.entities.compiled_dataset_shards import (
    CompiledDatasetShard,
    CompiledDatasetShards,
    NullCompiledDatasetShards,
)
from iai_core.repos import CompiledDatasetShardsRepo

from geti_types import ID, DatasetStorageIdentifier


class TestCompiledDatasetShardsRepo:
    idx = 0

    @classmethod
    def _create_item(cls, dataset_id: ID, label_schema_id: ID) -> CompiledDatasetShards:
        cls.idx += 1
        return CompiledDatasetShards(
            dataset_id=CompiledDatasetShardsRepo.generate_id(),
            label_schema_id=label_schema_id,
            compiled_shard_files=[
                CompiledDatasetShard(
                    filename=f"dummy_file_{i}.arrow",
                    binary_filename=f"dummy_file_{i}.arrow",
                    size=i,
                    checksum=f"checksum_{i}",
                )
                for i in range(cls.idx)
            ],
            creator_name=f"anonymous_{cls.idx}",
        )

    def test_compiled_dataset_shards_repo(self, fxt_empty_project, fxt_dataset_storage, request) -> None:
        """
        <b>Description:</b>
        Check that CompiledDatasetShardsRepo can be created and data saved/loaded to/from it
        without being modified during the process. Also check if metadata can
        be removed from the repo.

        <b>Input data:</b>
        Two CompiledDatasetShards

        <b>Expected results:</b>
        Reloading CompiledDatasetShards from the repo returns the same information previously stored.
        Also, after deletion, the CompiledDatasetShards is no longer accessible in the repo.

        <b>Steps</b>
        1. Create a CompiledDatasetShardsRepo
        2. Create and save a couple CompiledDatasetShards to the repo
        3. Reload one item from the repo and verify that it matches the original one
        4. Reload both items and check that they match the original ones, respectively
        5. Delete the item from the repo
        6. Verify that it's no longer possible to reload such CompiledDatasetShards item,
            while the other one remains accessible
        """
        dataset_storage_identifier = DatasetStorageIdentifier(
            workspace_id=fxt_empty_project.workspace_id,
            project_id=fxt_empty_project.id_,
            dataset_storage_id=fxt_dataset_storage.id_,
        )
        repo = CompiledDatasetShardsRepo(dataset_storage_identifier)

        item_1 = self._create_item(dataset_id=repo.generate_id(), label_schema_id=repo.generate_id())
        item_2 = self._create_item(dataset_id=repo.generate_id(), label_schema_id=repo.generate_id())
        repo.save(item_1)
        repo.save(item_2)

        request.addfinalizer(lambda: repo.delete_by_id(item_2.id_))

        loaded_item_1 = repo.get_by_id(item_1.id_)
        compare(loaded_item_1, item_1)

        repo.delete_by_id(item_1.id_)
        loaded_item_1 = repo.get_by_id(item_1.id_)
        loaded_item_2 = repo.get_by_id(item_2.id_)
        assert isinstance(loaded_item_1, NullCompiledDatasetShards)
        assert not isinstance(loaded_item_2, NullCompiledDatasetShards)

    def test_get_by_dataset_and_label_schema_ids(self, fxt_empty_project, fxt_dataset_storage, request) -> None:
        """
        <b>Description:</b>
        Check that CompiledDatasetShardsRepo can retrieve CompiledDatasetShards items
        for the given dataset_id and label_schema_id.

        <b>Input data:</b>
        Two CompiledDatasetShards have different dataset_id and label_schema_id.

        <b>Expected results:</b>
        A list of one CompiledDatasetShards respectively for both inputs, and an empty list

        <b>Steps</b>
        1. Create a CompiledDatasetShardsRepo
        2. Create and save two different CompiledDatasetShards to the repo
        3. Reload each item by giving different dataset_id and label_schema_id
        4. Obtain a empty list since we give invalid dataset_id and label_schema_id
        """
        dataset_storage_identifier = DatasetStorageIdentifier(
            workspace_id=fxt_empty_project.workspace_id,
            project_id=fxt_empty_project.id_,
            dataset_storage_id=fxt_dataset_storage.id_,
        )
        repo = CompiledDatasetShardsRepo(dataset_storage_identifier)

        item_1 = self._create_item(repo.generate_id(), repo.generate_id())
        item_2 = self._create_item(repo.generate_id(), repo.generate_id())

        request.addfinalizer(lambda: repo.delete_by_id(item_1.id_))
        request.addfinalizer(lambda: repo.delete_by_id(item_2.id_))

        repo.save(item_1)
        repo.save(item_2)

        loaded_items = repo.get_by_dataset_and_label_schema_ids(
            dataset_id=item_1.dataset_id,
            label_schema_id=item_1.label_schema_id,
        )
        compare(loaded_items, [item_1])

        loaded_items = repo.get_by_dataset_and_label_schema_ids(
            dataset_id=item_2.dataset_id,
            label_schema_id=item_2.label_schema_id,
        )
        compare(loaded_items, [item_2])

        loaded_items = repo.get_by_dataset_and_label_schema_ids(
            dataset_id=repo.generate_id(),
            label_schema_id=repo.generate_id(),
        )
        compare(loaded_items, [])
