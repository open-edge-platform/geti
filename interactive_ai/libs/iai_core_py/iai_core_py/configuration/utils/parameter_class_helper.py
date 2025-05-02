"""
This module implements utility functions related configurable parameter container
classes in the SC SDK
"""

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from iai_core_py.configuration.enums import ConfigurableParameterType
from iai_core_py.configuration.interfaces.configurable_parameters_interface import IConfigurableParameterContainer


def get_class_constructor_by_type(parameter_type: str | ConfigurableParameterType):  # noqa: ANN201
    """
    Returns the class type associated with the ConfigurableParameterType passed in
    as `parameter_type`.

    :param parameter_type: string or ConfigurableParameterType representing a certain type of configurable parameters.
    """
    parameter_classes_map = {str(cls.get_type()): cls for cls in IConfigurableParameterContainer.__subclasses__()}
    return parameter_classes_map[str(parameter_type)]
