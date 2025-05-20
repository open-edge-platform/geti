# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
#

"""This module implements the ConfigurationManager class"""

import functools
import logging
from typing import Any

from communication.exceptions import AlgorithmNotFoundException, TaskNotFoundException
from configuration import ComponentRegisterEntry, ConfigurableComponentRegister

from geti_fastapi_tools.exceptions import ModelNotFoundException, ProjectNotFoundException
from geti_kafka_tools import publish_event
from geti_telemetry_tools import unified_tracing
from geti_types import CTX_SESSION_VAR, ID, ProjectIdentifier
from iai_core.configuration.elements.component_parameters import ComponentParameters, ComponentType
from iai_core.configuration.elements.configurable_parameters import ConfigurableParameters
from iai_core.configuration.elements.hyper_parameters import HyperParameters
from iai_core.configuration.interfaces.configurable_parameters_interface import IConfigurableParameterContainer
from iai_core.entities.model import Model, NullModel
from iai_core.entities.model_storage import ModelStorage, ModelStorageIdentifier, NullModelStorage
from iai_core.entities.project import NullProject, Project
from iai_core.entities.task_node import TaskNode
from iai_core.repos import ConfigurableParametersRepo, ModelRepo, ModelStorageRepo, ProjectRepo
from iai_core.services.model_service import ModelService

logger = logging.getLogger(__name__)


