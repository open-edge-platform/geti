"""This module implements enums related to configurable parameters in the SC SDK"""

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

from .component_type import ComponentType
from .config_element_type import ConfigElementType
from .configurable_parameter_type import ConfigurableParameterType
from .model_lifecycle import ModelLifecycle

__all__ = ["ComponentType", "ConfigElementType", "ConfigurableParameterType", "ModelLifecycle"]
