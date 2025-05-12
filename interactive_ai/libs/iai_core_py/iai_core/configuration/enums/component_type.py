"""This module contains the ComponentType enum, which lists all configurable components in OTE"""

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from dataclasses import dataclass
from enum import Enum


@dataclass
class ComponentMetadata:
    """
    This class holds metadata about a Configurable Component in OTE. It contains the following information:

    :var per_task: True if the component operates per_task, False if it operates globally
    """

    per_task: bool


class ComponentType(Enum):
    """
    This Enum represents the type of components for which a configuration can be constructed. It is used to identify
    configurations in the ComponentConfigRepo.
    """

    # Because this Enum takes both a value and metadata, the auto() mechanism cannot be used to assign values. Hence,
    # they are assigned manually.
    NULL_COMPONENT = 0, ComponentMetadata(per_task=False)
    SUBSET_MANAGER = 1, ComponentMetadata(per_task=True)
    DATASET_COUNTER = 2, ComponentMetadata(per_task=True)
    PROJECT_ACTIVE_LEARNING = 3, ComponentMetadata(per_task=False)
    TASK_ACTIVE_LEARNING = 4, ComponentMetadata(per_task=True)
    TASK_NODE = 5, ComponentMetadata(per_task=True)
    PIPELINE_DATASET_MANAGER = 6, ComponentMetadata(per_task=False)

    def __new__(cls, value: int, metadata: ComponentMetadata):  # noqa: ARG004
        """
        Creates a new instance of the Enum. The ComponentType Enum holds both a value and metadata. In this method
        the `value` argument is parsed and assigned.
        """
        obj = object.__new__(cls)
        # Only the value is assigned here, since the _metadata_ attribute does not exists yet.
        obj._value_ = value
        return obj

    def __init__(self, value: int, metadata: ComponentMetadata) -> None:  # noqa: ARG002
        """
        Upon initialization, the Enum metadata is assigned.
        """
        # We cannot assign to _metadata_ in the __new__ method since it is not a valid attribute yet until the Enum is
        # initialized
        self._metadata_ = metadata

    @property
    def metadata(self) -> ComponentMetadata:
        """
        Returns the element category which the ConfigElementType belongs to. Categories are instances of the
        `otx.api.configuration.configuration_types.ElementCategory` Enum.
        """
        return self._metadata_

    def __str__(self) -> str:
        """
        Retrieves the string representation of an instance of the Enum
        """
        return self.name
