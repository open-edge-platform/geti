# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""This module tests commands to create and save compiled dataset shard entities"""

from unittest.mock import MagicMock, patch

import pytest
from sc_sdk.entities.compiled_dataset_shards import CompiledDatasetShard

from jobs_common_extras.shard_dataset.commands.create_and_save_compiled_dataset_shards_command import (
    CreateAndSaveCompiledDatasetShardsCommand,
)


@pytest.mark.JobsComponent
class TestCreateAndSaveCompiledDatasetShardCommand:
    @patch(
        "jobs_common_extras.shard_dataset.commands.create_and_save_compiled_dataset_shards_command.CompiledDatasetShardsRepo"
    )
    def test_create_and_save_compiled_dataset_shards_command(self, mock_repo, fxt_mongo_id) -> None:
        # Arrange
        expected_id = dataset_id = fxt_mongo_id(2)
        mock_repo.generate_id.return_value = expected_id
        label_schema = MagicMock()
        dataset_storage_identifier = MagicMock()
        compiled_shard_files = [
            CompiledDatasetShard(
                filename="dummy.arrow",
                binary_filename="dummy.arrow",
                size=10,
                checksum="031edd7d41651593c5fe5c006fa5752b37fddff7bc4e843aa6af0c950f4b9406",
            )
        ]

        # Act
        command = CreateAndSaveCompiledDatasetShardsCommand(
            dataset_id=dataset_id,
            label_schema=label_schema,
            compiled_shard_files=compiled_shard_files,
            dataset_storage_identifier=dataset_storage_identifier,
        )

        command.execute()

        # Assert
        mock_repo.return_value.save.assert_called_once()
        actual_id = command.compiled_dataset_shards_id
        assert actual_id == expected_id
