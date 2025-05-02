"""This module implements the TaskNodeConfig and AnomalyTaskNodeConfig classes"""

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
#

import attr

from iai_core.configuration.elements.configurable_parameters import ConfigurableParameters
from iai_core.configuration.elements.primitive_parameters import configurable_boolean, string_attribute
from iai_core.configuration.enums.model_lifecycle import ModelLifecycle


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
