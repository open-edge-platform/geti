# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module contains utility functions for use in defining ui rules."""

from sc_sdk.configuration.ui_rules.types import Action, Operator


def attr_convert_operator(operator: str | Operator) -> Operator:
    """This function converts an input operator to the correct instance of the Operator Enum.

    It is used when loading a Rule element from a yaml file.
    """
    if isinstance(operator, str):
        return Operator[operator]
    return operator


def attr_convert_action(action: str | Action) -> Action:
    """This function converts an input action to the correct instance of the Action Enum.

    It is used when loading a Rule element from a yaml file.
    """
    if isinstance(action, str):
        return Action[action]
    return action
