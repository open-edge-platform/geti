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


"""
This module contains the configurable parameters for dataset management
"""

import attr

from sc_sdk.configuration.elements.configurable_parameters import ConfigurableParameters

from .primitive_parameters import configurable_integer, string_attribute


@attr.s
class DatasetManagementConfig(ConfigurableParameters):
    """
    Class that holds the configurable parameters for dataset management
    """

    header = string_attribute("Dataset management")
    description = string_attribute("Specify parameters to control how datasets are managed in the system.")

    minimum_annotation_size = configurable_integer(
        header="Minimum annotation size",
        description="Minimum size of a shape in pixels. Any shape smaller than this will be ignored during \
        training. Setting this to -1 disables the setting.",
        max_value=1_000_000,
        min_value=-1,
        default_value=-1,
    )

    maximum_number_of_annotations = configurable_integer(
        header="Maximum number of shapes per annotation",
        description="The maximum number of shapes that can be in an annotation. Any annotations with "
        "more shapes than this number will be ignored during training. Setting this to -1 disables the "
        "setting.",
        default_value=-1,
        min_value=-1,
        max_value=10000,
    )
