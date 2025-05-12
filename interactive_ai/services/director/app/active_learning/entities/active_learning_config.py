# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
#

"""This module implements the Active Learning configuration"""

from typing import TypeVar

import attr

from iai_core.configuration.elements.configurable_enum import ConfigurableEnum
from iai_core.configuration.elements.configurable_parameters import ConfigurableParameters
from iai_core.configuration.elements.primitive_parameters import configurable_integer, selectable, string_attribute


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
