# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from enum import Enum

from geti_configuration_tools.hyperparameters import (
    AugmentationParameters,
    DatasetPreparationParameters,
    EarlyStopping,
    EvaluationParameters,
    Hyperparameters,
    TrainingHyperParameters,
)
from pydantic import BaseModel, Field


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
    DEPRECATED = "deprecated"  # Model architecture is deprecated, can still view and train but it's discouraged
    OBSOLETE = "obsolete"  # Model architecture is no longer supported, models can be still viewed but not trained

    def __str__(self) -> str:
        """Returns the name of the model status."""
        return str(self.name)


class PerformanceRatings(BaseModel):
    """Ratings for different performance aspects of a model."""

    accuracy: int = Field(
        ge=1,
        le=3,
        default=1,
        title="Accuracy rating",
        description="Rating of the model accuracy. "
        "The value should be interpreted relatively to the other available models, "
        "and it ranges from 1 (below average) to 3 (above average).",
    )
    training_time: int = Field(
        ge=1,
        le=3,
        default=1,
        title="Training time rating",
        description="Rating of the model training time. "
        "The value should be interpreted relatively to the other available models, "
        "and it ranges from 1 (below average/slower) to 3 (above average/faster).",
    )
    inference_speed: int = Field(
        ge=1,
        le=3,
        default=1,
        title="Inference speed rating",
        description="Rating of the model inference speed. "
        "The value should be interpreted relatively to the other available models, "
        "and it ranges from 1 (below average/slower) to 3 (above average/faster).",
    )


class ModelStats(BaseModel):
    """Information about a machine learning model."""

    gigaflops: float = Field(
        gt=0, title="Gigaflops", description="Billions of floating-point operations per second required by the model"
    )
    trainable_parameters: int = Field(
        gt=0, title="Trainable parameters", description="Number of trainable parameters in the model"
    )
    performance_ratings: PerformanceRatings = Field(
        title="Performance ratings", description="Standardized ratings for model performance metrics"
    )


class Capabilities(BaseModel):
    """Model capabilities configuration."""

    xai: bool = Field(
        default=False, title="Explainable AI Support", description="Whether the model supports explainable AI features"
    )
    tiling: bool = Field(
        default=False,
        title="Tiling Support",
        description="Whether the model supports image tiling for processing large images",
    )


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
    capabilities: Capabilities = Field(
        title="Model Capabilities", description="Special capabilities supported by the model"
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
    stats: ModelStats = Field(
        default=ModelStats(
            gigaflops=1,
            trainable_parameters=1,
            performance_ratings=PerformanceRatings(),
        )
    )
    support_status: ModelManifestDeprecationStatus = Field(default=ModelManifestDeprecationStatus.OBSOLETE)
    supported_gpus: dict[GPUMaker, bool] = Field(default={})
    hyperparameters: Hyperparameters = Field(
        default=Hyperparameters(
            dataset_preparation=DatasetPreparationParameters(augmentation=AugmentationParameters()),
            training=TrainingHyperParameters(
                max_epochs=1,
                early_stopping=EarlyStopping(patience=1),
                learning_rate=0.001,
            ),
            evaluation=EvaluationParameters(metric=None),
        )
    )
    capabilities: Capabilities = Field(default=Capabilities(xai=False, tiling=False))
