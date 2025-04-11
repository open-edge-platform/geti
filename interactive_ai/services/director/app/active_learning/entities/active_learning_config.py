# INTEL CONFIDENTIAL
#
# Copyright (C) 2022 Intel Corporation
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

"""This module implements the Active Learning configuration"""

from typing import TypeVar

import attr

from sc_sdk.configuration.elements.configurable_enum import ConfigurableEnum
from sc_sdk.configuration.elements.configurable_parameters import ConfigurableParameters
from sc_sdk.configuration.elements.primitive_parameters import configurable_integer, selectable, string_attribute


class ActiveScoreReductionFunction(ConfigurableEnum):
    """Method used to aggregate multiple active score values to a single one."""

    MIN = "min"
    MEAN = "mean"
    MAX = "max"


@attr.s
class ActiveLearningProjectConfig(ConfigurableParameters):
    """Project-level configurable parameters for Active Learning"""

    header = string_attribute("Active Learning")
    description = string_attribute("Specify the project-level configuration for active learning.")

    max_unseen_media = configurable_integer(
        header="Number of images analysed after training for active learning",
        description="Number of images analysed after training for active learning",
        default_value=500,
        min_value=10,
        max_value=10000,
    )

    inter_task_reduce_fn = selectable(
        default_value=ActiveScoreReductionFunction.MEAN,
        header="Inter-task scores reduction function",
        description="Function to aggregate the active scores of a media across the tasks",
    )


@attr.s
class ActiveLearningTaskConfig(ConfigurableParameters):
    """Task-level configurable parameters for Active Learning"""

    header = string_attribute("Active Learning")
    description = string_attribute("Specify the task-level configuration for active learning.")

    intra_task_reduce_fn = selectable(
        default_value=ActiveScoreReductionFunction.MEAN,
        header="Intra-task scores reduction function",
        description="Function to aggregate the active scores of a media within a task",
    )


TActiveLearningConfig = TypeVar(
    "TActiveLearningConfig",
    bound=ActiveLearningProjectConfig | ActiveLearningTaskConfig,
)
