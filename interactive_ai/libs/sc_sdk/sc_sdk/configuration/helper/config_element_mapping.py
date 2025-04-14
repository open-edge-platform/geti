# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module contains mappings from ConfigElementType names to the appropriate constructor classes or functions.

Currently three different mappings are defined: `PrimitiveElementMapping` representing the different base parameter
types, `GroupElementMapping` representing the different configuration groups and `RuleElementMapping` representing the
different ui exposure logic classes
"""

from enum import Enum
from functools import partial

from sc_sdk.configuration.elements.configurable_parameters import ConfigurableParameters
from sc_sdk.configuration.elements.parameter_group import ParameterGroup
from sc_sdk.configuration.elements.primitive_parameters import (
    configurable_boolean,
    configurable_float,
    configurable_integer,
    float_selectable,
    selectable,
)
from sc_sdk.configuration.ui_rules.rules import Rule, UIRules


class PrimitiveElementMapping(Enum):
    """This Enum represents the mapping from primitive configuration element names to their constructors.

    It is only used by the ConfigHelper to be able to reconstruct a configuration object out of a dictionary
    or yaml string.
    """

    INTEGER = partial(configurable_integer)
    FLOAT = partial(configurable_float)
    BOOLEAN = partial(configurable_boolean)
    FLOAT_SELECTABLE = partial(float_selectable)
    SELECTABLE = partial(selectable)

    def __str__(self):
        """Retrieves the string representation of an instance of the Enum."""
        return self.name


class GroupElementMapping(Enum):
    """This Enum represents the mapping from configuration group names to their constructors.

    It is only used by the ConfigHelper to be able to reconstruct a configuration object out of a dictionary or yaml
    string.
    """

    PARAMETER_GROUP = ParameterGroup
    CONFIGURABLE_PARAMETERS = ConfigurableParameters

    def __str__(self):
        """Retrieves the string representation of an instance of the Enum."""
        return self.name


class RuleElementMapping(Enum):
    """This Enum represents the mapping from configuration logic names to their constructors.

    It is only used by the ConfigHelper to be able to reconstruct a configuration object out of a dictionary or yaml
    string.
    """

    RULE = Rule
    UI_RULES = UIRules

    def __str__(self):
        """Retrieves the string representation of an instance of the Enum."""
        return self.name
