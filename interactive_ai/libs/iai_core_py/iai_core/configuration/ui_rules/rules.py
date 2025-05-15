# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module contains the different ui rules elements, Rule and UIRules.

They are used to define rules for disabling configuration parameters in the ui, conditional on the value of other
parameters.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

from attr import asdict, attrib, attrs, setters

from iai_core.configuration.elements.utils import attr_enum_to_str_serializer
from iai_core.configuration.enums.config_element_type import ConfigElementType

from .types import Action, Operator
from .utils import attr_convert_action, attr_convert_operator

ALLOWED_RULE_VALUE_TYPES = int | str | float | bool


@attrs(auto_attribs=True)
class Rule:
    """This class represents a `operator` applied to the `value` of the configurable parameter `parameter`.

    The parameter for which the rule should be evaluated is identified by name, or by a list of names representing the
    attribute path to the parameter in case of a nested configuration.
    """

    parameter: str | list[str]
    value: ALLOWED_RULE_VALUE_TYPES
    operator: Operator = attrib(default=Operator.EQUAL_TO, converter=attr_convert_operator)
    type: ConfigElementType = attrib(default=ConfigElementType.RULE, on_setattr=setters.frozen)

    def to_dict(self, enum_to_str: bool = True) -> dict:
        """Method to serialize a Rule instance to its dictionary representation.

        :param enum_to_str: Set to True to convert Enum instances to their string representation
        :return: dictionary representation of the Rule object for which this method is called
        """
        if enum_to_str:
            serializer: Callable | None = attr_enum_to_str_serializer
        else:
            serializer = None
        return asdict(self, value_serializer=serializer)


@attrs(auto_attribs=True)
class UIRules:
    """This class allows the combination of ExposureRules using boolean logic.

    The class can be set as an attribute of a configurable parameter. If the `rules`
    (combined according to the `operator`) evaluate to True, the corresponding`action` will be taken in the UI.

    If UIRules are nested, only the `action` of the outermost UIRule will be considered.
    """

    rules: list[Rule | UIRules] = attrib(kw_only=True)
    operator: Operator = attrib(default=Operator.AND, converter=attr_convert_operator)
    action: Action = attrib(default=Action.DISABLE_EDITING, converter=attr_convert_action)
    type: ConfigElementType = attrib(default=ConfigElementType.UI_RULES, on_setattr=setters.frozen)

    def add_rule(self, rule: Rule | UIRules) -> None:
        """Adds rule."""
        self.rules.append(rule)

    def to_dict(self, enum_to_str: bool = True) -> dict:
        """Method to serialize an UIRules instance to its dictionary representation.

        Applies recursion to convert nested rules, if applicable.

        :param enum_to_str: Set to True to convert Enum instances to their string representation
        :return: dictionary representation of the UIRules object for which this method is called
        """
        if enum_to_str:
            serializer: Callable | None = attr_enum_to_str_serializer
        else:
            serializer = None
        rules_list = []
        for rule in self.rules:
            rules_list.append(rule.to_dict(enum_to_str))
        dictionary_representation = asdict(self, value_serializer=serializer)
        dictionary_representation.update({"rules": rules_list})
        return dictionary_representation


@attrs
class NullUIRules(UIRules):
    """This class represents an empty, unset UIRules element."""

    rules: list[Rule | UIRules] = attrib(factory=list)
