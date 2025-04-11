"""This module implements the TaskNodeConfig and AnomalyTaskNodeConfig classes"""

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
#

import attr

from sc_sdk.configuration.elements.configurable_parameters import ConfigurableParameters
from sc_sdk.configuration.elements.primitive_parameters import configurable_boolean, string_attribute
from sc_sdk.configuration.enums.model_lifecycle import ModelLifecycle


@attr.s
class TaskNodeConfig(ConfigurableParameters):
    """
    Class that holds the configurable parameters for a generic Task Node.
    """

    # Header is required for all ConfigurableParameters
    header = string_attribute("General")
    description = string_attribute("General settings for a task.")

    auto_training = configurable_boolean(
        header="Auto-training",
        description="Enable to allow the task to start training automatically when it is ready to train.",
        default_value=True,
        affects_outcome_of=ModelLifecycle.NONE,
    )


@attr.s
class AnomalyTaskNodeConfig(TaskNodeConfig):
    """
    Class that holds the configurable parameters for an Anomaly task node.
    """

    auto_training = configurable_boolean(
        header="Auto-training",
        description="Enable to allow the task to start training automatically when it is ready to train.",
        default_value=False,
        affects_outcome_of=ModelLifecycle.NONE,
    )
