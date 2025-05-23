# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from collections.abc import Callable

from geti_configuration_tools.training_configuration import NullTrainingConfiguration, TrainingConfiguration
from pymongo import DESCENDING, IndexModel
from pymongo.command_cursor import CommandCursor
from pymongo.cursor import Cursor

from storage.mappers.training_configuration_mapper import TrainingConfigurationToMongo

from geti_types import ID, ProjectIdentifier, Session
from iai_core.repos.base import ProjectBasedSessionRepo
from iai_core.repos.mappers import IDToMongo
from iai_core.repos.mappers.cursor_iterator import CursorIterator


class TrainingConfigurationRepo(ProjectBasedSessionRepo[TrainingConfiguration]):
    """
    Repository to persist TrainingConfiguration entities in the database.

    :param project_identifier: Identifier of the project
    :param session: Session object; if not provided, it is loaded through the context variable CTX_SESSION_VAR
    """

    def __init__(self, project_identifier: ProjectIdentifier, session: Session | None = None) -> None:
        super().__init__(
            collection_name="training_configuration",
            session=session,
            project_identifier=project_identifier,
        )

    @property
    def indexes(self) -> list[IndexModel]:
        super_indexes = super().indexes
        new_indexes = [
            IndexModel([("task_id", DESCENDING)]),
            IndexModel([("model_manifest_id", DESCENDING)]),
        ]
        return super_indexes + new_indexes

    @property
    def forward_map(self) -> Callable[[TrainingConfiguration], dict]:
        return TrainingConfigurationToMongo.forward

    @property
    def backward_map(self) -> Callable[[dict], TrainingConfiguration]:
        return TrainingConfigurationToMongo.backward

    @property
    def null_object(self) -> NullTrainingConfiguration:
        return NullTrainingConfiguration()

    @property
    def cursor_wrapper(self) -> Callable[[Cursor | CommandCursor], CursorIterator]:
        return lambda mongo_cursor: CursorIterator(
            cursor=mongo_cursor, mapper=TrainingConfigurationToMongo, parameter=None
        )

    def get_by_task_id(self, task_id: ID) -> TrainingConfiguration:
        """
        Get a TrainingConfiguration by task ID only. This returns task-level configuration
        that does not have an associated model manifest ID.

        :param task_id: The task ID to search for.
        :return: The TrainingConfiguration object if found, otherwise NullTrainingConfiguration.
        """
        task_filter = {"task_id": IDToMongo.forward(instance=task_id), "model_manifest_id": {"$exists": False}}
        return self.get_one(extra_filter=task_filter)

    def get_by_model_manifest_id(self, model_manifest_id: str) -> TrainingConfiguration:
        """
        Get a TrainingConfiguration by model manifest ID.

        :param model_manifest_id: The model manifest ID to search for.
        :return: The TrainingConfiguration object if found, otherwise NullTrainingConfiguration.
        """
        manifest_filter = {"model_manifest_id": model_manifest_id}
        return self.get_one(extra_filter=manifest_filter)
