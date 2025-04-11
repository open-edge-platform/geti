"""This module contains the ConfigurableParameterType Enum"""

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

from enum import Enum


class ConfigurableParameterType(Enum):
    """
    This Enum contains the different possible types of configurable parameters.
    Currently, there are two different type of parameters implemented:
     Hyper parameters, which are used for model and training configuration. Examples
        are batch size, learning rate, model input size, etc.
     Component parameters, which are used to configure certain components in the system.
        Examples are whether auto training is turned on or off, the minimum number of
        annotated images required to start training, etc.
    """

    NULL_PARAMETERS = 0
    HYPER_PARAMETERS = 1
    COMPONENT_PARAMETERS = 2

    def __str__(self) -> str:
        """
        Retrieves the string representation of an instance of the Enum
        """
        return self.name
