# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module contains the definition for the `validate` function within the configuration helper.

This function can be used to validate the values of a OTX configuration object, checking that each of the parameter
values in the configuration are within their allowed bounds or options.
"""

import attr

from iai_core.configuration.elements.parameter_group import ParameterGroup


def _validate_inner(config: ParameterGroup):
    """Recursive method that performs validation on all parameters within a parameter group.

    Uses recursion to validate parameters living inside nested groups.
    """
    attr.validate(config)
    if config.groups:
        for group_name in config.groups:
            group = getattr(config, group_name)
            _validate_inner(group)


def validate(config: ParameterGroup) -> bool:
    """Validate a configuration object.

    :param config: Configuration to validate
    :return: True if config is valid
    """
    _validate_inner(config)
    return True
