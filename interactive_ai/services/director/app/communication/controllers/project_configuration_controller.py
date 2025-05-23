# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from typing import Any

from geti_configuration_tools.project_configuration import NullProjectConfiguration

from communication.exceptions import ProjectConfigurationNotFoundException
from communication.views.project_configuration_rest_views import ProjectConfigurationRESTViews
from storage.repos.project_configuration_repo import ProjectConfigurationRepo

from geti_telemetry_tools import unified_tracing
from geti_types import ProjectIdentifier


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
