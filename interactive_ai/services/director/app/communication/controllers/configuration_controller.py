# INTEL CONFIDENTIAL
#
# Copyright (C) 2021 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and
# your use of them is governed by the express license under which they were provided to
# you ("License"). Unless the License provides otherwise, you may not use, modify, copy,
# publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is,
# with no express or implied warranties, other than those that are expressly stated
# in the License.

from typing import TYPE_CHECKING, Any

from communication.data_validator import ConfigurationRestValidator
from communication.exceptions import ConfigurationMismatchException, TaskNotFoundException
from communication.views.configuration_rest_views import ConfigurationRESTViews
from configuration import ConfigurationValidator
from configuration.configuration_manager import ConfigurationManager
from coordination.dataset_manager.subset_manager_config import SubsetManagerConfig

from geti_fastapi_tools.exceptions import BadRequestException, ProjectNotFoundException
from geti_fastapi_tools.responses import success_response_rest
from geti_telemetry_tools import unified_tracing
from geti_types import ID
from sc_sdk.configuration.elements.component_parameters import ComponentParameters, ComponentType
from sc_sdk.configuration.elements.hyper_parameters import HyperParameters
from sc_sdk.configuration.enums.configurable_parameter_type import ConfigurableParameterType
from sc_sdk.entities.project import NullProject
from sc_sdk.repos import ConfigurableParametersRepo, ProjectRepo

if TYPE_CHECKING:
    from sc_sdk.configuration.elements.configurable_parameters import ConfigurableParameters
    from sc_sdk.configuration.interfaces import IConfigurableParameterContainer


