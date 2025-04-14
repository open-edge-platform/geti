# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
This module contains the ConfigurationValidator class, that is used to validate
configurable parameters related input to the POST REST endpoints for both the
director and resource microservice
"""

import logging
from typing import Any

from communication.exceptions import (
    ConfigurationMismatchException,
    ConfigurationNotFoundException,
    InvalidConfigurationException,
    TaskNotFoundException,
)

import sc_sdk.configuration.helper as otx_config_helper
from geti_fastapi_tools.exceptions import InvalidEntityIdentifierException
from geti_types import ID, ProjectIdentifier
from sc_sdk.configuration.elements.component_parameters import ComponentEntityIdentifier
from sc_sdk.configuration.elements.configurable_parameters import ConfigurableParameters
from sc_sdk.configuration.elements.entity_identifiers import EntityIdentifier, ModelEntityIdentifier
from sc_sdk.configuration.interfaces.configurable_parameters_interface import (
    IConfigurableParameterContainer,
    NullConfigurableParameterContainer,
)
from sc_sdk.entities.model_storage import ModelStorage
from sc_sdk.entities.project import Project
from sc_sdk.repos import ConfigurableParametersRepo, ModelStorageRepo, TaskNodeRepo

logger = logging.getLogger(__name__)
BE_VALIDATOR = logging.DEBUG
IO_VALIDATOR = logging.DEBUG


class ConfigurationValidator:
    """
    This class serves to validate configurable parameter input from any of the REST
    endpoints.

    It does not do schema validation (that is handled by the
    `ConfigurationRestValidator`), but instead validates that all relevant database ID's
    are correct, that the provided input values are within the specified parameter
    ranges/list of options, types of the input values are correct, etc.
    """

    @staticmethod
    def validate_and_update_config(
        input_config: dict[str, Any],
        entity_identifier: EntityIdentifier,
        project: Project,
        task_id: ID | None = None,
    ) -> IConfigurableParameterContainer[ConfigurableParameters]:
        """
        Validates that a dictionary `input_config` can be used for setting
        configurable parameters for the entity identified by `entity_identifier`.

        The following validation steps are performed:
         - Validates that the `entity_identifier` points to an entity (either model or
           component) within the `project`
         - Validates that the dictionary in `input_config` matches the structure of
           the configuration for the entity
         - Validates that all parameter values provided in `input_config` are of the
           proper type and within the allowed range/list of options for each parameter
           in the configuration for the entity

        Once all these validation steps pass, this method returns the updated
        configuration for the entity

        :param input_config: Dictionary holding the parameter values to be set. The
            dictionary structure should match the configuration structure for the entity
        :param entity_identifier: EntityIdentifier pointing to the entity for which to
            validate and update the configuration
        :param project: Project to which the entity belongs
        :param task_id: Optional task id to validate
        :raises: InvalidEntityIdentifierException if a model storage id is specified in
            the `entity_identifier` that does not belong to the project and task
        :raises TaskNotFoundException if the task_id passed in the keyword arguments or
            in the entity_identifier does not exist in the project
        :raises: ConfigurationMismatchException if the structure of the configuration
            in the request does not match the expected structure of the configurable
            parameters for the entity
        :raises: InvalidConfigurationException if an invalid value is attempted to be
            set for the configurable parameters
        :return: Validated configuration object, holding the updated values
        """
        ConfigurationValidator._validate_entity_identifier(
            entity_identifier=entity_identifier, project=project, task_id=task_id
        )
        return ConfigurationValidator._validate_and_update_config_values(
            input_config=input_config, entity_identifier=entity_identifier
        )

    @staticmethod
    def _validate_entity_identifier(
        entity_identifier: EntityIdentifier,
        project: Project,
        task_id: ID | None = None,
    ) -> None:
        """
        Validates that the `entity_identifier` provided points to an entity (can be
        a model or a component) within the `project`

        :param entity_identifier: EntityIdentifier to validate against
        :param project: the project to check
        :param task_id: Optional task ID to check
        :raises: InvalidEntityIdentifierException if a model storage id is specified in
            the `entity_identifier` that does not belong to the project and task
        :raises TaskNotFoundException if the task_id passed in the keyword arguments or
            in the entity_identifier does not exist in the project
        """
        project_identifier = project.identifier
        task_ids = [task.id_ for task in project.tasks]

        if isinstance(entity_identifier, ComponentEntityIdentifier):  # noqa: SIM102
            if entity_identifier.component.metadata.per_task:
                if task_id is None or task_id == ID():
                    task_id = entity_identifier.task_id if entity_identifier.task_id is not None else ID()
                if task_id not in task_ids:
                    raise TaskNotFoundException(task_id=task_id)

        if isinstance(entity_identifier, ModelEntityIdentifier):
            model_storage_id = entity_identifier.model_storage_id
            if task_id is not None:
                # Check that model storage in entity identifier belongs to the task
                task_model_storages = ConfigurationValidator.__get_model_storages_by_task_id(
                    project_identifier=project_identifier,
                    task_id=task_id,
                )
                task_model_storages_ids = [ms.id_ for ms in task_model_storages]
                if model_storage_id not in task_model_storages_ids:
                    raise InvalidEntityIdentifierException(
                        f"Model storage with id {model_storage_id} does not belong to task with id {task_id}"
                    )
            else:  # no task id specified
                # Check that the model storage exists within the project
                project_model_storages: list[ModelStorage] = []
                for task_node in project.get_trainable_task_nodes():
                    project_model_storages.extend(
                        ConfigurationValidator.__get_model_storages_by_task_id(
                            project_identifier=project_identifier, task_id=task_node.id_
                        )
                    )
                project_model_storages_ids = [ms.id_ for ms in project_model_storages]
                if model_storage_id not in project_model_storages_ids:
                    raise InvalidEntityIdentifierException(
                        f"Model storage with ID {model_storage_id} is not associated "
                        f"with any task of project {project}."
                    )

    @staticmethod
    def _validate_and_update_config_values(
        input_config: dict[str, Any], entity_identifier: EntityIdentifier
    ) -> IConfigurableParameterContainer[ConfigurableParameters]:
        """
        Validates that the dictionary in `input_config` matches the structure of
        the configuration expected by the entity with `entity_identifier`. If the
        input_config is valid, an updated configuration object will be returned.

        :param input_config: Dictionary holding configuration values, that should be
            validated
        :param entity_identifier: EntityIdentifier pointing to the entity for which
            the configuration data should be validated
        :raises: ConfigurationMismatchException if the structure of the configuration
            in the request does not match the expected structure of the configurable
            parameters for the entity
        :raises: InvalidConfigurationException if an invalid value is attempted to be
            set for the configurable parameters
        :return: Validated configuration object, holding the new values
        """
        latest_config = ConfigurationValidator._get_latest_config_by_entity_identifier(
            entity_identifier=entity_identifier
        )
        if latest_config.data is None:
            raise ConfigurationNotFoundException(
                f"There was an error retrieving the latest configurable parameter "
                f"data for the requested entity from the repository. "
                f"Entitiy Identifier: `{entity_identifier}`."
            )
        try:
            otx_config_helper.substitute_values(latest_config.data, input_config)
        except AttributeError as error:
            raise ConfigurationMismatchException(
                f"Unable to save configuration, the structure of the input dictionary "
                f"does not match the expected structure of the configuration: {error}"
            ) from error
        except (ValueError, TypeError) as validation_error:
            raise InvalidConfigurationException(
                f"An invalid value was attempted to be set for the configuration "
                f"for the entity: {entity_identifier}: {validation_error}"
            ) from validation_error
        return latest_config

    @staticmethod
    def _get_latest_config_by_entity_identifier(
        entity_identifier: EntityIdentifier,
    ) -> IConfigurableParameterContainer[ConfigurableParameters]:
        """
        Returns the latest configuration for the entity with `entity_identifier`, as
        well as the instance of the ConfigurableParametersRepo in which the
        configuration for the entity lives.

        NOTE: This method caches the configuration, because it should only used to
        validate configuration values on an incoming POST request. Even though
        configuration values may change, the structure and schema of the configuration
        does not change so it can be safely cached. This method should not be used to
        return the latest configuration for a GET request.

        :param entity_identifier: EntityIdentifier pointing to the entity to retrieve
            the configuration and repository for.
        :raises ConfigurationNotFoundException: If no configuration was found in the
            repository for the entity
        :return: Instance of IConfigurableParametersContainer holding the latest
                configurable parameters for the entity
        """
        project_identifier = ProjectIdentifier(
            workspace_id=entity_identifier.workspace_id,
            project_id=entity_identifier.project_id,
        )
        repo = ConfigurableParametersRepo(project_identifier)
        latest_config = repo.get_latest_by_identifier(entity_identifier=entity_identifier)
        if isinstance(latest_config, NullConfigurableParameterContainer) or latest_config.data is None:
            raise ConfigurationNotFoundException(
                f"Cannot find a configuration for the requested entity. "
                f"Perhaps the configuration was not initialized yet? "
                f"Entity Identifier: `{entity_identifier}`."
            )
        return latest_config

    @staticmethod
    def __get_model_storages_by_task_id(project_identifier: ProjectIdentifier, task_id: ID) -> tuple[ModelStorage, ...]:
        """
        Retrieve all the model storages of a task by its ID.

        Either returns the model storages from the cache,
         or loads it from the repository if it is not found in the cache.

        :param project_identifier: Identifier of the project containing the task
        :param task_id: ID of the task to get the model storages for
        :return: List of model storages associated to the task identified by `task_id`
        """
        task = TaskNodeRepo(project_identifier).get_by_id(task_id)
        if task.task_properties.is_trainable:
            return tuple(ModelStorageRepo(project_identifier).get_by_task_node_id(task_node_id=task.id_))
        return ()
