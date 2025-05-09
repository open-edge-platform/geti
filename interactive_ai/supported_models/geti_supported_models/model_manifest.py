# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from enum import Enum, auto

from pydantic import BaseModel, Field

from .hyperparameters import (
    AugmentationParameters,
    DatasetPreparationParameters,
    EvaluationParameters,
    Hyperparameters,
    TrainingHyperParameters,
)


class ModelStats(BaseModel):
    """Information about a machine learning model."""

    gigaflops: float = Field(
        gt=0, title="Gigaflops", description="Billions of floating-point operations per second required by the model"
    )
    trainable_parameters: int = Field(
        gt=0, title="Trainable parameters", description="Number of trainable parameters in the model"
    )


class GPUMaker(str, Enum):
    """GPU maker names."""

    NVIDIA = "nvidia"
    INTEL = "intel"

    def __str__(self) -> str:
        """Returns the name of the GPU maker."""
        return str(self.name)


class ModelManifestDeprecationStatus(str, Enum):
    """Status of a model architecture with respect to the deprecation process."""

    ACTIVE = "active"  # Model architecture is fully supported, models can be trained
    DEPRECATED = "deprecated"  # Model architecture is deprecated, models can be still viewed and trained but it's discouraged
    OBSOLETE = "obsolete"  # Model architecture is no longer supported, models can be still viewed but not trained

    def __str__(self) -> str:
        """Returns the name of the model status."""
        return str(self.name)


class ModelManifest(BaseModel):
    """ModelManifest contains the necessary information for training a specific machine learning model."""

    id: str = Field(title="Model architecture ID", description="Unique identifier for the model architecture")
    name: str = Field(title="Model architecture name", description="Friendly name of the model architecture")
    description: str = Field(title="Description", description="Detailed description of the model capabilities")
    task: str = Field(title="Task Type", description="Type of machine learning task addressed by the model")
    stats: ModelStats = Field(title="Model Statistics", description="Statistics about the model")
    support_status: ModelManifestDeprecationStatus = Field(
        title="Support Status", description="Current support level (active, deprecated, or obsolete)"
    )
    supported_gpus: dict[GPUMaker, bool] = Field(
        title="Supported GPUs", description="Dictionary mapping GPU types to compatibility status"
    )
    hyperparameters: Hyperparameters = Field(
        title="Hyperparameters", description="Configuration parameters for model training"
    )


class NullModelManifest(ModelManifest):
    """
    NullModelManifest is a placeholder for an empty or non-existent model manifest.

    This class is used to represent the absence of a valid model manifest.
    """

    id: str = Field(default="null")
    name: str = Field(default="null")
    description: str = Field(default="null")
    task: str = Field(default="null")
    stats: ModelStats = Field(default=ModelStats(gigaflops=1, trainable_parameters=1))
    support_status: ModelManifestDeprecationStatus = Field(default=ModelManifestDeprecationStatus.OBSOLETE)
    supported_gpus: dict[str, bool] = Field(default={})
    hyperparameters: Hyperparameters = Field(
        default=Hyperparameters(
            dataset_preparation=DatasetPreparationParameters(
                augmentation=AugmentationParameters(
                    horizontal_flip=False,
                    vertical_flip=False,
                    gaussian_blur=False,
                    random_rotate=False,
                )
            ),
            training=TrainingHyperParameters(
                max_epochs=1,
                early_stopping_epochs=1,
                learning_rate=0.001,
                learning_rate_warmup_epochs=0,
                batch_size=1,
            ),
            evaluation=EvaluationParameters(metric=None),
        )
    )
