# INTEL CONFIDENTIAL
#
# Copyright (C) 2022 Intel Corporation
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
import copy
import logging
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from attr import fields_dict

from geti_fastapi_tools.exceptions import InvalidEntityIdentifierException
from geti_telemetry_tools import unified_tracing
from geti_types import ID
from sc_sdk.configuration.elements import metadata_keys
from sc_sdk.configuration.elements.entity_identifiers import EntityIdentifier, ModelEntityIdentifier
from sc_sdk.configuration.elements.hyper_parameters import HyperParameters
from sc_sdk.configuration.elements.parameter_group import ParameterGroup
from sc_sdk.configuration.enums.config_element_type import ConfigElementType
from sc_sdk.configuration.enums.configurable_parameter_type import ConfigurableParameterType
from sc_sdk.configuration.helper.convert import parameter_group_to_dict
from sc_sdk.configuration.interfaces.configurable_parameters_interface import IConfigurableParameterContainer
from sc_sdk.configuration.ui_rules.rules import NullUIRules
from sc_sdk.entities.task_node import TaskNode

logger = logging.getLogger("sc_rest_views")
BE_VIEWS = logging.DEBUG
IO_VIEWS = logging.DEBUG

COMPONENTS = "components"
ENTITY_IDENTIFIER = "entity_identifier"
GROUPS = "groups"
ID_ = "id"
NAME = "name"
GROUP_NAME = "group_name"
PARAMETERS = "parameters"
TASK_ID = "task_id"
TASK_TITLE = "task_title"
TYPE = "type"
TEMPLATE_TYPE = "template_type"
DATA_TYPE = "data_type"
MODEL_STORAGE_ID = "model_storage_id"
WORKSPACE_ID = "workspace_id"
TASK_CHAIN = "task_chain"
GLOBAL = "global"
ITEMS = "items"
PROJECT_ID = "project_id"
HYPER_PARAMETER_GROUP = "HYPER_PARAMETER_GROUP"
VISIBLE_IN_UI = "visible_in_ui"

# These groups are hidden as a workaround for CVS-144193
HIDDEN_HYPER_PARAMETER_GROUPS = {"pot_parameters", "nncf_optimization"}


@dataclass
class HyperParameterGroupList:
    """
    Data container class holding the rest representation of all hyper parameter
    groups for a single dictionary representing a ModelEntityIdentifier

    :var entity_identifier: Dictionary containing the identifiers for the entity to
        which the hyper parameter groups relate
    :var hyper_parameter_groups: List of dictionaries, each representing a single
        hyper parameter group
    """

    entity_identifier: dict[str, str] = field(default_factory=dict)
    hyper_parameter_groups: list[dict[str, Any]] = field(default_factory=list)

    def append_group(self, hyper_parameter_group: dict[str, Any]) -> None:
        """
        Appends a `hyper_parameter_group` to the existing list of hyper parameter
        groups in the container

        NOTE: The 'id' key is stripped from the group, because it is not used for
            a parameter group

        :param hyper_parameter_group: dictionary representation of a hyper parameter
            group
        """
        group_to_add = {key: value for key, value in hyper_parameter_group.items() if key != ID_}
        self.hyper_parameter_groups.append(group_to_add)

    def _clean_entity_identifier(self):
        """
        Removes any fields in the entity identifier dict that do not belong to a
        ModelEntityIdentifier
        """
        self.entity_identifier = {
            key: value for key, value in self.entity_identifier.items() if key in fields_dict(ModelEntityIdentifier)
        }

    def to_dict(self) -> dict[str, dict[str, str] | list[dict[str, Any]]]:
        """
        Converts the HyperParameterGroupList to a dictionary conforming to the REST
        contract.

        :return: Dictionary holding the keys 'entity_identifier' and 'groups', with
            the corresponding data as values
        """
        self._clean_entity_identifier()
        return {
            ENTITY_IDENTIFIER: self.entity_identifier,
            GROUPS: self.hyper_parameter_groups,
        }


