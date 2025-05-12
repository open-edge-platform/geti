# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
This module contains a register of all configurable components.
"""

from enum import Enum

from active_learning.entities import ActiveLearningProjectConfig, ActiveLearningTaskConfig
from coordination.configuration_manager.task_node_config import AnomalyTaskNodeConfig, TaskNodeConfig
from coordination.dataset_manager.dataset_counter_config import (
    AnomalyDatasetCounterConfig,
    ClassificationDatasetCounterConfig,
    DatasetCounterConfig,
    KeypointDetectionCounterConfig,
)
from coordination.dataset_manager.subset_manager_config import AnomalySubsetManagerConfig, SubsetManagerConfig

from .component_register_entry import ComponentRegisterEntry
from iai_core.configuration.elements.dataset_manager_parameters import DatasetManagementConfig


class ConfigurableComponentRegister(Enum):
    """
    This Enum contains a registry of all configurable components. It maps the names of the components to their
    respective configuration types.

    Some task specific components also have alternative configurable parameters defined
    for specific task types, such as classification or anomaly tasks. Such
    alternatives can be specified in the ComponentRegisterEntry for a component
    """

    PROJECT_ACTIVE_LEARNING = ComponentRegisterEntry(default_type=ActiveLearningProjectConfig)
    TASK_ACTIVE_LEARNING = ComponentRegisterEntry(default_type=ActiveLearningTaskConfig)
    DATASET_COUNTER = ComponentRegisterEntry(
        default_type=DatasetCounterConfig,
        classification_type=ClassificationDatasetCounterConfig,
        anomaly_type=AnomalyDatasetCounterConfig,
        keypoint_type=KeypointDetectionCounterConfig,
    )
    SUBSET_MANAGER = ComponentRegisterEntry(default_type=SubsetManagerConfig, anomaly_type=AnomalySubsetManagerConfig)
    TASK_NODE = ComponentRegisterEntry(default_type=TaskNodeConfig, anomaly_type=AnomalyTaskNodeConfig)
    PIPELINE_DATASET_MANAGER = ComponentRegisterEntry(default_type=DatasetManagementConfig)

    def __str__(self) -> str:
        """
        Retrieves the string representation of an instance of the Enum
        """
        return self.name
