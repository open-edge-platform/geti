"""This module contains the ConfigurableParameterType Enum"""

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