class ConfigurationManager:
    """
    This class is responsible for gathering the data to handle REST requests for the
    configuration for all components and tasks. It has the following responsibilities:

        1. Processing requests to update configurations, persisting them to the
            appropriate repository.
        2. Processing requests to retrieve the configuration for a project, by querying
            the repositories.
    """

    @staticmethod
    def __get_active_model_storage_by_project_and_task_id(project_id: ID, task_id: ID) -> ModelStorage:
        """
        Retrieve the active model storage by task ID.

        Either returns the ModelStorage from the cache or loads it from the repository,
        if it is not found in the cache.

        :param project_id: ID of the project to get in which the task to get the
            ModelStorage for lives
        :param task_id: ID of the task to get the model storage for
        :return: Active ModelStorage used in the task identified by `task_id`
        """
        project = ProjectRepo().get_by_id(project_id)
        if isinstance(project, NullProject):
            raise ProjectNotFoundException(project_id)

        trainable_task: TaskNode | None = None
        for task in project.tasks:
            if task.id_ == task_id and task.task_properties.is_trainable:
                trainable_task = task
                break

        if trainable_task is not None:
            return ModelService.get_active_model_storage(
                project_identifier=project.identifier,
                task_node_id=trainable_task.id_,
            )
        return NullModelStorage()

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
        return tuple(ModelStorageRepo(project_identifier).get_by_task_node_id(task_node_id=task_id))

    @functools.lru_cache(maxsize=128)
    @staticmethod
    def __get_config_repo(workspace_id: ID, project_id: ID) -> ConfigurableParametersRepo:
        """
        Retrieve a config repository by workspace and project ids. Either returns the repository
        from the cache or creates it

        :param workspace_id: ID of the workspace in which the project lives
        :param project_id: ID of the project containing the config
        :return: ConfigurableParametersRepo for the project
        """
        project_identifier = ProjectIdentifier(
            workspace_id=workspace_id,
            project_id=project_id,
        )
        return ConfigurableParametersRepo(project_identifier)

    @unified_tracing
    @staticmethod
    def get_active_configuration_for_task(
        workspace_id: ID, project_id: ID, task_id: ID
    ) -> list[IConfigurableParameterContainer]:
        """
        Returns the latest Configuration entities related to the active model storage
        of a certain task.
        This includes ModelConfig entities and ComponentConfig entities for that task.

        :param workspace_id: ID of the workspace in which the project lives
        :param project_id: ID of the project in which the task lives
        :param task_id: ID of the task for which to retrieve the configuration
        """
        config_repo = ConfigurationManager.__get_config_repo(workspace_id=workspace_id, project_id=project_id)
        model_storage = ConfigurationManager.__get_active_model_storage_by_project_and_task_id(
            project_id=project_id, task_id=task_id
        )

        # First add the model config
        model_config: HyperParameters = config_repo.get_or_create_hyper_parameters(model_storage=model_storage)
        configs: list[IConfigurableParameterContainer] = [model_config]

        project = ProjectRepo().get_by_id(project_id)
        if isinstance(project, NullProject):
            raise ProjectNotFoundException(project_id)
        task_node = project.get_trainable_task_node_by_id(task_id=task_id)
        if task_node is None:
            raise TaskNotFoundException(task_id)
        # Then add configs for all per-task components
        for component in ConfigurationManager.__get_per_task_components():
            register_data: ComponentRegisterEntry = ConfigurableComponentRegister[component.name].value
            configuration_type = register_data.get_configuration_type(task_type=task_node.task_properties.task_type)
            config = config_repo.get_or_create_component_parameters(
                data_instance_of=configuration_type,
                component=component,
                task_id=task_id,
            )

            configs.append(config)
        return configs

    @staticmethod
    def get_configuration_for_model(
        workspace_id: ID, project_id: ID, task_id: ID, model_id: ID
    ) -> tuple[ConfigurableParameters, ID]:
        """
        Returns the ConfigurableParameters that were used to train a model. This is not
        the current configuration, but the configuration used, from the history of the
        model. Returns only the ConfigurableParameters, not a IConfigurableParametersEntity.
        Additionally, return the ID of the model storage the model lives in.

        :param workspace_id: ID of the workspace in which the project lives
        :param project_id: ID of the project in which the task lives
        :param task_id: ID of the task this model belongs to
        :param model_id: ID of the model to get the related configuration for
        :raises ModelNotFoundException: If the model with ID `model_id` was not found
            in any of the model storages for the task
        :return: Tuple containing:
            - ConfigurableParameters that were used to generate the model
            - Model storage the model lives in
        """
        project_identifier = ProjectIdentifier(workspace_id=workspace_id, project_id=project_id)
        task_model_storages = ConfigurationManager.__get_model_storages_by_task_id(
            project_identifier=project_identifier, task_id=task_id
        )

        model: Model | None = None
        model_storage_id: ID | None = None
        for model_storage in task_model_storages:
            model_storage_identifier = ModelStorageIdentifier(
                workspace_id=project_identifier.workspace_id,
                project_id=project_identifier.project_id,
                model_storage_id=model_storage.id_,
            )
            model = ModelRepo(model_storage_identifier).get_by_id(model_id)
            if not isinstance(model, NullModel):
                model_storage_id = model_storage.id_
                break
        if model is None or model_storage_id is None:
            raise ModelNotFoundException(model_id)
        return model.configuration.configurable_parameters, model_storage_id

    @staticmethod
    @unified_tracing
    def get_configuration_for_algorithm(
        algorithm_name: str, workspace_id: ID, project_id: ID, task_id: ID
    ) -> HyperParameters:
        """
        Returns the HyperParameters connected to an algorithm with algorithm_name, in
        the task with task_id. This is not necessarily the current configuration of the
        task, but the configuration that was most recently set for a specific algorithm.
        The function checks all model storages connected to the task with task_id,
        and if a model_storage has the queried algorithm_name, the current configuration
        for that model storage will be fetched. If no configuration had yet been
        set for that model storage, the default configurable parameters will
        be returned.

        :param algorithm_name: name of the algorithm to get the configuration for.
        algorithm_name in the API is model_template_id in the backend.
        :param workspace_id: ID of the workspace in which the project lives
        :param project_id: ID of the project in which the task lives
        :param task_id: ID of the task the configuration is connected to
        :return: HyperParameters for the current configuration of
        :raises TaskNotFoundError if the task with task_id does not belong to the project
        :raises AlgorithmNotFoundError if there is no model storage with
        :raises ConfigurationNotFoundException if the configuration is not found in the repo
        model_storage_id= algorithm_name in the task
        """
        project = ProjectRepo().get_by_id(project_id)
        if isinstance(project, NullProject):
            raise ProjectNotFoundException(project_id)
        config_repo = ConfigurationManager.__get_config_repo(workspace_id=workspace_id, project_id=project_id)
        trainable_task: TaskNode | None = None
        for task in project.tasks:
            if task.id_ == task_id and task.task_properties.is_trainable:
                trainable_task = task
                break
        if trainable_task is None:
            raise TaskNotFoundException(task_id)

        try:
            model_storage = ModelService.get_or_create_model_storage(
                project_identifier=project.identifier,
                task_node=trainable_task,
                model_template_id=algorithm_name,
            )
        except ValueError as error:
            raise AlgorithmNotFoundException(message=str(error))

        config: HyperParameters = config_repo.get_or_create_hyper_parameters(model_storage=model_storage)
        return config

    @staticmethod
    @unified_tracing
    def get_global_configuration(workspace_id: ID, project_id: ID) -> list[ComponentParameters]:
        """
        Prepares the REST response for configurable parameters for components that are
        defined project-wide, (as opposed to per-task components).

        :param workspace_id: ID of the workspace in which the project lives
        :param project_id: Project for which to retrieve the global components
        :return: dictionary containing the serialized configurations, grouped per domain
            and per component
        """
        config_repo = ConfigurationManager.__get_config_repo(workspace_id=workspace_id, project_id=project_id)
        configs = []
        for component in ConfigurationManager.__get_global_components():
            register_data: ComponentRegisterEntry = ConfigurableComponentRegister[component.name].value
            config = config_repo.get_or_create_component_parameters(
                data_instance_of=register_data.get_configuration_type(),
                component=component,
                task_id=None,
            )
            configs.append(config)
        return configs

    @staticmethod
    @unified_tracing
    def get_configuration_for_task_chain(workspace_id: ID, project_id: ID) -> list[dict[str, Any]]:
        """
        Create a list of the configurable parameters for all tasks in the project.
        Each list entry contains the task and a list of configurable parameters for
        that task.

        Note: the current implementation is limited to the active model storages only.

        :param workspace_id: ID of the workspace in which the project lives
        :param project_id: ID of the project for which to retrieve the configuration
        """
        project = ProjectRepo().get_by_id(project_id)
        if isinstance(project, NullProject):
            raise ProjectNotFoundException(project_id)
        task_chain_configs = []
        for task_node in ConfigurationManager.__get_trainable_task_nodes(project):
            task_config_list = ConfigurationManager.get_active_configuration_for_task(
                workspace_id=workspace_id, project_id=project_id, task_id=task_node.id_
            )
            task_chain_configs.append({"task": task_node, "configurations": task_config_list})
        return task_chain_configs

    @staticmethod
    @unified_tracing
    def get_full_configuration(
        workspace_id: ID, project_id: ID
    ) -> tuple[list[ComponentParameters], list[dict[str, Any]]]:
        """
        Create a dictionary of the full configurable parameters in the project. This
        includes the parameters for both the global components as well as the task chain.

        The dictionary has two keys `global` and `task_chain`. The values for these
        keys each hold a list of configurations for either the project-wide components
        or the task chain

        :param workspace_id: ID of the workspace in which the project lives
        :param project_id: ID of the project for which to retrieve the configuration
        """
        global_configs = ConfigurationManager.get_global_configuration(workspace_id=workspace_id, project_id=project_id)
        task_chain_configs = ConfigurationManager.get_configuration_for_task_chain(
            workspace_id=workspace_id, project_id=project_id
        )

        return global_configs, task_chain_configs

    @staticmethod
    def __get_trainable_task_nodes(project: Project) -> list[TaskNode]:
        """
        Returns a list of trainable task nodes in the project

        :param project: Project to retrieve the trainable tasks for
        :return: list of task nodes that are trainable
        """
        return [node for node in project.tasks if node.task_properties.is_trainable]

    @staticmethod
    def __get_per_task_components() -> list[ComponentType]:
        """
        Get all components that operate per-task, as opposed to project-wide.
        """
        return [
            component
            for component in ComponentType
            if component.metadata.per_task and component is not ComponentType.NULL_COMPONENT
        ]

    @staticmethod
    def __get_global_components() -> list[ComponentType]:
        """
        Get all components that operate project-wide, as opposed to per-task.
        """
        return [
            component
            for component in ComponentType
            if not component.metadata.per_task and component is not ComponentType.NULL_COMPONENT
        ]

    @staticmethod
    @unified_tracing
    def save_configuration_list(
        workspace_id: ID,
        project_id: ID,
        configurable_parameter_list: list[IConfigurableParameterContainer],
    ) -> None:
        """
        Persist a list of new configurable parameters in the correct repository.

        :param workspace_id: ID of the workspace to which the configurable parameters
            in the list should be saved
        :param project_id: ID of the project for which the configurable parameters are
            saved
        :param configurable_parameter_list: List of ConfigurableParameterContainers,
            holding the hyper parameters or component parameters to save to the
            repository
        """
        repo = ConfigurationManager.__get_config_repo(workspace_id=workspace_id, project_id=project_id)
        model_storage_id = ""
        for configurable_parameters in configurable_parameter_list:
            repo.save(configurable_parameters)
            if isinstance(configurable_parameters, HyperParameters):
                model_storage_id = str(configurable_parameters.model_storage_id)

        body = {
            "workspace_id": str(workspace_id),
            "project_id": str(project_id),
            "model_storage_id": str(model_storage_id),
        }
        publish_event(
            topic="configuration_changes",
            body=body,
            key=str(project_id).encode(),
            headers_getter=lambda: CTX_SESSION_VAR.get().as_list_bytes(),
        )
