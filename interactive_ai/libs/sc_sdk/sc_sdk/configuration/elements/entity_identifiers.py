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

"""
This module implements the EntityIdentifier classes that are used to identify specific models or components
"""

from __future__ import annotations

import copy
from enum import Enum
from typing import TYPE_CHECKING

from attr import asdict, attrib, attrs

from sc_sdk.configuration.enums import ConfigurableParameterType
from sc_sdk.configuration.helper.utils import ids_to_strings

from .utils import attr_convert_component_type, convert_string_to_id
from geti_types import ID

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from sc_sdk.configuration.enums.component_type import ComponentType


@attrs(frozen=True)
class EntityIdentifier:
    """
    Base data class that provides a view of the identifiers for the entity to which a Configuration applies.

    :var workspace_id: ID of the workspace which the configuration belongs to
    :var project_id: ID of the project which the configuration belongs to
    :var type: Instance of the `ConfigElementType` Enum, representing the type of the configuration
    """

    # Unfortunately a converter with Optional parameter is not correctly recognized
    workspace_id = attrib(type=ID, converter=convert_string_to_id)  # type: ignore[misc]
    project_id = attrib(type=ID, converter=convert_string_to_id)  # type: ignore[misc]
    type = attrib(type=ConfigurableParameterType)

    def as_dict(
        self,
        serialize_ids: bool = False,
        enum_to_str: bool = False,
        exclude_keys: Sequence | None = None,
    ) -> dict:
        """
        Returns a dictionary representation of the entity identifier

        :param serialize_ids: True to convert all ids to strings
        :param enum_to_str: True to convert enums to strings
        :param exclude_keys: Sequence of keys to exclude from the dict
        :return: Dictionary representation of the entity identifier
        """
        dict_repr = asdict(self)
        if enum_to_str:
            for key, value in dict_repr.items():
                if isinstance(value, Enum):
                    dict_repr.update({key: str(value)})
        for key in exclude_keys or []:
            dict_repr.pop(key, None)
        return ids_to_strings(dict_repr) if serialize_ids else dict_repr

    @staticmethod
    def from_dict(
        input_dict: Mapping,
    ) -> ComponentEntityIdentifier | ModelEntityIdentifier:
        """
        Create a Component or Model entity identifier object from an input dictionary.

        :param input_dict: dictionary containing the data to construct the entity
            identifier from
        :return: EntityIdentifier of the corresponding type
        """
        constructor_dict = dict(copy.deepcopy(input_dict))
        parameter_type_string = constructor_dict.pop("type")
        parameter_type = ConfigurableParameterType[parameter_type_string]
        constructor: type[ModelEntityIdentifier | ComponentEntityIdentifier]
        if parameter_type == ConfigurableParameterType.HYPER_PARAMETERS:
            constructor = ModelEntityIdentifier
        elif parameter_type == ConfigurableParameterType.COMPONENT_PARAMETERS:
            constructor = ComponentEntityIdentifier
        else:
            raise TypeError(f"Invalid type found in entity identifier dict: {parameter_type} is not supported.")
        return constructor(**constructor_dict)


@attrs(frozen=True)
class ComponentEntityIdentifier(EntityIdentifier):
    """
    Data class that provides a view of the identifiers for the Component to which the ComponentConfig applies

    :var workspace_id: ID of the workspace which the configuration belongs to
    :var project_id: ID of the project which the configuration belongs to
    :var type: Instance of the `ConfigElementType` Enum, representing the type of the configuration
    :var task_id: ID of the task which the configuration belongs to
    :var component: instance of the ComponentType Enum representing the component that the ComponentConfig belongs to.
    """

    component: ComponentType = attrib(converter=attr_convert_component_type)  # type: ignore[misc]
    task_id: ID | None = attrib(default=None, converter=convert_string_to_id)  # type: ignore[misc]
    type: ConfigurableParameterType = attrib(
        default=ConfigurableParameterType.COMPONENT_PARAMETERS,
        kw_only=True,
    )


@attrs(frozen=True)
class ModelEntityIdentifier(EntityIdentifier):
    """
    Data class that provides a view of the identifiers for the Model to which the ModelConfig applies

    :var workspace_id: ID of the workspace which the configuration belongs to
    :var type: Instance of the `ConfigElementType` Enum, representing the type of the configuration
    :var model_storage_id: ID of the model_storage which the configuration belongs to
    """

    model_storage_id = attrib(type=ID, converter=convert_string_to_id)  # type: ignore[misc]
    type: ConfigurableParameterType = attrib(default=ConfigurableParameterType.HYPER_PARAMETERS, kw_only=True)
