# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from collections.abc import Callable

from geti_configuration_tools.training_configuration import NullTrainingConfiguration, PartialTrainingConfiguration
from pymongo import DESCENDING, IndexModel
from pymongo.command_cursor import CommandCursor
from pymongo.cursor import Cursor

from storage.mappers.partial_training_configuration_mapper import PartialTrainingConfigurationToMongo

from geti_types import ID, ProjectIdentifier, Session
from iai_core.repos.base import ProjectBasedSessionRepo
from iai_core.repos.mappers import IDToMongo
from iai_core.repos.mappers.cursor_iterator import CursorIterator


class PartialTrainingConfigurationRepo(ProjectBasedSessionRepo[PartialTrainingConfiguration]):
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
    def forward_map(self) -> Callable[[PartialTrainingConfiguration], dict]:
        return PartialTrainingConfigurationToMongo.forward

    @property
    def backward_map(self) -> Callable[[dict], PartialTrainingConfiguration]:
        return PartialTrainingConfigurationToMongo.backward

    @property
    def null_object(self) -> NullTrainingConfiguration:
        return NullTrainingConfiguration()

    @property
    def cursor_wrapper(self) -> Callable[[Cursor | CommandCursor], CursorIterator]:
        return lambda mongo_cursor: CursorIterator(
            cursor=mongo_cursor, mapper=PartialTrainingConfigurationToMongo, parameter=None
        )

    def get_task_only_configuration(self, task_id: ID) -> PartialTrainingConfiguration:
        """
        Get a partial training configuration that is only applied to the specified task ID.
        This returns task-level configuration that does not have an associated model manifest ID.

        :param task_id: The task ID to search for.
        :return: A partial training configuration object if found, otherwise NullTrainingConfiguration.
        """
        task_filter = {"task_id": IDToMongo.forward(instance=task_id), "model_manifest_id": {"$exists": False}}
        return self.get_one(extra_filter=task_filter)

    def get_by_model_manifest_id(self, model_manifest_id: str) -> PartialTrainingConfiguration:
        """
        Get a TrainingConfiguration by model manifest ID.

        :param model_manifest_id: The model manifest ID to search for.
        :return: The TrainingConfiguration object if found, otherwise NullTrainingConfiguration.
        """
        manifest_filter = {"model_manifest_id": model_manifest_id}
        return self.get_one(extra_filter=manifest_filter)
