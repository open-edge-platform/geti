# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""This module implements the repository for compiled dataset entities"""

from collections.abc import Callable, Iterator

from pymongo.command_cursor import CommandCursor
from pymongo.cursor import Cursor

from sc_sdk.entities.compiled_dataset_shards import CompiledDatasetShards, NullCompiledDatasetShards
from sc_sdk.repos.base import DatasetStorageBasedSessionRepo
from sc_sdk.repos.mappers.cursor_iterator import CursorIterator
from sc_sdk.repos.mappers.mongodb_mappers.compiled_dataset_shards_mapper import CompiledDatasetShardsToMongo
from sc_sdk.repos.mappers.mongodb_mappers.id_mapper import IDToMongo

from geti_types import ID, DatasetStorageIdentifier, Session


class CompiledDatasetShardsRepo(DatasetStorageBasedSessionRepo[CompiledDatasetShards]):
    """
    Repository to persist CompiledDatasetShards entities in the database.

    :param dataset_storage_identifier: Identifier of the dataset_storage
    :param session: Session object; if not provided, it is loaded through the context variable CTX_SESSION_VAR
    """

    def __init__(
        self,
        dataset_storage_identifier: DatasetStorageIdentifier,
        session: Session | None = None,
    ) -> None:
        super().__init__(
            collection_name="compiled_dataset_shard",
            session=session,
            dataset_storage_identifier=dataset_storage_identifier,
        )

    @property
    def forward_map(self) -> Callable[[CompiledDatasetShards], dict]:
        return CompiledDatasetShardsToMongo.forward

    @property
    def backward_map(self) -> Callable[[dict], CompiledDatasetShards]:
        return CompiledDatasetShardsToMongo.backward

    @property
    def null_object(self) -> NullCompiledDatasetShards:
        return NullCompiledDatasetShards()

    @property
    def cursor_wrapper(self) -> Callable[[Cursor | CommandCursor], CursorIterator]:
        return lambda mongo_cursor: CursorIterator(
            cursor=mongo_cursor, mapper=CompiledDatasetShardsToMongo, parameter=None
        )

    def get_by_dataset_and_label_schema_ids(
        self, dataset_id: ID, label_schema_id: ID
    ) -> Iterator[CompiledDatasetShards]:
        """
        Get all compiled dataset shards with the given dataset id and label schema id.

        :param dataset_id: ID of dataset
        :param label_schema_id: ID of label schema
        :return: Iterator of CompiledDatasetShards
        """
        if dataset_id == ID():
            raise ValueError("Dataset ID cannot be null")

        if label_schema_id == ID():
            raise ValueError("Label schema ID cannot be null")

        query = {
            "_id": IDToMongo.forward(dataset_id),
            "label_schema_id": IDToMongo.forward(label_schema_id),
        }

        return self.get_all(extra_filter=query)
