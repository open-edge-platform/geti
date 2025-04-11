"""
This module implements utility functions related configurable parameter container
classes in the SC SDK
"""

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

from sc_sdk.configuration.enums import ConfigurableParameterType
from sc_sdk.configuration.interfaces.configurable_parameters_interface import IConfigurableParameterContainer


def get_class_constructor_by_type(parameter_type: str | ConfigurableParameterType):  # noqa: ANN201
    """
    Returns the class type associated with the ConfigurableParameterType passed in
    as `parameter_type`.

    :param parameter_type: string or ConfigurableParameterType representing a certain type of configurable parameters.
    """
    parameter_classes_map = {str(cls.get_type()): cls for cls in IConfigurableParameterContainer.__subclasses__()}
    return parameter_classes_map[str(parameter_type)]
