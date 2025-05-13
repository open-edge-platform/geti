# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""This module implements the CompiledDatasetShard entity"""

from collections.abc import Sequence
from dataclasses import dataclass
from enum import IntEnum

from iai_core.entities.persistent_entity import PersistentEntity
from iai_core.utils.constants import DEFAULT_USER_NAME

from geti_types import ID


class CompiledDatasetShardsDeleteFlag(IntEnum):
    """Enum class to indicate shard file deletion after download"""

    DO_NOT_DELETE = 0
    DELETE_AFTER_DOWNLOAD = 1


@dataclass(eq=True, frozen=True)
class CompiledDatasetShard:
    """
    A meta info object for the compiled dataset shard file which is stored in BinaryRepo.

    :param filename: Name of the file
    :param binary_filename: Filename of the binary file, which will be used for its access on the BinaryRepo
    :param size: Size of the file (the number of bytes)
    :param checksum: SHA-256 checksum of the file which will be used for the integrity check
    """

    filename: str
    binary_filename: str
    size: int
    checksum: str


class CompiledDatasetShards(PersistentEntity):
    """
    A meta info object for the compiled dataset shard files built from Dataset.
    This entity is created when `Dataset` is converted to dataset shard files (.arrow binary format).
    It includes filenames of the shard files uploaded to BinaryRepo, the ID of source dataset,
    the ID of source label schema, and the creator name and creation date.
    It is used to serve the dataset shard files to the client (e.g., training workload, batch inference workload, ...)
    by providing pre-signed urls of them.

    :param dataset_id: ID of the source dataset from which the shard files were compiled. It also a id
    :param label_schema_id: ID of the label schema from which the shard files were compiled.
    :param compiled_shard_files: A list of compiled shard file infos.
    :param creator_name: Name of the one that compiled shard files
    :param ephemeral: Boolean to mark whether it has been persisted in the database or not
    """

    def __init__(
        self,
        dataset_id: ID,
        label_schema_id: ID,
        compiled_shard_files: Sequence[CompiledDatasetShard],
        creator_name: str | None = None,
        ephemeral: bool = True,
    ) -> None:
        super().__init__(id_=dataset_id, ephemeral=ephemeral)
        self.label_schema_id = label_schema_id
        self.compiled_shard_files = compiled_shard_files
        self.creator_name = creator_name if creator_name is not None else DEFAULT_USER_NAME

    def __len__(self) -> int:
        return len(self.compiled_shard_files)

    def __repr__(self) -> str:
        return (
            f"CompiledDatasetShards(dataset_id={self.dataset_id}, "
            f"label_schema_id={self.label_schema_id}, "
            f"num_compiled_shard_files={len(self)})"
        )

    def __hash__(self):
        return hash(str(self))

    @property
    def dataset_id(self) -> ID:
        return self.id_

    @property
    def total_size(self) -> int:
        """Total size of shard files (bytes)"""
        return sum(file.size for file in self.compiled_shard_files)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, CompiledDatasetShards):
            return (
                self.id_ == other.id_
                and self.label_schema_id == other.label_schema_id
                and self.compiled_shard_files == other.compiled_shard_files
                and self.creator_name == other.creator_name
            )
        return False


class NullCompiledDatasetShards(CompiledDatasetShards):
    """Representation of a 'compiled dataset shard not found'"""

    def __init__(self) -> None:
        super().__init__(
            dataset_id=ID(),
            label_schema_id=ID(),
            compiled_shard_files=[],
            creator_name="",
            ephemeral=False,
        )

    def __repr__(self) -> str:
        return "NullCompiledDatasetShards()"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, NullCompiledDatasetShards)
