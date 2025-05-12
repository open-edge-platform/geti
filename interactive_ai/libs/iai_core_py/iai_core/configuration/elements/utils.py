# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
This module implements utility functions for use with configurable parameter elements in the SC SDK
"""

from collections.abc import Callable
from enum import Enum
from typing import TypeVar

from attr import Attribute

from iai_core.configuration.enums.component_type import ComponentType
from iai_core.configuration.enums.utils import get_enum_names

from .configurable_enum import ConfigurableEnum
from .parameter_group import ParameterGroup
from geti_types import ID

NumericTypeVar = TypeVar("NumericTypeVar", int, float)
SelectableTypeVar = TypeVar("SelectableTypeVar", float, str)
ConfigurableEnumTypeVar = TypeVar("ConfigurableEnumTypeVar", bound=ConfigurableEnum)


def attr_enum_to_str_serializer(
    instance: object,  # noqa: ARG001
    attribute: Attribute,  # noqa: ARG001
    value: Enum | str,
) -> str:
    """This function converts Enums to their string representation.

    It is used when converting between yaml and python object representation of the configuration.
    The function signature matches what is expected by the `attr.asdict` value_serializer argument.

    :param instance: (Unused) The instance of the class that the attribute is attached to.
    :param attribute: (unused) The attribute that is being serialized.
    :param value: The value to serialize.
    :return: The string representation of the value.
    """
    if isinstance(value, Enum):
        return str(value)
    return value


def _convert_enum_selectable_value(
    value: str | ConfigurableEnumTypeVar,
    enum_class: type[ConfigurableEnumTypeVar],
) -> ConfigurableEnumTypeVar:
    """Helper function that converts the input value to an instance of the correct ConfigurableEnum.

    :param value: input value to convert
    :param enum_class: Type of the Enum to convert to
    :return: Instance of the correct ConfigurableEnum
    """
    if isinstance(value, str):
        try:
            enum_value = enum_class(value)
        except ValueError as ex:
            raise ValueError(
                f"The value {value} is an invalid option for {enum_class.__name__}. Valid options are:"
                f" {enum_class.get_values()}"
            ) from ex
        return enum_value
    return value


def construct_attr_enum_selectable_converter(
    default_value: ConfigurableEnumTypeVar,
) -> Callable[[str | ConfigurableEnumTypeVar], ConfigurableEnumTypeVar]:
    """This function converts an input value to the correct instance of the ConfigurableEnum.

    It is used when initializing a selectable parameter.

    :param default_value: Default value for the selectable
    :return: Function that converts an input value to the correct instance of the ConfigurableEnum.
    """
    enum_class = type(default_value)

    def attr_convert_enum_selectable_value(value: str | ConfigurableEnumTypeVar) -> ConfigurableEnumTypeVar:
        """Function that converts an input value to an instance of the appropriate ConfigurableEnum.

        Can be used as a `converter` for attrs.Attributes of type ConfigurableEnum.

        :param value: Value to convert to ConfigurableEnum instance
        :return: Instance of the correct ConfigurableEnum
        """
        return _convert_enum_selectable_value(value, enum_class=enum_class)

    return attr_convert_enum_selectable_value


def construct_attr_enum_selectable_onsetattr(
    default_value: ConfigurableEnumTypeVar,
) -> Callable[[ParameterGroup, Attribute, str | ConfigurableEnumTypeVar], ConfigurableEnumTypeVar]:
    """This function converts an input value to the correct instance of the ConfigurableEnum.

    It is used when setting a value for a selectable parameter.

    :param default_value: Default value for the enum_selectable.
    :return: Function that converts an input value to the correct instance of the ConfigurableEnum.
    """
    enum_class = type(default_value)

    def attr_convert_enum_selectable_value(
        instance: ParameterGroup,  # noqa: ARG001
        attribute: Attribute,  # noqa: ARG001
        value: str | ConfigurableEnumTypeVar,
    ) -> ConfigurableEnumTypeVar:
        """Function that converts an input value to an instance of the appropriate ConfigurableEnum.

        Can be used with the `on_setattr` hook of the attrs package.
        """
        return _convert_enum_selectable_value(value, enum_class=enum_class)

    return attr_convert_enum_selectable_value


def construct_attr_value_validator(
    min_value: NumericTypeVar, max_value: NumericTypeVar
) -> Callable[[ParameterGroup, Attribute, NumericTypeVar], None]:
    """Constructs a validator function that is used in the attribute validation of numeric configurable parameters.

    :param min_value: Minimum value for the parameter
    :param max_value: Maximum value for the parameter
    :return: Function that validates the input value.
    """

    def attr_validate_value(instance: ParameterGroup, attribute: Attribute, value: NumericTypeVar):  # noqa: ARG001
        """This function is used to validate values for numeric ConfigurableParameters."""
        if not min_value <= value <= max_value:
            raise ValueError(f"Invalid value set for {attribute.name}: {value} is out of bounds.")

    return attr_validate_value


def construct_attr_selectable_validator(
    options: list[SelectableTypeVar],
) -> Callable[[ParameterGroup, Attribute, SelectableTypeVar], None]:
    """Constructs a validator function that is used in the attribute validation of selectable configurable parameters.

    :param options: List of valid options for the parameter.
    :return: Function that validates the input value.
    """

    def attr_validate_selectable(instance: ParameterGroup, attribute: Attribute, value: SelectableTypeVar):  # noqa: ARG001
        """This function is used to validate values for selectable ConfigurableParameters."""
        if value not in options:
            raise ValueError(
                f"Invalid value set for {attribute.name}: {value} is not a valid option for this parameter."
            )

    return attr_validate_selectable


def convert_string_to_id(id_string: str | ID | None) -> ID:
    """This function converts an input string representing an ID into an OTX ID object.

    Inputs that are already in the form of an ID are left untouched.

    :param id_string: string, ID or None object that should be converted to an ID.
    :return: the input as an instance of ID
    """
    if id_string is None:
        output_id = ID()
    elif isinstance(id_string, str):
        output_id = ID(id_string)
    else:
        output_id = id_string
    return output_id


def attr_strict_int_validator(
    instance: ParameterGroup,  # noqa: ARG001
    attribute: Attribute,
    value: int,
) -> None:
    """Validates that the value set for an attribute is an integer.

    :param instance: (Unused) ParameterGroup to which the attribute belongs
    :param attribute: Attribute for which to validate the value
    :param value: Value to validate
    :raises: TypeError if the value passed to the validator is not an integer
    """
    is_strict_int = isinstance(value, int) and not isinstance(value, bool)
    if not is_strict_int:
        raise TypeError(f"Invalid argument type for {attribute.name}: {value} is not of type 'int'")


def _validate_and_convert_float(value: float) -> float | None:
    """Validate that a value is a float, or a number that can be converted to a float.

    If the value is valid, this method will return the value as float. Otherwise, this
    method returns None

    :param value: Value to validate and convert
    :return: The value as a float, or None if the value is not valid
    """
    valid = True
    if not isinstance(value, float | int):
        valid = False
    if isinstance(value, bool):
        valid = False
    if valid:
        return float(value)
    return None


def attr_strict_float_on_setattr(
    instance: ParameterGroup,  # noqa: ARG001
    attribute: Attribute,
    value: float,
) -> float:
    """Validate that the value set for an attribute is a float, or a number that can be converted to a float.

    :param instance: ParameterGroup to which the attribute belongs
    :param attribute: Attribute for which to validate the value
    :param value: Value to validate
    :raises TypeError: if the value passed to the validator is not a float or number
    :return: The value as a float
    """
    float_value = _validate_and_convert_float(value)
    if float_value is None:
        raise TypeError(f"Invalid argument type for {attribute.name}: {value} is not of type 'float'")
    return float_value


def attr_strict_float_converter(value: float) -> float:
    """Converts a value to float.

    :param value: value to convert
    :raises TypeError: if value cannot be converted to float
    :return: value as float
    """
    float_value = _validate_and_convert_float(value)
    if float_value is None:
        raise TypeError(f"Invalid value passed for parameter. Value {value} of type {type(value)} is not a float.")
    return float_value


def attr_convert_component_type(component_type: str | ComponentType) -> ComponentType:
    """
    This function converts an input component type to the correct instance of the ComponentType Enum. It is used when
    loading a component configuration from a yaml file.
    """
    if isinstance(component_type, str):
        try:
            _type = ComponentType[component_type]  # type: ignore
            # Mypy doesn't recognize that we're indexing the Enum instead of giving a
            # type argument
        except KeyError:
            raise ValueError(
                f"Type {component_type} is an invalid name for ComponentType. Valid component types are:"
                f" {get_enum_names(ComponentType)}"
            )
        return _type
    return component_type
