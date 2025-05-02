# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module defines commands to create and save CompiledDatasetShard entity to the repo"""

import logging

from geti_telemetry_tools import unified_tracing
from geti_types import ID, DatasetStorageIdentifier
from iai_core.entities.compiled_dataset_shards import CompiledDatasetShard, CompiledDatasetShards
from iai_core.entities.label_schema import LabelSchema
from iai_core.repos import CompiledDatasetShardsRepo

from jobs_common.commands.interfaces.command import ICommand
from jobs_common.exceptions import DataShardCreationFailedException

logger = logging.getLogger(__name__)


class CreateAndSaveCompiledDatasetShardsCommand(ICommand):
    """
    Command to create and save CompiledDatasetShards entity

    :param dataset_id: ID of the source dataset
    :param label_schema: label schema to use for the task
    :param urls: URLs of shard files in BinaryRepo
    :param workspace: Workspace required to access to CompiledDatasetShardRepo
    """

    def __init__(
        self,
        dataset_id: str,
        label_schema: LabelSchema,
        compiled_shard_files: list[CompiledDatasetShard],
        dataset_storage_identifier: DatasetStorageIdentifier,
    ) -> None:
        super().__init__()
        self.dataset_id = dataset_id
        self.label_schema = label_schema
        self.compiled_shard_files = compiled_shard_files
        self.dataset_storage_identifier = dataset_storage_identifier
        self._compiled_dataset_shards_id: str | None = None

    @unified_tracing
    def execute(self) -> None:
        """
        Create and save CompiledDatasetShard entity to CompiledDatasetShardRepo

        :raises DataShardCreationFailedException: If any error happens during the execution
        """
        try:
            if self._compiled_dataset_shards_id is not None:
                raise RuntimeError("It should call execute() just one time.")

            instance = CompiledDatasetShards(
                dataset_id=ID(self.dataset_id),
                label_schema_id=ID(self.label_schema.id_),
                compiled_shard_files=self.compiled_shard_files,
            )
            repo: CompiledDatasetShardsRepo = CompiledDatasetShardsRepo(
                dataset_storage_identifier=self.dataset_storage_identifier
            )
            repo.save(instance)
            logger.info(
                f"[Command {self.id_}] Created CompiledDatasetShard[id={instance.id_}] "
                f"for Dataset[id={self.dataset_id}]"
            )
            self._compiled_dataset_shards_id = str(instance.id_)

        except Exception as exc:
            logger.exception(f"Could not create CompiledDatasetShard for Dataset[id={self.dataset_id}]")
            raise DataShardCreationFailedException from exc

    @property
    def compiled_dataset_shards_id(self) -> str:
        """Return ID of the created and saved CompiledDatasetShard

        :return: ID of the created and saved CompiledDatasetShard
        """
        if self._compiled_dataset_shards_id is None:
            raise RuntimeError("You should execute() first.")

        return self._compiled_dataset_shards_id
