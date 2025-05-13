# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from pydantic import BaseModel, Field


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


class ProjectConfiguration(BaseModel):
    """Configurable parameters for a project."""

    task_configs: list[TaskConfig] = Field(
        title="Task configurations", description="List of configurations for all tasks in this project"
    )
