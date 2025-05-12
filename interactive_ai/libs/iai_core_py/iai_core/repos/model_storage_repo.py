# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""Repository for model storage entities"""

from collections.abc import Callable

from pymongo import DESCENDING, IndexModel
from pymongo.command_cursor import CommandCursor
from pymongo.cursor import Cursor

from iai_core.entities.model_storage import ModelStorage, NullModelStorage
from iai_core.repos.base import ProjectBasedSessionRepo
from iai_core.repos.mappers.cursor_iterator import CursorIterator
from iai_core.repos.mappers.mongodb_mappers.id_mapper import IDToMongo
from iai_core.repos.mappers.mongodb_mappers.model_storage_mapper import ModelStorageToMongo

from geti_types import ID, ProjectIdentifier, Session


class ModelStorageRepo(ProjectBasedSessionRepo[ModelStorage]):
    """
    Repository to persist ModelStorage entities in the database.

    :param project_identifier: Identifier of the project
    :param session: Session object; if not provided, it is loaded through the context variable CTX_SESSION_VAR
    """

    collection_name = "model_storage"

    def __init__(self, project_identifier: ProjectIdentifier, session: Session | None = None) -> None:
        super().__init__(
            collection_name=ModelStorageRepo.collection_name,
            session=session,
            project_identifier=project_identifier,
        )

    @property
    def forward_map(self) -> Callable[[ModelStorage], dict]:
        return ModelStorageToMongo.forward

    @property
    def backward_map(self) -> Callable[[dict], ModelStorage]:
        return ModelStorageToMongo.backward

    @property
    def null_object(self) -> NullModelStorage:
        return NullModelStorage()

    @property
    def cursor_wrapper(self) -> Callable[[Cursor | CommandCursor], CursorIterator]:
        return lambda mongo_cursor: CursorIterator(
            cursor=mongo_cursor,
            mapper=ModelStorageToMongo,
            parameter=None,
        )

    @property
    def indexes(self) -> list[IndexModel]:
        super_indexes = super().indexes
        new_indexes = [
            IndexModel([("task_node_id", DESCENDING)]),
            # Index on model_template_id needed to filter out dataset and crop tasks
            IndexModel([("model_template_id", DESCENDING)]),
        ]
        return super_indexes + new_indexes

    def get_by_task_node_id(self, task_node_id: ID) -> CursorIterator[ModelStorage]:
        """
        Get all the model storage for a task node.

        :param task_node_id: ID of the task node for which to list all model storages.
        :return: List of model storages.
        """
        task_node_filter = {"task_node_id": IDToMongo.forward(instance=task_node_id)}
        return self.get_all(extra_filter=task_node_filter)

    def get_one_by_task_node_id(self, task_node_id: ID, extra_filter: dict | None = None) -> ModelStorage:
        """
        Get a model storage for a task node.

        :param task_node_id: ID of the task node for which to get a model storage.
        :param extra_filter: Optional filter to apply in addition to the default one.
        :return: model storage.
        """
        task_node_filter = {"task_node_id": IDToMongo.forward(instance=task_node_id), **(extra_filter or {})}
        return self.get_one(extra_filter=task_node_filter)
