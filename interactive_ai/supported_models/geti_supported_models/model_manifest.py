# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from enum import Enum

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


class SupportedStatus(str, Enum):
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    OBSOLETE = "obsolete"


class ModelManifest(BaseModel):
    """Algorithm contains the necessary information for training a specific machine learning model."""

    id: str = Field(title="Model manifest ID", description="Unique identifier for the model manifest")
    name: str = Field(title="Model manifest name", description="Display name of the model manifest")
    description: str = Field(title="Description", description="Detailed description of the model capabilities")
    task: str = Field(title="Task Type", description="Type of machine learning task the model performs")
    stats: ModelStats = Field(title="Model Statistics", description="Performance statistics of the model")
    support_status: SupportedStatus = Field(
        title="Support Status", description="Current support level (active, deprecated, or obsolete)"
    )
    supported_gpus: dict[str, bool] = Field(
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
    support_status: SupportedStatus = Field(default=SupportedStatus.OBSOLETE)
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
