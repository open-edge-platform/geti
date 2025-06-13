# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from geti_types import ID, PersistentEntity
from pydantic import BaseModel, Field, model_validator

from .utils import partial_model


class TrainConstraints(BaseModel):
    """Constraints applied for model training."""

    min_images_per_label: int = Field(
        ge=0,
        default=0,
        title="Minimum number of images per label",
        description="Minimum number of images that must be present for each label to train",
    )


class AutoTrainingParameters(BaseModel):
    """Configuration for auto-training feature."""

    enable: bool = Field(
        default=True, title="Enable auto training", description="Whether automatic training is enabled for this task"
    )
    enable_dynamic_required_annotations: bool = Field(
        default=False,
        title="Enable dynamic required annotations",
        description="Whether to dynamically adjust the number of required annotations",
    )
    min_images_per_label: int = Field(
        ge=0,
        default=0,
        title="Minimum images per label",
        description="Minimum number of images needed for each label to trigger auto-training",
    )


class TrainingParameters(BaseModel):
    """Parameters that control the training process."""

    constraints: TrainConstraints = Field(
        title="Training constraints", description="Constraints that must be satisfied for training to proceed"
    )


class TaskConfig(BaseModel):
    """Configuration for a specific task within a project."""

    task_id: str = Field(title="Task ID", description="Unique identifier for the task")
    training: TrainingParameters = Field(
        title="Training parameters", description="Parameters controlling the training process"
    )
    auto_training: AutoTrainingParameters = Field(
        title="Auto-training parameters", description="Parameters controlling auto-training"
    )

    @model_validator(mode="after")
    def task_id_not_empty(self) -> "TaskConfig":
        if not self.task_id:
            raise ValueError("Task ID must be provided as part of the task configuration and cannot be empty.")
        return self


class ProjectConfiguration(BaseModel, PersistentEntity):
    """
    Configurable parameters for a project.

    Each project has exactly one configuration entity. The ID of this entity
    matches the project ID, as there is a one-to-one relationship between
    projects and their configurations.
    """

    def __init__(self, project_id: ID, ephemeral: bool = True, **data):
        # first initialize the Pydantic BaseModel with all arguments
        BaseModel.__init__(self, **data)

        # then initialize PersistentEntity with id and ephemeral parameters
        PersistentEntity.__init__(self, id_=project_id, ephemeral=ephemeral)

        self._task_idx_mapping = {task_config.task_id: i for i, task_config in enumerate(self.task_configs)}

    @property
    def project_id(self) -> ID:
        """Returns the project ID of this configuration."""
        return self.id_

    task_configs: list[TaskConfig] = Field(
        title="Task configurations", description="List of configurations for all tasks in this project"
    )

    def get_task_config(self, task_id: str) -> TaskConfig:
        """
        Retrieves the configuration for a specific task by its ID.

        :param task_id: The ID of the task to retrieve the configuration for.
        :return: The TaskConfig for the specified task, or None if not found.
        """
        if task_id not in self._task_idx_mapping:
            raise ValueError(f"Task configuration with ID {task_id} not found.")

        idx = self._task_idx_mapping[task_id]
        return self.task_configs[idx]

    def update_task_config(self, task_config: TaskConfig) -> None:
        """
        Updates an existing task configuration in-place with the provided configuration.

        This method modifies the project configuration directly by replacing the
        task configuration for the specified task ID with the new configuration.

        :param task_config: The new task configuration to update with
        :raises ValueError: If a task configuration with the specified task_id does not exist
        """
        if task_config.task_id not in self._task_idx_mapping:
            raise ValueError(f"Task configuration with ID {task_config.task_id} not found.")

        idx = self._task_idx_mapping[task_config.task_id]
        self.task_configs[idx] = task_config

    def __eq__(self, other: object) -> bool:
        """
        Compares two ProjectConfiguration instances.

        Checks if both objects have the same ID and task configurations.
        """
        if not isinstance(other, ProjectConfiguration):
            return False

        # Compare IDs
        if self.id_ != other.id_:
            return False

        # Compare task configurations
        return self.task_configs == other.task_configs


class NullProjectConfiguration(ProjectConfiguration):
    """
    Null object implementation for ProjectConfiguration.

    This class implements the Null Object Pattern to represent a "non-existent" project configuration.
    It is used when a project configuration cannot be found.
    """

    def __init__(self) -> None:
        ProjectConfiguration.__init__(
            self,
            project_id=ID(),
            task_configs=[],
            ephemeral=True,
        )


@partial_model
class PartialTaskConfig(TaskConfig):
    """
    A partial version of `TaskConfig` where all fields are optional.

    This class is useful for update operations or PATCH endpoints, allowing clients
    to provide only the fields they wish to modify, while leaving others unset.
    """


@partial_model
class PartialProjectConfiguration(BaseModel):
    """
    A partial version of `ProjectConfiguration` where all fields are optional.

    This class is useful for update operations or PATCH endpoints, allowing clients
    to provide only the fields they wish to modify, while leaving others unset.
    """

    task_configs: list[PartialTaskConfig] = Field(
        title="Task configurations", description="List of configurations for all tasks in this project"
    )