class ConfigurationRESTViews:
    @staticmethod
    @unified_tracing
    def global_config_from_rest(
        global_config_rest: dict[str, list[dict[str, Any]]],
        workspace_id: ID,
        project_id: ID,
    ) -> list[tuple[dict, EntityIdentifier]]:
        """
        Converts a dictionary that contains the global configuration to a list of appropriately
        structured dictionaries that can be converted into configurations.

        :param global_config_rest: Dictionary containing global configuration, as passed by the user
        :param workspace_id: ID of the workspace the configuration lives in
        :param project_id: Project for which to change the configuration
        :return: List of tuples containing configurations and entity identifiers, that can be readily deserialized
        into configuration objects
        """
        config_list_rest = global_config_rest.get("global", list({}))
        return ConfigurationRESTViews.config_list_from_rest_dict(
            {"components": config_list_rest},
            workspace_id=workspace_id,
            project_id=project_id,
        )

    @staticmethod
    @unified_tracing
    def task_chain_config_from_rest(
        task_chain_config_rest: dict[str, list[dict[str, Any]]],
        workspace_id: ID,
        project_id: ID,
    ) -> list[list[tuple[dict, EntityIdentifier]]]:
        """
        Converts a dictionary that contains the task chain configuration to a list of appropriately
        structured dictionaries that can be converted into task configurations.

        :param task_chain_config_rest: Dictionary containing task chain configuration, as passed by the user
        :param workspace_id: ID of the workspace the configuration lives in
        :param project_id: Project for which to change the configuration
        :return: Nested list of restructured dictionaries and entity identifiers, that can be readily deserialized into
        configuration objects for each task
        """
        config_list_rest = task_chain_config_rest.get("task_chain", [{"task_id": ""}])
        return ConfigurationRESTViews._task_chain_config_from_rest_list(
            config_list_rest, workspace_id=workspace_id, project_id=project_id
        )

    @staticmethod
    @unified_tracing
    def config_list_from_rest_dict(
        rest_input: dict[str, list[dict]],
        workspace_id: ID,
        project_id: ID,
        task_id: ID | None = None,
    ) -> list[tuple[dict, EntityIdentifier]]:
        """
        Converts a list of configurations that are sent to the configuration POST endpoint to a list of appropriately
        structured dictionaries that can be converted into configurations.

        :param rest_input: list of dictionaries representing configurations
        :param workspace_id: ID of the workspace
        :param project_id: ID of the project
        :param task_id: Optional ID of the task
        :return: List of tuples containing configurations and entity identifiers, that can be readily deserialized
        into configuration objects
        """
        output_list: list[tuple[dict, EntityIdentifier]] = []
        parameter_group_mapping: dict[str, HyperParameterGroupList] = {}
        for config_dict in rest_input[COMPONENTS]:
            entity_identifier = copy.deepcopy(config_dict[ENTITY_IDENTIFIER])
            if entity_identifier[TYPE] != HYPER_PARAMETER_GROUP:
                output_list.append(
                    ConfigurationRESTViews._config_dict_from_rest(
                        rest_input=config_dict,
                        workspace_id=workspace_id,
                        project_id=project_id,
                        task_id=task_id,
                    )
                )
            else:
                # Collect all hyper parameter groups for the same entity_identifer
                entity_identifier[TYPE] = ConfigurableParameterType.HYPER_PARAMETERS.name
                group_config = {key: value for key, value in config_dict.items() if key != ENTITY_IDENTIFIER}
                model_storage_id = entity_identifier[MODEL_STORAGE_ID]
                parameter_groups_for_model_storage = parameter_group_mapping.get(model_storage_id)
                group_name = entity_identifier[GROUP_NAME]
                group_config.update({NAME: group_name})
                if parameter_groups_for_model_storage is None:
                    parameter_group_list = HyperParameterGroupList(
                        entity_identifier=entity_identifier,
                        hyper_parameter_groups=[group_config],
                    )
                    parameter_group_mapping.update({model_storage_id: parameter_group_list})
                else:
                    parameter_groups_for_model_storage.append_group(group_config)
        for hyper_parameter_config_list in parameter_group_mapping.values():
            # Group all hyper parameter groups for the same entity_identifier in
            # single dictionary, and convert to object
            output_list.append(
                ConfigurationRESTViews._config_dict_from_rest(
                    rest_input=hyper_parameter_config_list.to_dict(),
                    workspace_id=workspace_id,
                    project_id=project_id,
                    task_id=task_id,
                )
            )
        return output_list

    @staticmethod
    @unified_tracing
    def _config_dict_from_rest(
        rest_input: dict, workspace_id: ID, project_id: ID, task_id: ID | None = None
    ) -> tuple[dict, EntityIdentifier]:
        """
        Convert the rest input from the configuration POST endpoint into a dictionary
        that is structured appropriately, such that it can be converted into a
        configuration. Also returns the entity identifier, used to identify the
        model or task the configuration belongs to.

        :param rest_input: input dictionary containing a configuration or a list of
            configurations
        :param workspace_id: workspace ID that should set for the returned
            entity_identifier
        :param project_id: project ID that should set for the returned
            entity_identifier.
        :param task_id: Optional task ID that should be set for the returned
            entity_identifier.
        :raises InvalidEntityIdentifierException: In case no valid entity_identifier
            could be constructed from the input
        :return: Tuple containing:
            - restructured_dictionary containing the dictionary structured for config
              creation
            - dictionary used to identify the entity the configuration belongs to
        """
        entity_identifier_dict = rest_input.pop(ENTITY_IDENTIFIER)
        entity_identifier_dict.update({WORKSPACE_ID: workspace_id})
        entity_identifier_dict.update({PROJECT_ID: project_id})
        parameter_type = entity_identifier_dict[TYPE]
        if parameter_type == ConfigurableParameterType.COMPONENT_PARAMETERS.name:
            entity_identifier_dict.update({PROJECT_ID: project_id})
            if task_id is not None and task_id != ID():
                entity_identifier_dict.update({TASK_ID: task_id})
        try:
            entity_identifier = EntityIdentifier.from_dict(entity_identifier_dict)
        except TypeError as error:
            raise InvalidEntityIdentifierException(
                f"Unable to construct valid entity_identifier from REST input data. "
                f"The dictionary {entity_identifier_dict} does not contain a valid "
                f"entity identifier."
            ) from error
        config_dict = ConfigurationRESTViews._restructure_parameter_group_rest_input(rest_input)

        return config_dict, entity_identifier

    @staticmethod
    @unified_tracing
    def _task_chain_config_from_rest_list(
        rest_input: list[dict[str, list[dict]]], workspace_id: ID, project_id: ID
    ) -> list[list[tuple[dict, EntityIdentifier]]]:
        """
        Converts rest input for the set_task_chain_configuration POST endpoint to a nested list of appropriately
        structured dictionaries that can be converted into configurations. Each task in the project corresponds to one
        entry in the outermost list.

        :param rest_input: list of dictionaries representing configurations
        :param workspace_id: ID of the workspace
        :param project_id: ID of the project
        :return: Nested list of restructured dictionaries and entity identifiers, that can be readily deserialized into
        configuration objects for each task
        """
        return [
            ConfigurationRESTViews.config_list_from_rest_dict(
                config_dict, workspace_id=workspace_id, project_id=project_id
            )
            for config_dict in rest_input
        ]

    @staticmethod
    def _restructure_parameter_group_rest_input(rest_input: dict) -> dict:
        """
        Restructures an input dictionary sent to the rest POST endpoint to a form that
        is compatible with configuration creation.

        :param rest_input: input dictionary containing the rest representation of a
            parameter group or configuration
        :return: restructured dictionary
        """
        output_dictionary = copy.deepcopy(rest_input)
        parameter_list = output_dictionary.pop(PARAMETERS, [])
        for parameter in parameter_list:
            name = parameter.pop(NAME)
            if not parameter.get(metadata_keys.UI_RULES, {"": ""}):
                # Remove empty UI rules. These will be instantiated as NullUIRules by
                # the config parser later on
                parameter.pop(metadata_keys.UI_RULES)
            output_dictionary.update({name: parameter})
        group_list = output_dictionary.pop(GROUPS, [])
        for group in group_list:
            name = group.pop(NAME)
            output_dictionary.update({name: ConfigurationRESTViews._restructure_parameter_group_rest_input(group)})
        return output_dictionary

    @staticmethod
    @unified_tracing
    def full_config_to_rest_dict(
        global_config: Sequence[IConfigurableParameterContainer],
        task_chain_config: list[dict[str, Any]],
    ) -> dict[str, list[dict[str, str | list[dict]]]]:
        """
        Converts a dictionary containing the full configuration for a project to a
        serialized, REST compatible representation

        :param global_config: List of ComponentParameters holding the configurable
            parameters for the global components
        :param task_chain_config: List of dictionaries holding the configurable
            parameters for all tasks in the task chain. Each dictionary in the
            outermost list corresponds to the configuration for one task
        :return: Dictionary containing the same keys, with its values converted to
            their REST representation
        """
        global_config_rest = ConfigurationRESTViews.global_config_to_rest_dict(global_config)
        task_chain_config_rest = ConfigurationRESTViews.task_chain_config_to_rest_dict(task_chain_config)
        return {**global_config_rest, **task_chain_config_rest}

    @staticmethod
    @unified_tracing
    def global_config_to_rest_dict(
        global_config: Sequence[IConfigurableParameterContainer],
    ) -> dict[str, list[dict[str, str | list[dict]]]]:
        """
        Converts a dictionary containing the global configuration for a project to a
        serialized, REST compatible representation

        :param global_config: List of ComponentParameters holding the configurable
            parameters for the global components
        :return: Dictionary containing the same keys, with its values converted to
            their REST representation
        """
        global_config_rest = ConfigurationRESTViews._config_list_to_rest(global_config)
        for config in global_config_rest:
            if not config["entity_identifier"]["task_id"]:
                config["entity_identifier"].pop("task_id")
        return {GLOBAL: global_config_rest}

    @staticmethod
    @unified_tracing
    def task_chain_config_to_rest_dict(
        task_chain_config: list[dict[str, Any]],
    ) -> dict[str, list[dict[str, ID | str | list[dict]]]]:
        """
        Converts a list of configurations for all tasks in a task chain to a serialized, REST compatible representation
        according to the REST contract.

        :param task_chain_config: Nested list of configurations for all tasks in the project. Each entry in the
            outermost list represents the configuration for a task in the chain.
        :return: nested list of converted configurations, structured according to the REST contract
        """
        return {
            TASK_CHAIN: [
                ConfigurationRESTViews.task_config_list_to_rest(
                    task=task_config["task"], configs=task_config["configurations"]
                )
                for task_config in task_chain_config
            ]
        }

    @staticmethod
    @unified_tracing
    def task_config_list_to_rest(
        task: TaskNode, configs: list[IConfigurableParameterContainer]
    ) -> dict[str, str | list[dict]]:
        """
        Converts the configurable parameters for a task to serialized REST compatible
        representation.

        :param task: Task the configurable parameters are connected to
        :param configs: List of Configurations that should be converted to REST
        :return: REST view of a configuration for a task
        """
        return {
            COMPONENTS: ConfigurationRESTViews._config_list_to_rest(configs),
            TASK_ID: str(task.id_),
            TASK_TITLE: task.title,
        }

    @staticmethod
    @unified_tracing
    def _config_list_to_rest(
        configs: Sequence[IConfigurableParameterContainer],
    ) -> list[dict]:
        """
        Converts a list of configurable parameters to a serialized REST compatible
        representation.

        :param configs: List of Configurations that should be converted to REST
            representation
        :return: list of converted configurable parameters
        """
        config_list: list[dict] = []
        for config in configs:
            if isinstance(config, HyperParameters):
                config_list.extend(ConfigurationRESTViews._hyper_parameters_to_rest(config))
            else:
                config_dict = ConfigurationRESTViews._config_to_rest(config)
                if config_dict.get("parameters", None) or config_dict.get("groups", None):
                    # Configs that contain no parameters or groups that are visible
                    # in the UI should be excluded from the response
                    config_list.append(config_dict)
        return config_list

    @staticmethod
    def _hyper_parameters_to_rest(hyper_parameters: HyperParameters) -> list[dict]:
        """
        Convert a hyper parameters instance to its REST representation

        :param hyper_parameters: HyperParameters to convert
        :return: list of dictionaries containing the REST representations of the
            parameter groups in the hyper parameters
        """
        if hyper_parameters.data is None:
            logger.warning(
                "Attribute 'data' not found in hyper parameters: %s. Assuming empty.",
                hyper_parameters,
            )
            return []

        group_names = hyper_parameters.data.groups
        parameter_names = hyper_parameters.data.parameters
        if len(parameter_names) != 0 and len(group_names) != 0:
            raise ValueError(
                f"Creating a REST view for hyper parameters with both ungrouped and "
                f"grouped parameters is currently not supported. Found ungrouped "
                f"parameters: {parameter_names} and parameter groups: {group_names}. "
                f"Please either make sure all parameters are grouped, or create two "
                f"separate hyper parameter instances for grouped and ungrouped "
                f"parameters."
            )
        if len(group_names) == 0:
            return [ConfigurationRESTViews._config_to_rest(hyper_parameters)]

        entity_identifier_dict = hyper_parameters.entity_identifier.as_dict(enum_to_str=True, serialize_ids=True)
        entity_identifier_dict[metadata_keys.TYPE] = HYPER_PARAMETER_GROUP
        rest_output_list: list[dict] = []
        for group_number, group_name in enumerate(group_names):
            if group_name in HIDDEN_HYPER_PARAMETER_GROUPS:
                continue
            group_data = getattr(hyper_parameters.data, group_name)
            if not group_data.visible_in_ui:
                # Skip groups that should not be exposed to UI
                continue
            group_rest = ConfigurationRESTViews._parameter_group_to_rest(group_data)
            group_entity_identifier = copy.deepcopy(entity_identifier_dict)
            group_entity_identifier[GROUP_NAME] = group_name
            group_rest[ENTITY_IDENTIFIER] = group_entity_identifier
            group_rest[NAME] = group_name
            group_rest[ID_] = hyper_parameters.id + f"-{group_number}"
            # Remove keys that should not be included in response
            group_rest.pop(VISIBLE_IN_UI, False)
            rest_output_list.append(group_rest)
        return rest_output_list

    @staticmethod
    @unified_tracing
    def _config_to_rest(config: IConfigurableParameterContainer) -> dict:
        """
        Convert a configuration to its REST representation.

        :param config: Configuration to convert
        :return: serialized dictionary representation of the configuration
        """
        if config.data is not None:
            config_dict = ConfigurationRESTViews._parameter_group_to_rest(config.data)
        else:
            raise ValueError(f"No configurable parameter data found in {config}.")
        config_dict.pop(metadata_keys.VISIBLE_IN_UI)

        # Serialize ID
        config_dict[ID_] = str(config_dict[ID_])

        # Serialize and group entity_identifier items for the config
        entity_identifier_dict = config.entity_identifier.as_dict(enum_to_str=True, serialize_ids=True)
        config_dict[ENTITY_IDENTIFIER] = entity_identifier_dict

        return config_dict

    @staticmethod
    def _parameter_group_to_rest(parameter_group: ParameterGroup) -> dict:
        """
        Convert a parameter group to its REST representation. Uses recursion to convert nested groups.

        :param parameter_group: ParameterGroup to convert
        :return: serialized dictionary holding the REST representation of the group, according to the contract
        """
        config_dict = parameter_group_to_dict(parameter_group, enum_to_str=True)

        config_dict[PARAMETERS] = []
        for parameter_name in parameter_group.parameters:
            parameter_config = config_dict.pop(parameter_name)

            metadata = parameter_group.get_metadata(parameter_name)
            # Skip parameters that should not be exposed in the ui. These will not be
            # part of the response at all
            if not metadata[metadata_keys.VISIBLE_IN_UI]:
                continue
            parameter_config.pop(metadata_keys.VISIBLE_IN_UI)

            # Remove specific flags from the metadata that should not be passed to the
            # ui
            parameter_config.pop(metadata_keys.AFFECTS_OUTCOME_OF)

            # Convert any NullUIRules to empty objects, to reduce verbosity of the rest
            # response
            if isinstance(metadata[metadata_keys.UI_RULES], NullUIRules):
                parameter_config[metadata_keys.UI_RULES] = {}

            # Parameter name is needed for later deserialization
            parameter_config[NAME] = parameter_name

            # Split type into template_type and data_type
            parameter_type = parameter_config.pop(TYPE)
            (
                template_type,
                data_type,
            ) = ConfigurationRESTViews._parameter_type_to_template_and_data_type(parameter_type)
            parameter_config[TEMPLATE_TYPE] = template_type
            parameter_config[DATA_TYPE] = data_type

            # Convert option dict of selectable to a list of values
            if parameter_type == "SELECTABLE":
                options_dict = parameter_config.pop(metadata_keys.OPTIONS)
                options_list = [value for key, value in options_dict.items()]
                parameter_config[metadata_keys.OPTIONS] = options_list

            config_dict[PARAMETERS].append(parameter_config)

        if len(parameter_group.groups) != 0:
            config_dict[GROUPS] = []
        for group_name in parameter_group.groups:
            # Recursively convert group in order to handle nested ParameterGroups
            group = getattr(parameter_group, group_name)

            # skip groups that should not be shown in the UI. These will not be
            # included in the REST response
            if not group.visible_in_ui:
                continue
            group_config = ConfigurationRESTViews._parameter_group_to_rest(group)
            group_config.pop(metadata_keys.VISIBLE_IN_UI)
            # Group name is needed for later deserialization
            group_config[NAME] = group_name
            config_dict.pop(group_name)
            config_dict[GROUPS].append(group_config)
        return config_dict

    @staticmethod
    def _parameter_type_to_template_and_data_type(
        parameter_type: str,
    ) -> tuple[str, str]:
        """
        Convert internal naming of parameter type to REST format of template_type and
        data_type, which are more user friendly.

        :param parameter_type: Parameter type to convert to REST format
        :return: tuple containing:
            - template_type: 'input' or 'selectable'
            - data_type: 'integer', 'float', 'boolean' or 'string'
        """
        if parameter_type == ConfigElementType.INTEGER.name:
            return "input", "integer"
        if parameter_type == ConfigElementType.FLOAT.name:
            return "input", "float"
        if parameter_type == ConfigElementType.BOOLEAN.name:
            return "input", "boolean"
        if parameter_type == ConfigElementType.FLOAT_SELECTABLE.name:
            return "selectable", "float"
        if parameter_type == ConfigElementType.SELECTABLE.name:
            return "selectable", "string"
        raise NotImplementedError(f"Rest view of parameter type {parameter_type} is currently not implemented")
