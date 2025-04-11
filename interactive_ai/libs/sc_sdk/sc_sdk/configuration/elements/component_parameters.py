"""This module implements the ComponentParameter class"""

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

from attr.exceptions import FrozenAttributeError

from sc_sdk.configuration.enums.component_type import ComponentType
from sc_sdk.configuration.enums.configurable_parameter_type import ConfigurableParameterType
from sc_sdk.configuration.interfaces.configurable_parameters_interface import (
    IConfigurableParameterContainer,
    NullConfigurableParameterContainer,
)

from .configurable_parameters import ConfigurableParameters
from .entity_identifiers import ComponentEntityIdentifier
from .hyper_parameters import TConfig
from .utils import attr_convert_component_type
from geti_types import ID


class ComponentParameters(IConfigurableParameterContainer[TConfig]):
    """
    This class contains the configurable parameters for a component.

    This class accepts a type parameter TConfig, which can be used to specify the type
    of the ConfigurableParameters data it is expected to hold.

    :param workspace_id: ID of the workspace in which the
        ComponentParameters live
    :param project_id: ID of the project in which the ComponentParameters
        live
    :param component: ComponentType that identifies to which component the
        ComponentParameters relate
    :param task_id: Optional task_id that should be used if the component parameters
        are task-specific. Defaults to None, which indicates that the parameters affect
        the entire project and are not task-specific
    :param data: ParameterGroup (can be nested) containing the schema and values for
        the actual configurable parameters. `data` is optional and can be set after
        initialization as well.
    :param id_: ID of the ComponentParameters
    """

    def __init__(
        self,
        workspace_id: ID | str,
        project_id: ID | str,
        component: ComponentType | str,
        id_: ID,
        task_id: ID | str | None = None,
        data: TConfig | None = None,
    ) -> None:
        IConfigurableParameterContainer.__init__(
            self, workspace_id=workspace_id, project_id=project_id, data=data, id_=id_
        )
        self.component: ComponentType = attr_convert_component_type(component)
        self.task_id: ID = ID(task_id) if task_id is not None else ID()

    @property
    def entity_identifier(self) -> ComponentEntityIdentifier:
        """
        Returns the ComponentEntityIdentifier that uniquely identifies the component to
        which the ComponentParameters relate
        """
        return ComponentEntityIdentifier(  # type: ignore
            workspace_id=self.workspace_id,
            project_id=self.project_id,
            component=self.component,
            task_id=self.task_id,
        )

    @classmethod
    def get_type(cls) -> ConfigurableParameterType:
        """
        Returns the type of the ConfigurableParameterContainer, as an instance of the
        ConfigurableParameterType Enum
        """
        return ConfigurableParameterType.COMPONENT_PARAMETERS


class NullComponentParameters(ComponentParameters, NullConfigurableParameterContainer):
    """
    This class defines an empty, unset ComponentParameters object
    """

    def __init__(self) -> None:
        ComponentParameters.__init__(
            self,
            workspace_id=ID(),
            project_id=ID(),
            task_id=ID(),
            component=ComponentType.NULL_COMPONENT,
            id_=ID(),
        )
        NullConfigurableParameterContainer.__init__(self)

    @property
    def data(self) -> ConfigurableParameters:
        """
        NullComponentParameters objects do not contain any data. The data
        property always returns an empty ConfigurableParameters instance.
        """
        return ConfigurableParameters(header="Empty parameters")  # type: ignore

    @data.setter
    def data(self, configurable_parameters: ConfigurableParameters):  # noqa: ARG002
        """
        Set the data attribute for an instance of the ComponentParameters
        """
        raise FrozenAttributeError("Unable to set data for NullComponentParameters")

    @classmethod
    def get_type(cls) -> ConfigurableParameterType:
        """
        Returns the type of the ConfigurableParameterContainer, as an instance of the
        ConfigurableParameterType Enum
        """
        return ConfigurableParameterType.NULL_PARAMETERS