class ConfigurationRESTController:
    @staticmethod
    @unified_tracing
    def get_full_configuration(workspace_id: ID, project_id: ID) -> dict[str, Any]:
        """
        Get the configuration for the full project associated with `project_id`, living
        in the workspace with `workspace_id`.

        :param workspace_id: ID of the workspace in which the project to get
            the configuration for lives
        :param project_id: ID of the project to get the configuration for.
        :return: Tuple of (response, http_status_code).
            Response contains the requested configuration
        """
        global_config, task_chain_config = ConfigurationManager.get_full_configuration(
            workspace_id=workspace_id, project_id=project_id
        )
        return ConfigurationRESTViews.full_config_to_rest_dict(
            global_config=global_config, task_chain_config=task_chain_config
        )

    @staticmethod
    @unified_tracing
    def get_global_configuration(workspace_id: ID, project_id: ID) -> dict[str, list[dict[str, Any]]]:
        """
        Get the configuration for the global components within the project with
        `project_id`, living in the workspace with `workspace_id`.

        :param workspace_id: ID of the workspace in which the project to get
            the configuration for lives
        :param project_id: ID of the project to get the configuration for.
        :return: Tuple of (response, http_status_code).
            Response contains the requested configuration
        """
        global_config = ConfigurationManager.get_global_configuration(workspace_id=workspace_id, project_id=project_id)
        return ConfigurationRESTViews.global_config_to_rest_dict(global_config)

    @staticmethod
    def get_task_chain_configuration(workspace_id: ID, project_id: ID) -> dict[str, list[dict[str, Any]]]:
        """
        Get the configuration for the full task chain associated with `project_id`.

        :param workspace_id: ID of the workspace in which the project to get
            the configuration for lives
        :param project_id: ID of the project to get the configuration for.
        :return: Tuple of (response, http_status_code).
            Response contains the requested configuration
        """
        task_chain_config = ConfigurationManager.get_configuration_for_task_chain(
            workspace_id=workspace_id, project_id=project_id
        )
        return ConfigurationRESTViews.task_chain_config_to_rest_dict(task_chain_config)

    @staticmethod
    @unified_tracing
    def get_task_or_model_configuration(
        workspace_id: ID,
        project_id: ID,
        task_id: ID,
        model_id: ID | None = None,
        algorithm_name: str | None = None,
    ) -> dict[str, Any]:
        """
        Get the configuration for the task with `task_id` within project `project_id`.

        If model_id is specified, get the configuration used to generate this model.
        If algorithm_name is specified, get the latest configuration used to generate
        a model with this algorithm.
        Otherwise, get the latest configuration relative to the active model.

        :param workspace_id: ID of the workspace in which the project
            to get the configuration for lives
        :param project_id: ID of the project in which the task lives.
        :param task_id: ID of the task to get the configuration for
        :param model_id: ID of the model to get the used configuration for
        :param algorithm_name: name of the algorithm to get the latest configuration for
        :return: Tuple of (response, http_status_code).
            Response contains the requested configuration
        :raises BadRequestException if both model_id and algorithm_name are used as query parameters
        """
        if model_id is not None and algorithm_name is not None:
            raise BadRequestException("Cannot use both model_id and algorithm name as query parameters")
        project = ProjectRepo().get_by_id(project_id)
        if isinstance(project, NullProject):
            raise ProjectNotFoundException(project_id)
        task = project.get_trainable_task_node_by_id(task_id=task_id)
        if task is None:
            raise TaskNotFoundException(task_id=task_id)

        hyper_parameters: HyperParameters
        if model_id is not None:
            (
                model_config,
                model_storage_id,
            ) = ConfigurationManager.get_configuration_for_model(
                workspace_id=workspace_id,
                project_id=project_id,
                task_id=task_id,
                model_id=model_id,
            )
            hyper_parameters = HyperParameters(
                workspace_id=workspace_id,
                project_id=project_id,
                model_storage_id=model_storage_id,
                data=model_config,
                id_=ConfigurableParametersRepo.generate_id(),
            )
            config_list_rest = ConfigurationRESTViews.task_config_list_to_rest(task=task, configs=[hyper_parameters])
        elif algorithm_name is not None:
            config = ConfigurationManager.get_configuration_for_algorithm(
                algorithm_name=algorithm_name,
                workspace_id=workspace_id,
                project_id=project_id,
                task_id=task_id,
            )
            config_list_rest = ConfigurationRESTViews.task_config_list_to_rest(task=task, configs=[config])
        else:
            config_list = ConfigurationManager.get_active_configuration_for_task(
                workspace_id=workspace_id, project_id=project_id, task_id=task_id
            )
            config_list_rest = ConfigurationRESTViews.task_config_list_to_rest(task=task, configs=config_list)

        return config_list_rest

    @staticmethod
    def validate_and_set_task_chain_configuration(
        workspace_id: ID,
        project_id: ID,
        set_request: dict[str, list[dict[str, Any]]],
    ) -> dict[str, Any]:
        ConfigurationRestValidator().validate_task_chain_configuration(set_request)
        return ConfigurationRESTController.set_task_chain_configuration(
            workspace_id=workspace_id,
            project_id=project_id,
            set_request=set_request,
        )

    @staticmethod
    @unified_tracing
    def set_task_chain_configuration(
        workspace_id: ID,
        project_id: ID,
        set_request: dict[str, list[dict[str, Any]]],
    ) -> dict[str, Any]:
        """
        Set the configuration for the full task chain for the project with `project_id`.

        :param workspace_id: ID of the workspace in which the project
            to set the configuration for lives
        :param project_id: ID of the project to set the configuration for.
        :param set_request: List of dictionaries representing configurations.
            Each entry in the outermost list corresponds to the full configuration
            or a task in the task chain
        :return: Tuple of (response, http_status_code) representing whether
            saving was successful or not
        """
        project = ProjectRepo().get_by_id(project_id)
        if isinstance(project, NullProject):
            raise ProjectNotFoundException(project_id)

        task_chain_config_list = ConfigurationRESTViews.task_chain_config_from_rest(
            task_chain_config_rest=set_request,
            workspace_id=workspace_id,
            project_id=project_id,
        )

        trainable_task_nodes_list = project.get_trainable_task_nodes()
        if len(trainable_task_nodes_list) != len(task_chain_config_list):
            raise ConfigurationMismatchException(
                f"Unable to set task chain configuration: The number of tasks in the "
                f"project ({len(trainable_task_nodes_list)}) does not match "
                f"the number of configurations received in the request."
            )

        # Check that request url parameters match id's in the entity_identifiers,
        # and that all tasks exist in the project, and check that the values in the
        # request are valid for all configurations
        updated_configs: list[IConfigurableParameterContainer[ConfigurableParameters]] = []
        for task, task_config_list in zip(trainable_task_nodes_list, task_chain_config_list):
            for config_dict, entity_identifier in task_config_list:
                updated_configs.append(
                    ConfigurationValidator.validate_and_update_config(
                        input_config=config_dict,
                        entity_identifier=entity_identifier,
                        project=project,
                        task_id=task.id_,
                    )
                )

        # Find the subset manager configuration and rescale it if necessary.
        subset_manager_config = next(
            (
                config
                for config in updated_configs
                if config.get_type() == ConfigurableParameterType.COMPONENT_PARAMETERS
                and config.component == ComponentType.SUBSET_MANAGER
            ),
            None,
        )
        if subset_manager_config is not None:
            ConfigurationRESTController._rescale_subset_manager_config(subset_manager_config)  # type: ignore

        # Save once all configs and entity_identifiers are validated
        ConfigurationManager.save_configuration_list(
            workspace_id=workspace_id,
            project_id=project_id,
            configurable_parameter_list=updated_configs,
        )
        return success_response_rest()

    @staticmethod
    def validate_and_set_global_configuration(
        workspace_id: ID,
        project_id: ID,
        set_request: dict[str, list[dict[str, Any]]],
    ) -> dict[str, Any]:
        ConfigurationRestValidator().validate_global_configuration(set_request)
        return ConfigurationRESTController.set_global_configuration(
            workspace_id=workspace_id,
            project_id=project_id,
            set_request=set_request,
        )

    @staticmethod
    @unified_tracing
    def set_global_configuration(
        workspace_id: ID,
        project_id: ID,
        set_request: dict[str, list[dict[str, Any]]],
    ) -> dict[str, Any]:
        """
        Set the configuration for the global components in the project with
        `project_id`.

        :param workspace_id: ID of the workspace in which the project
            to set the configuration for lives
        :param project_id: ID of the project to set the configuration for.
        :param set_request: List of dictionaries representing configurations.
            Each entry in the outermost list corresponds to the configuration of a
            global component
        :return: Tuple of (response, http_status_code) representing whether
            saving was successful or not
        """
        project = ProjectRepo().get_by_id(project_id)
        if isinstance(project, NullProject):
            raise ProjectNotFoundException(project_id)

        global_config_list = ConfigurationRESTViews.global_config_from_rest(
            global_config_rest=set_request,
            workspace_id=workspace_id,
            project_id=project_id,
        )

        # Check that all entity identifiers match with URL parameters, and check that
        # the values in the request are valid for all configurations
        updated_configs: list[IConfigurableParameterContainer[ConfigurableParameters]] = []
        for config_dict, entity_identifier in global_config_list:
            updated_configs.append(
                ConfigurationValidator.validate_and_update_config(
                    input_config=config_dict,
                    entity_identifier=entity_identifier,
                    project=project,
                )
            )
        # Save once all configs and entity_identifiers are validated
        ConfigurationManager.save_configuration_list(
            workspace_id=workspace_id,
            project_id=project_id,
            configurable_parameter_list=updated_configs,
        )

        return success_response_rest()

    @staticmethod
    @unified_tracing
    def set_task_configuration(
        workspace_id: ID,
        task_id: ID,
        project_id: ID,
        set_request: dict[str, list[dict]],
    ) -> dict[str, Any]:
        """
        Set the configuration for the task with `task_id` within project `project_id`.

        :param workspace_id: ID of the workspace in which the project
            to set the configuration for lives
        :param task_id: ID of the task to get the configuration for
        :param project_id: ID of the project in which the task lives.
        :param set_request: Dictionary containing a list of configuration
            for the components in the task
        :return: Tuple of (response, http_status_code) representing
            whether saving was successful or not
        """
        project = ProjectRepo().get_by_id(project_id)
        if isinstance(project, NullProject):
            raise ProjectNotFoundException(project_id)

        task_node = project.get_trainable_task_node_by_id(task_id=task_id)
        if not task_node:
            raise TaskNotFoundException(task_id=task_id)
        ConfigurationRestValidator().validate_task_configuration(set_request)

        task_config_list = ConfigurationRESTViews.config_list_from_rest_dict(
            set_request,
            workspace_id=workspace_id,
            project_id=project_id,
            task_id=task_id,
        )

        # Check that all entity identifiers match with URL parameters and check that
        # the values in the request are valid for all configurations
        updated_configs: list[IConfigurableParameterContainer[ConfigurableParameters]] = []
        for config_dict, entity_identifier in task_config_list:
            updated_configs.append(
                ConfigurationValidator.validate_and_update_config(
                    input_config=config_dict,
                    entity_identifier=entity_identifier,
                    project=project,
                    task_id=task_id,
                )
            )
        subset_manager_config = next(
            (
                config
                for config in updated_configs
                if config.get_type() == ConfigurableParameterType.COMPONENT_PARAMETERS
                and config.component == ComponentType.SUBSET_MANAGER
            ),
            None,
        )
        if subset_manager_config is not None:
            ConfigurationRESTController._rescale_subset_manager_config(subset_manager_config)  # type: ignore
        # Save once all configs and entity_identifiers are validated
        ConfigurationManager.save_configuration_list(
            workspace_id=workspace_id,
            project_id=project_id,
            configurable_parameter_list=updated_configs,
        )

        return success_response_rest()

    @staticmethod
    @unified_tracing
    def set_full_configuration(
        workspace_id: ID,
        project_id: ID,
        set_request: dict[str, list[dict[str, Any]]],
    ) -> dict[str, Any]:
        """
        Set the full configuration for the project with `project_id`.

        :param workspace_id: ID of the workspace in which the project
            to set the configuration for lives
        :param project_id: ID of the project to set the configuration for.
        :param set_request: Dictionary containing two keys:
            - 'global'
            - 'task_chain'
            Each item should contain a list of dictionaries representing configurations.
        :return: Tuple of (response, http_status_code) representing whether
            saving was successful or not
        """
        project = ProjectRepo().get_by_id(project_id)
        if isinstance(project, NullProject):
            raise ProjectNotFoundException(project_id)
        ConfigurationRestValidator().validate_full_configuration(set_request)

        ConfigurationRESTController.set_global_configuration(
            workspace_id=workspace_id,
            project_id=project_id,
            set_request=set_request,
        )
        ConfigurationRESTController.set_task_chain_configuration(
            workspace_id=workspace_id,
            project_id=project_id,
            set_request=set_request,
        )
        return success_response_rest()

    @staticmethod
    def _rescale_subset_manager_config(
        subset_manager_config: ComponentParameters[SubsetManagerConfig],
    ) -> None:
        """
        Rescales the subset manager's subset distribution if the values do not properly add up to 1.

        :param subset_manager_config: Configurable parameters for the subset manager component
        """
        subset_parameters = subset_manager_config.data.subset_parameters  # type: ignore
        subset_parameters_sum = (
            subset_parameters.train_proportion
            + subset_parameters.test_proportion
            + subset_parameters.validation_proportion
        )
        if subset_parameters_sum == 1:
            return
        rescale_value = 1 / (subset_parameters_sum)
        subset_parameters.train_proportion = round(subset_parameters.train_proportion * rescale_value, 2)
        subset_parameters.validation_proportion = round(subset_parameters.validation_proportion * rescale_value, 2)
        subset_parameters.test_proportion = round(
            1 - subset_parameters.train_proportion - subset_parameters.validation_proportion,
            2,
        )
