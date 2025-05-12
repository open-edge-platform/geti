#
# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
#

"""
This module contains the MongoDB mappers for HyperParameter and
ComponentParameter entities
"""

from enum import Enum
from typing import Any, Union

import iai_core.configuration.helper as otx_config_helper
from iai_core.configuration.elements import metadata_keys
from iai_core.configuration.elements.hyper_parameters import HyperParameters
from iai_core.configuration.enums.component_type import ComponentType
from iai_core.configuration.enums.configurable_parameter_type import ConfigurableParameterType
from iai_core.configuration.interfaces.configurable_parameters_interface import IConfigurableParameterContainer
from iai_core.configuration.utils.parameter_class_helper import get_class_constructor_by_type
from iai_core.repos.mappers.mongodb_mapper_interface import IMapperSimple

from .id_mapper import IDToMongo
from geti_types import ID

KeyType = Union[ID, ComponentType, ConfigurableParameterType]  # noqa: UP007

DATA_KEY = "data"
ENTITY_IDENTIFIER_KEY = "entity_identifier"
WORKSPACE_ID = "workspace_id"
PROJECT_ID = "project_id"
ID_FIELDS = [WORKSPACE_ID, PROJECT_ID, "model_storage_id", "task_id"]


class ConfigurableParametersToMongo(IMapperSimple[IConfigurableParameterContainer, dict]):
    """
    Class to map a generic Config entity to Mongo, and back again
    """

    @staticmethod
    def map_identifiers_to_strings(identifiers: dict[str, KeyType | None]) -> dict[str, str]:
        """
        Helper function to convert the values in a `identifiers` dictionary to strings. Since the dictionary is meant to
        be used to query the database, all values have to be serialized.

        :param identifiers: Dictionary containing field names as keys, and field values as values.
        :raises: TypeError if a value of unsupported type is passed inside the `identifiers` dictionary. Currently
            supported types are `str`, `ID` and `Enum`
        :return: Dictionary containing the same field names and field values as the input, but with the field
            values serialized to strings

        """
        keys_as_strings: dict[str, Any] = {}
        for key, value in identifiers.items():
            if isinstance(value, ID):
                keys_as_strings[key] = IDToMongo.forward(value)
            elif isinstance(value, str) or value is None:
                keys_as_strings[key] = value
            elif isinstance(value, Enum):
                keys_as_strings[key] = str(value)
            else:
                raise TypeError(
                    f"Unsupported value for key {key}: objects of type {type(value)} can not be used "
                    f"to query the configuration repository."
                )
        return keys_as_strings  # type: ignore[return-value]

    @staticmethod
    def forward(instance: IConfigurableParameterContainer) -> dict:
        # Extract data from the instance
        data = instance.data
        instance_dict = otx_config_helper.convert(config=data, target=dict, enum_to_str=True, id_to_str=True)
        serialized_configuration = {DATA_KEY: instance_dict}

        # Get and serialize identifiers
        identifier_dict = instance.entity_identifier.as_dict(exclude_keys=(WORKSPACE_ID, PROJECT_ID))
        serialized_identifiers = ConfigurableParametersToMongo.map_identifiers_to_strings(identifier_dict)

        serialized_configuration.update({ENTITY_IDENTIFIER_KEY: serialized_identifiers})

        if isinstance(instance, HyperParameters):
            serialized_configuration["single_use"] = instance.single_use

        return serialized_configuration

    @staticmethod
    def backward(instance: dict) -> IConfigurableParameterContainer:
        """
        Creates a configurable parameters object from an input dictionary.
        """
        id_ = IDToMongo.backward(instance["_id"])

        # Note that the configuration will be deserialized to an instance of
        # HyperParameters or ComponentParameters, rather than a base
        # ConfigurableParameters. This can be done because the type of the
        # Configuration is stored with the data
        entity_identifier = instance.get(ENTITY_IDENTIFIER_KEY, {})
        entity_identifier[WORKSPACE_ID] = instance[WORKSPACE_ID]
        entity_identifier[PROJECT_ID] = instance[PROJECT_ID]
        for key, value in entity_identifier.items():
            if key in ID_FIELDS:
                entity_identifier[key] = IDToMongo.backward(value)

        config_data = otx_config_helper.create(instance.get(DATA_KEY, {}))
        parameter_constructor = get_class_constructor_by_type(entity_identifier.pop(metadata_keys.TYPE))

        parameters = parameter_constructor(**entity_identifier, data=config_data, id_=id_)
        if isinstance(parameters, HyperParameters):
            parameters.single_use = instance.get("single_use", False)
        return parameters
