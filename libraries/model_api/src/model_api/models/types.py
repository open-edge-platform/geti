#
# Copyright (C) 2020-2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#

from __future__ import annotations

from typing import Any


class ConfigurableValueError(ValueError):
    def __init__(self, message, prefix=None):
        self.message = f"{prefix}: {message}" if prefix else message
        super().__init__(self.message)


class BaseValue:
    def __init__(
        self,
        description: str = "No description available",
        default_value: Any | None = None,
    ) -> None:
        self.default_value = default_value
        self.description = description

    def update_default_value(self, default_value):
        self.default_value = default_value

    def validate(self, value):
        return []

    def get_value(self, value):
        errors = self.validate(value)
        if len(errors) == 0:
            return value if value is not None else self.default_value
        msg = "Encountered errors during validation."
        raise ValueError(msg)

    def build_error(self) -> None:
        pass

    def __str__(self) -> str:
        info = self.description
        if self.default_value:
            info += f"\nThe default value is '{self.default_value}'"
        return info


class NumericalValue(BaseValue):
    def __init__(
        self,
        value_type: Any = float,
        choices: tuple[Any, ...] = (),
        min: Any | None = None,
        max: Any | None = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.choices = choices
        self.min = min
        self.max = max
        self.value_type = value_type

    def from_str(self, value: str) -> Any:
        if not value and self.default_value is not None:
            return self.default_value
        if not value and self.default_value is None:
            return None
        if value == "None":
            return None
        return self.value_type(value)

    def validate(self, value):
        errors = super().validate(value)
        if not value:
            return errors
        if not isinstance(value, self.value_type):
            errors.append(
                ConfigurableValueError(
                    f"Incorrect value type {type(value)}: should be {self.value_type}",
                ),
            )
            return errors
        if len(self.choices) and value not in self.choices:
            errors.append(
                ConfigurableValueError(
                    f"Incorrect value {value}: out of allowable list - {self.choices}",
                ),
            )
        if self.min is not None and value < self.min:
            errors.append(
                ConfigurableValueError(
                    f"Incorrect value {value}: less than minimum allowable {self.min}",
                ),
            )
        if self.max is not None and value > self.max:
            errors.append(
                ConfigurableValueError(
                    f"Incorrect value {value}: bigger than maximum allowable {self.min}",
                ),
            )
        return errors

    def __str__(self) -> str:
        info = super().__str__()
        info += f"\nAppropriate type is {self.value_type}"
        if self.choices:
            info += f"\nAppropriate values are {self.choices}"
        return info


class StringValue(BaseValue):
    def __init__(
        self,
        choices: tuple[Any, ...] = (),
        description: str = "No description available",
        default_value: str = "",
    ) -> None:
        super().__init__(description, default_value)
        self.choices = choices
        for choice in self.choices:
            if not isinstance(choice, str):
                msg = f"Incorrect option in choice list - {choice}."
                raise ValueError(msg)

    def from_str(self, value: str) -> str | None:
        if value == "None":
            return None
        return value

    def validate(self, value):
        errors = super().validate(value)
        if not value:
            return errors
        if not isinstance(value, str):
            errors.append(
                ConfigurableValueError(
                    f'Incorrect value type {type(value)}: should be "str"',
                ),
            )
        if len(self.choices) > 0 and value not in self.choices:
            errors.append(
                ConfigurableValueError(
                    f"Incorrect value {value}: out of allowable list - {self.choices}",
                ),
            )
        return errors

    def __str__(self) -> str:
        info = super().__str__()
        info += "\nAppropriate type is str"
        if self.choices:
            info += f"\nAppropriate values are {self.choices}"

        return info


class BooleanValue(BaseValue):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def from_str(self, value: str) -> bool | None:
        if value == "None":
            return None
        return value == "YES" or value == "True"

    def validate(self, value):
        errors = super().validate(value)
        if not value:
            return errors
        if not isinstance(value, bool):
            errors.append(
                ConfigurableValueError(
                    f'Incorrect value type - {type(value)}: should be "bool"',
                ),
            )
        return errors


class ListValue(BaseValue):
    def __init__(
        self,
        value_type: Any | None = None,
        description: str = "No description available",
        default_value: list[Any] = [],
    ) -> None:
        super().__init__(description, default_value)
        self.value_type = value_type

    def from_str(self, value: str) -> list[Any] | None:
        if value == "None":
            return None
        if self.value_type is str or self.value_type is StringValue:
            return value.split()
        try:
            floats = [float(i) for i in value.split()]
            try:
                ints = [int(i) for i in value.split()]
            except ValueError:
                ints = []
            if ints == floats:
                return ints
            return floats
        except ValueError:
            return value.split()

    def validate(self, value):
        errors = super().validate(value)
        if not value:
            return errors
        if not isinstance(value, (tuple, list)):
            errors.append(
                ConfigurableValueError(
                    f"Incorrect value type - {type(value)}: should be list or tuple",
                ),
            )
        if self.value_type:
            if isinstance(self.value_type, BaseValue):
                for i, element in enumerate(value):
                    temp_errors = self.value_type.validate(element)
                    if len(temp_errors) > 0:
                        errors.extend(
                            [
                                ConfigurableValueError(
                                    f"Incorrect #{i} element of the list",
                                ),
                                *temp_errors,
                            ],
                        )
            else:
                for i, element in enumerate(value):
                    if not isinstance(element, self.value_type):
                        errors.append(
                            ConfigurableValueError(
                                f"Incorrect #{i} element type - {type(element)}: should be {self.value_type}",
                            ),
                        )
        return errors


class DictValue(BaseValue):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def from_str(self, value: str):
        raise NotImplementedError

    def validate(self, value):
        errors = super().validate(value)
        if not value:
            return errors
        if not isinstance(value, dict):
            errors.append(
                ConfigurableValueError(
                    f'Incorrect value type - {type(value)}: should be "dict"',
                ),
            )
        return errors


def get_python_type(base_value: BaseValue) -> type | type[Any]:
    """Helper function that extracts the corresponding Python type from a BaseValue instance.

    Args:
        base_value: An instance of BaseValue or its subclass

    Returns:
        The corresponding Python type (int, float, bool, str, list, dict, or object)
    """
    if isinstance(base_value, NumericalValue):
        return base_value.value_type if hasattr(base_value, "value_type") else float
    if isinstance(base_value, BooleanValue):
        return bool
    if isinstance(base_value, StringValue):
        return str
    if isinstance(base_value, ListValue):
        return list
    if isinstance(base_value, DictValue):
        return dict

    return object
