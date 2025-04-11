"""This module implements the IConfigurableParameterContainer interface"""

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
from __future__ import annotations

import abc
from typing import Generic, TypeVar

from attr.exceptions import FrozenAttributeError

from sc_sdk.configuration.elements.configurable_parameters import ConfigurableParameters
from sc_sdk.configuration.elements.entity_identifiers import EntityIdentifier
from sc_sdk.configuration.enums import ConfigurableParameterType
from sc_sdk.entities.persistent_entity import PersistentEntity

from geti_types import ID

TConfig = TypeVar("TConfig", bound=ConfigurableParameters)


class IConfigurableParameterContainer(Generic[TConfig], PersistentEntity):
    """
    This class is the interface for HyperParameter and ComponentParameter
    objects. These objects are container classes that consists of:
    1. Identifiers that point to the object to which the ConfigurableParameters apply.
    2. The ConfigurableParameters data, containing the parameter schema and values

    This class accepts a type parameter TConfig, which can be used to specify the type
    of the ConfigurableParameters data it is expected to hold.

    :param workspace_id: ID of the workspace containing the ConfigurableParameters
    :param project_id: ID of the project containing the ConfigurableParameters
    :param data: ConfigurableParameters containing the schema and values for the actual
        ConfigurableParameters. Can be nested, and can be set after initialization.
        Defaults to None.
    :param id_: ID of the ConfigurableParameters
    """

    def __init__(
        self,
        workspace_id: ID | str,
        project_id: ID | str,
        id_: ID,
        data: TConfig | None = None,
    ) -> None:
        PersistentEntity.__init__(self, id_=id_)
        self.workspace_id: ID = ID(workspace_id)
        self.project_id: ID = ID(project_id)
        self.__data = data

    def __repr__(self) -> str:
        """Returns a string representation of the class"""
        return f"{type(self).__name__}(id_={self.id_}, entity_identifier={self.entity_identifier}, data={self.data})"

    def __eq__(self, other: object):
        """Test equality"""
        if not isinstance(other, IConfigurableParameterContainer):
            return False
        return (
            (self.id_ == other.id_)
            and (self.entity_identifier == other.entity_identifier)
            and (self.data == other.data)
        )

    @property
    @abc.abstractmethod
    def entity_identifier(self) -> EntityIdentifier:
        """
        Returns an EntityIdentifier that uniquely identifies the object for which the
        ConfigurableParameters define a configuration.
        """
        raise NotImplementedError("Entity identifier is not implemented for base configurable parameter interface")

    @property
    def data(self):  # noqa: ANN201
        """
        Returns the schema and actual values of the configurable parameters stored in
        the ConfigurableParameters object
        """
        data = self.__data
        if data is not None:
            data.id = self.id_
        return data

    @data.setter
    def data(self, configurable_parameters: TConfig):
        """
        Set the data attribute for an instance of the ConfigurableParameters
        """
        self.__data = configurable_parameters

    @classmethod
    @abc.abstractmethod
    def get_type(cls) -> ConfigurableParameterType:
        """
        Returns the type of the configurable parameter object, as an instance of the
        ConfigurableParameterType Enum
        """
        raise NotImplementedError("get_type method is not implemented for base configurable parameter interface")

    def __getattr__(self, item):  # noqa: ANN001
        """
        Redirect attribute lookup to the data class, so that parameters in the
        configuration can be accessed from the container class directly
        """
        # Use __dict__ to get the data to avoid infinite recursion on attribute
        # lookup during class initialization
        data = self.__dict__.get("_IConfigurableParameterContainer__data", None)
        if data is not None:
            return getattr(data, item)
        raise AttributeError(f"No configurable parameter data found in {type(self).__name__} instance.")

    @classmethod
    def from_entity_identifier(
        cls,
        entity_identifier: EntityIdentifier,
        id: ID,
        data: TConfig | None = None,
    ) -> IConfigurableParameterContainer:
        """
        Method to create a new instance of a IConfigurableParameterContainer, from the
        entity identifier of a previous instance.

        :param entity_identifier: EntityIdentifier object containing the identifiers
            that should be assigned to the new instance
        :param id: ID of the ConfigurableParameters
        :param data: Optional ConfigurableParameters object holding the data that
            should be contained by the new instance
        :return: HyperParameters or ComponentParameters object containing the
            specified identifiers and data
        """
        identifier_dict = entity_identifier.as_dict()
        identifier_dict.pop("type")
        return cls(**identifier_dict, data=data, id_=id)


class NullConfigurableParameterContainer(IConfigurableParameterContainer):
    """
    This class defines an empty, unset ConfigurableParameters object
    """

    def __init__(self) -> None:
        super().__init__(workspace_id=ID(), project_id=ID(), id_=ID())

    @property
    def entity_identifier(self) -> EntityIdentifier:
        """
        Returns the EntityIdentifier that uniquely identifies the entity to which
        the ConfigurableParameters held in the ConfigurableParameterContainer relate
        """
        # At the moment the type is not correct, this will be fixed in a later MR when
        # the new ConfigurableParameterContainer classes are fully implemented.
        return EntityIdentifier(workspace_id=self.workspace_id, project_id=self.project_id, type=self.get_type())  # type: ignore

    @property
    def data(self) -> ConfigurableParameters:
        """
        NullConfigurableParameterContainer objects do not contain any data. The data
        property always returns an empty ConfigurableParameters instance.
        """
        return ConfigurableParameters(header="Empty parameters")  # type: ignore

    @data.setter
    def data(self, configurable_parameters: ConfigurableParameters):  # noqa: ARG002
        """
        Set the data attribute for an instance of the ConfigurableParameterContainer
        """
        raise FrozenAttributeError("Unable to set data for NullConfigurableParameterContainer")

    @classmethod
    def get_type(cls) -> ConfigurableParameterType:
        """
        Returns the type of the ConfigurableParameterContainer, as an instance of the
        ConfigurableParameterType Enum
        """
        return ConfigurableParameterType.NULL_PARAMETERS
