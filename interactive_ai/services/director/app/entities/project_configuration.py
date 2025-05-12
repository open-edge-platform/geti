# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from pydantic import BaseModel, Field

from geti_types import ID
from iai_core.entities.persistent_entity import PersistentEntity


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
    min_images_per_label: int | None = Field(
        gt=0,
        default=None,
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

    @property
    def project_id(self) -> ID:
        """Returns the project ID of this configuration."""
        return self.id_

    task_configs: list[TaskConfig] = Field(
        title="Task configurations", description="List of configurations for all tasks in this project"
    )

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
