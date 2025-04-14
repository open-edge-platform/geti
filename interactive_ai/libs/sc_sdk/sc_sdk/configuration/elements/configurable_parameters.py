# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module contains the base class to define ConfigurableParameters within OTX."""

from __future__ import annotations

from attr import attrib, attrs, setters

from sc_sdk.configuration.enums.config_element_type import ConfigElementType

from .parameter_group import ParameterGroup
from .utils import convert_string_to_id
from geti_types import ID


@attrs(auto_attribs=True, order=False, eq=False)
class ConfigurableParameters(ParameterGroup):
    """Base class representing a generic set of configurable parameters.

    A ConfigurableParameters instance is essentially a parameter group with an id
    attached to it, so that it can be uniquely identified in the repositories.

    Attributes:
        id (ID): ID that uniquely identifies the ConfigurableParameters
        type (ConfigElementType): Type of the ConfigurableParameters
    """

    id: ID = attrib(default=ID(), kw_only=True, converter=convert_string_to_id)
    type: ConfigElementType = attrib(
        default=ConfigElementType.CONFIGURABLE_PARAMETERS,
        repr=False,
        init=False,
        on_setattr=setters.frozen,
    )
