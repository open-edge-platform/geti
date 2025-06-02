# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from typing import Any

from geti_configuration_tools.project_configuration import (
    NullProjectConfiguration,
    PartialProjectConfiguration,
    TaskConfig,
)

from communication.controllers.utils import delete_none_from_dict, merge_deep_dict
from communication.exceptions import ProjectConfigurationNotFoundException
from communication.views.project_configuration_rest_views import ProjectConfigurationRESTViews
from storage.repos.project_configuration_repo import ProjectConfigurationRepo

from geti_telemetry_tools import unified_tracing
from geti_types import ID, ProjectIdentifier


class ProjectConfigurationRESTController:
    @staticmethod
    @unified_tracing
    def get_configuration(
        project_identifier: ProjectIdentifier,
    ) -> dict[str, Any]:
        """
        Retrieves configuration related to a specific project.

        :param project_identifier: Identifier for the project (containing organization_id, workspace_id, and project_id)
        :return: Dictionary representation of the project configuration
        """
        project_config = ProjectConfigurationRepo(project_identifier).get_project_configuration()
        if isinstance(project_config, NullProjectConfiguration):
            raise ProjectConfigurationNotFoundException(project_identifier.project_id)
        return ProjectConfigurationRESTViews.project_configuration_to_rest(project_config)

    @staticmethod
    @unified_tracing
    def update_configuration(
        project_identifier: ProjectIdentifier,
        update_configuration: PartialProjectConfiguration,
    ) -> None:
        """
        Updates the configuration for a specific project.

        :param project_identifier: Identifier for the project (containing organization_id, workspace_id, and project_id)
        :param update_configuration: Dictionary representation of the new project configuration
        :return: Updated dictionary representation of the project configuration
        """
        if not update_configuration.task_configs:
            return

        repo = ProjectConfigurationRepo(project_identifier)
        current_config = repo.get_project_configuration()
        current_task_config_map = {task_config.task_id: task_config for task_config in current_config.task_configs}

        for task_config in update_configuration.task_configs:
            if task_config.task_id not in current_task_config_map:
                raise ProjectConfigurationNotFoundException(
                    project_id=project_identifier.project_id,
                    task_id=ID(task_config.task_id),
                )
            # Update existing task config
            current_task_config = current_task_config_map[task_config.task_id]
            updated_task_config_dict = delete_none_from_dict(task_config.model_dump())
            merged_task_config_dict = merge_deep_dict(current_task_config.model_dump(), updated_task_config_dict)
            current_task_config_map[task_config.task_id] = TaskConfig.model_validate(merged_task_config_dict)

        for _, task_config in current_task_config_map.items():
            repo.update_task_config(task_config)
