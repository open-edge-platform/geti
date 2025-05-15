# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from typing import Any

from geti_configuration_tools.project_configuration import NullProjectConfiguration
from geti_fastapi_tools.exceptions import ProjectNotFoundException
from geti_telemetry_tools import unified_tracing
from geti_types import ProjectIdentifier
from storage.repos.project_configuration_repo import ProjectConfigurationRepo


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
            raise ProjectNotFoundException(project_identifier.project_id)
        # The project configuration is a Pydantic model, so we can simply convert it to a dict
        return project_config.model_dump()
