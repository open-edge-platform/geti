# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from typing import Any

from geti_configuration_tools.training_configuration import NullTrainingConfiguration, PartialTrainingConfiguration

from communication.exceptions import MissingTaskIDException, TaskNodeNotFoundException
from communication.views.training_configuration_rest_views import TrainingConfigurationRESTViews
from service.configuration_service import ConfigurationService
from storage.repos.partial_training_configuration_repo import PartialTrainingConfigurationRepo

from geti_telemetry_tools import unified_tracing
from geti_types import ID, ProjectIdentifier
from iai_core.repos import TaskNodeRepo


class TrainingConfigurationRESTController:
    @staticmethod
    @unified_tracing
    def get_configuration(
        project_identifier: ProjectIdentifier,
        task_id: ID | None = None,
        model_manifest_id: str | None = None,
        model_id: ID | None = None,
    ) -> dict[str, Any]:
        """
        Retrieves training configuration.

        If model_id is provided, the configuration is loaded from the model entity.

        :param project_identifier: Identifier for the project (containing organization_id, workspace_id, and project_id)
        :param task_id: ID of the task to retrieve configuration for
        :param model_manifest_id: Optional ID of the model manifest to retrieve specific configurations
        :param model_id: Optional ID of the model to retrieve specific configurations
        :return: Dictionary representation of the training configuration
        :raises TaskNotFoundException: If the task does not exist
        """
        # task_id can be None if the project is single-task
        if task_id is None:
            task_ids = list(TaskNodeRepo(project_identifier).get_trainable_task_ids())
            if len(task_ids) != 1:
                raise MissingTaskIDException
            task_id = task_ids[0]

        if not TaskNodeRepo(project_identifier).exists(task_id):
            raise TaskNodeNotFoundException(task_node_id=task_id)

        if model_id is not None:
            # TODO ITEP-68215: if model_id is provided, load configuration from the model entity
            pass

        if model_manifest_id is None:
            training_configuration_repo = PartialTrainingConfigurationRepo(project_identifier)
            task_level_config = training_configuration_repo.get_task_only_configuration(task_id)
            # Only task level configuration can be retrieved
            return TrainingConfigurationRESTViews.training_configuration_to_rest(
                training_configuration=task_level_config
            )

        # If model_manifest_id is available, the full configuration can be built
        full_config = ConfigurationService.get_full_training_configuration(
            project_identifier=project_identifier,
            task_id=task_id,
            model_manifest_id=model_manifest_id,
        )
        return TrainingConfigurationRESTViews.training_configuration_to_rest(training_configuration=full_config)

    @classmethod
    @unified_tracing
    def update_configuration(
        cls,
        project_identifier: ProjectIdentifier,
        update_configuration: PartialTrainingConfiguration,
    ) -> None:
        """
        Updates a training configuration.

        This method handles both task-level and algorithm-level configurations:
        - Task-level: Applied to all model architectures for a given task. Used when
          model_manifest_id is not provided in the update_configuration.
        - Algorithm-level: Specific to a particular model architecture. Applied on top
          of task-level configuration and overwrites any conflicting parameters. Used
          when model_manifest_id is provided.

        :param project_identifier: Identifier for the project
        :param update_configuration: The configuration to update with
        :raises TaskNotFoundException: If the specified task does not exist
        """
        training_configuration_repo = PartialTrainingConfigurationRepo(project_identifier)

        task_id = ID(update_configuration.task_id)
        if not TaskNodeRepo(project_identifier).exists(task_id):
            raise TaskNodeNotFoundException(task_node_id=task_id)

        # configuration is saved as "task level"
        if not update_configuration.model_manifest_id:
            task_config = training_configuration_repo.get_task_only_configuration(task_id)
            new_config = ConfigurationService.overlay_training_configurations(
                task_config, update_configuration, validate_full_config=False
            )
            training_configuration_repo.save(new_config)
            return

        # configuration is saved as "algorithm level"
        current_config = training_configuration_repo.get_by_model_manifest_id(
            model_manifest_id=update_configuration.model_manifest_id
        )
        if isinstance(current_config, NullTrainingConfiguration):
            # If the configuration does not exist, create a new one
            update_configuration.id_ = training_configuration_repo.generate_id()
            training_configuration_repo.save(update_configuration)
            return

        new_config = ConfigurationService.overlay_training_configurations(
            current_config,
            update_configuration,
            validate_full_config=False,
        )
        training_configuration_repo.save(new_config)
