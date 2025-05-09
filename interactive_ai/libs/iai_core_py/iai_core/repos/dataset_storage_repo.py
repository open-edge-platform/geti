# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""Repository for dataset storage entities"""

from collections.abc import Callable

from pymongo.command_cursor import CommandCursor
from pymongo.cursor import Cursor

from iai_core.entities.dataset_storage import DatasetStorage, NullDatasetStorage
from iai_core.repos.base import ProjectBasedSessionRepo
from iai_core.repos.mappers.cursor_iterator import CursorIterator
from iai_core.repos.mappers.mongodb_mappers.dataset_storage_mapper import DatasetStorageToMongo

from geti_types import ProjectIdentifier, Session


class DatasetStorageRepo(ProjectBasedSessionRepo[DatasetStorage]):
    """
    Repository to persist DatasetStorage entities in the database.

    :param project_identifier: Identifier of the project
    :param session: Session object; if not provided, it is loaded through the context variable CTX_SESSION_VAR
    """

    def __init__(self, project_identifier: ProjectIdentifier, session: Session | None = None) -> None:
        super().__init__(
            collection_name="dataset_storage",
            session=session,
            project_identifier=project_identifier,
        )

    @property
    def forward_map(self) -> Callable[[DatasetStorage], dict]:
        return DatasetStorageToMongo.forward

    @property
    def backward_map(self) -> Callable[[dict], DatasetStorage]:
        return DatasetStorageToMongo.backward

    @property
    def null_object(self) -> NullDatasetStorage:
        return NullDatasetStorage()

    @property
    def cursor_wrapper(self) -> Callable[[Cursor | CommandCursor], CursorIterator]:
        return lambda mongo_cursor: CursorIterator(
            cursor=mongo_cursor,
            mapper=DatasetStorageToMongo,
            parameter=None,
        )
