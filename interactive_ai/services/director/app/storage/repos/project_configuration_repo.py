# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from collections.abc import Callable, Sequence

from geti_configuration_tools.project_configuration import (
    AutoTrainingParameters,
    NullProjectConfiguration,
    ProjectConfiguration,
    TaskConfig,
    TrainConstraints,
    TrainingParameters,
)
from pymongo.command_cursor import CommandCursor
from pymongo.cursor import Cursor

from storage.mappers.project_configuration_mapper import ProjectConfigurationToMongo

from geti_types import ID, ProjectIdentifier, Session
from iai_core.repos.base import ProjectBasedSessionRepo
from iai_core.repos.mappers.cursor_iterator import CursorIterator


class ProjectConfigurationRepo(ProjectBasedSessionRepo[ProjectConfiguration]):
    """
    Repository to persist ProjectConfiguration entities in the database.

    :param project_identifier: Identifier of the project
    :param session: Session object; if not provided, it is loaded through the context variable CTX_SESSION_VAR
    """

    def __init__(self, project_identifier: ProjectIdentifier, session: Session | None = None) -> None:
        super().__init__(
            collection_name="project_configuration",
            session=session,
            project_identifier=project_identifier,
        )

    @property
    def forward_map(self) -> Callable[[ProjectConfiguration], dict]:
        return ProjectConfigurationToMongo.forward

    @property
    def backward_map(self) -> Callable[[dict], ProjectConfiguration]:
        return ProjectConfigurationToMongo.backward

    @property
    def null_object(self) -> NullProjectConfiguration:
        return NullProjectConfiguration()

    @property
    def cursor_wrapper(self) -> Callable[[Cursor | CommandCursor], CursorIterator]:
        return lambda mongo_cursor: CursorIterator(
            cursor=mongo_cursor, mapper=ProjectConfigurationToMongo, parameter=None
        )

    def get_project_configuration(self) -> ProjectConfiguration:
        """
        Gets the project configuration for the current project.

        This is an alias for get_one() since each project has exactly one
        configuration entity with an ID matching the project ID.

        :return: The ProjectConfiguration for this project
        """
        return self.get_one()

    def update_task_config(self, task_config: TaskConfig) -> None:
        """
        Update a task configuration in the project.

        :param task_config: task configuration to be updated
        :raises ValueError: if the task to update is not found
        """
        project_config = self.get_project_configuration()
        if project_config is None:
            raise ValueError(f"Project configuration with ID {task_config.id_} not found.")

        project_config.update_task_config(task_config=task_config)
        self.save(project_config)

    def create_default_configuration(self, task_ids: Sequence[ID]) -> None:
        """
        Create a default project configuration if one doesn't already exist.

        This method checks if a project configuration already exists and creates
        a new configuration with default parameters for the provided task IDs
        only if no configuration is found.

        :param task_ids: Sequence of task IDs to include in the default configuration
        :return: None
        """
        exists = not isinstance(self.get_project_configuration(), NullProjectConfiguration)
        if exists:
            return

        default_task_configs = []

        for task_id in task_ids:
            default_task_configs.append(
                TaskConfig(
                    task_id=task_id,
                    training=TrainingParameters(
                        constraints=TrainConstraints(),
                    ),
                    auto_training=AutoTrainingParameters(),
                )
            )

        default_config = ProjectConfiguration(
            id_=self.generate_id(),
            project_id=self.identifier.project_id,
            task_configs=default_task_configs,
        )
        self.save(default_config)
