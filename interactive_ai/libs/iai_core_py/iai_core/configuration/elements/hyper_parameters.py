"""This module implements the HyperParameter class"""

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from typing import TypeVar

from attr.exceptions import FrozenAttributeError

from iai_core.configuration.enums.configurable_parameter_type import ConfigurableParameterType
from iai_core.configuration.interfaces.configurable_parameters_interface import (
    IConfigurableParameterContainer,
    NullConfigurableParameterContainer,
)

from .configurable_parameters import ConfigurableParameters
from .entity_identifiers import ModelEntityIdentifier
from geti_types import ID

TConfig = TypeVar("TConfig", bound=ConfigurableParameters)


class HyperParameters(IConfigurableParameterContainer[TConfig]):
    """
    This class contains the configurable hyper parameters for a model.

    This class accepts a type parameter TConfig, which can be used to specify the type
    of the ConfigurableParameters data it is expected to hold.

    :param id_: ID of the HyperParameters
    :param workspace_id: ID of the workspace containing the HyperParameters
    :param project_id: ID of the project containing the HyperParameters
    :param model_storage_id: ID of the model storage that contains the model to which
        the HyperParameters relate
    :param data: ParameterGroup (can be nested) containing the schema and values for
        the actual hyper parameters. `data` is optional and can be set after
        initialization as well
    :param single_use: If True, the validity of these hyper-parameters is limited to a single
        specific job run, they do not apply to subsequent jobs in the same model storage.
        If False, then these parameters will be used by default by all the jobs in the same model storage.
    """

    def __init__(
        self,
        id_: ID,
        workspace_id: ID,
        project_id: ID,
        model_storage_id: ID,
        data: TConfig | None = None,
        single_use: bool = False,
    ) -> None:
        IConfigurableParameterContainer.__init__(
            self, workspace_id=workspace_id, project_id=project_id, data=data, id_=id_
        )
        self.model_storage_id = model_storage_id
        self.single_use = single_use

    @property
    def entity_identifier(self) -> ModelEntityIdentifier:
        """
        Returns the ModelEntityIdentifier that uniquely identifies the model to which
        the HyperParameters relate
        """
        return ModelEntityIdentifier(  # type: ignore
            workspace_id=self.workspace_id,
            project_id=self.project_id,
            model_storage_id=self.model_storage_id,
        )

    @classmethod
    def get_type(cls) -> ConfigurableParameterType:
        """
        Returns the type of the ConfigurableParameterContainer, as an instance of the
        ConfigurableParameterType Enum
        """
        return ConfigurableParameterType.HYPER_PARAMETERS


class NullHyperParameters(HyperParameters, NullConfigurableParameterContainer):
    """
    This class defines an empty, unset HyperParameters object
    """

    def __init__(self) -> None:
        super().__init__(workspace_id=ID(), project_id=ID(), model_storage_id=ID(), id_=ID())

    @property
    def data(self) -> ConfigurableParameters:
        """
        NullHyperParameters objects do not contain any data. The data
        property always returns an empty ConfigurableParameters instance.
        """
        return ConfigurableParameters(header="Empty parameters")  # type: ignore

    @data.setter
    def data(self, configurable_parameters: ConfigurableParameters):  # noqa: ARG002
        """
        Set the data attribute for an instance of the HyperParameters
        """
        raise FrozenAttributeError("Unable to set data for NullHyperParameters")

    @classmethod
    def get_type(cls) -> ConfigurableParameterType:
        """
        Returns the type of the ConfigurableParameterContainer, as an instance of the
        ConfigurableParameterType Enum
        """
        return ConfigurableParameterType.NULL_PARAMETERS
