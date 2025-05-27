# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from typing import Any

from geti_configuration_tools.training_configuration import PartialTrainingConfiguration

from communication.controllers.utils import delete_none_from_dict, merge_deep_dict
from communication.exceptions import TaskNodeNotFoundException
from communication.views.training_configuration_rest_views import TrainingConfigurationRESTViews
from storage.repos.partial_training_configuration_repo import PartialTrainingConfigurationRepo

from geti_telemetry_tools import unified_tracing
from geti_types import ID, ProjectIdentifier
from iai_core.repos import TaskNodeRepo


class TrainingConfigurationRESTController:
    @classmethod
    @unified_tracing
    def get_configuration(
        cls,
        project_identifier: ProjectIdentifier,
        task_id: ID,
        model_manifest_id: str | None = None,
        model_id: ID | None = None,  # noqa: ARG003
    ) -> dict[str, Any]:
        """
        Retrieves training configuration.

        If model_id is provided, the configuration is loaded from the model entity.

        :param project_identifier: Identifier for the project (containing organization_id, workspace_id, and project_id)
        :param task_id: ID of the task to retrieve configuration for
        :param model_manifest_id: Optional ID of the model manifest to retrieve specific configurations
        :return: Dictionary representation of the training configuration
        :raises TaskNotFoundException: If the task does not exist
        """
        if not TaskNodeRepo(project_identifier).exists(task_id):
            raise TaskNodeNotFoundException(task_node_id=task_id)

        # TODO: if model_id is provided, load configuration from the model entity
        training_configuration_repo = PartialTrainingConfigurationRepo(project_identifier)
        training_config = training_configuration_repo.get_task_only_configuration(task_id)
        # Merge with algorithm level configuration if model_manifest_id is provided
        if model_manifest_id:
            algo_config = training_configuration_repo.get_by_model_manifest_id(model_manifest_id)
            training_config_dict = training_config.model_dump()
            algo_config_dict = delete_none_from_dict(algo_config.model_dump())
            complete_config_dict = merge_deep_dict(training_config_dict, algo_config_dict)
            complete_config_dict["id_"] = ""  # ID is required but is not relevant for the REST view
            training_config = PartialTrainingConfiguration.model_validate(complete_config_dict)
        return TrainingConfigurationRESTViews.training_configuration_to_rest(training_configuration=training_config)
