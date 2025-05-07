# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from enum import Enum

from pydantic import BaseModel, Field

from sc_sdk.algorithms.hyperparameters import (
    AugmentationParameters,
    DatasetPreparationParameters,
    EvaluationParameters,
    Hyperparameters,
    TrainingHyperParameters,
)


class AlgorithmStats(BaseModel):
    """Information about a machine learning algorithm."""
    gigaflops: float = Field(
        gt=0,
        title="Gigaflops",
        description="Billions of floating-point operations per second required by the model"
    )
    trainable_parameters: int = Field(
        gt=0,
        title="Trainable parameters",
        description="Number of trainable parameters in the model"
    )


class SupportedStatus(str, Enum):
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    OBSOLETE = "obsolete"


class Algorithm(BaseModel):
    """Algorithm contains the necessary information for training a specific machine learning model."""
    id: str = Field(
        title="Algorithm ID",
        description="Unique identifier for the algorithm"
    )
    name: str = Field(
        title="Algorithm Name",
        description="Display name of the algorithm"
    )
    description: str = Field(
        title="Description",
        description="Detailed description of the algorithm's capabilities"
    )
    task: str = Field(
        title="Task Type",
        description="Type of machine learning task the algorithm performs"
    )
    stats: AlgorithmStats = Field(
        title="Algorithm Statistics",
        description="Performance statistics of the model"
    )
    support_status: SupportedStatus = Field(
        title="Support Status",
        description="Current support level (active, deprecated, or obsolete)"
    )
    supported_gpus: dict[str, bool] = Field(
        title="Supported GPUs",
        description="Dictionary mapping GPU types to compatibility status"
    )
    hyperparameters: Hyperparameters = Field(
        title="Hyperparameters",
        description="Configuration parameters for model training"
    )


class NullAlgorithm(Algorithm):
    """
    NullAlgorithm is a placeholder for an empty or non-existent algorithm.

    This class is used to represent the absence of a valid algorithm configuration.
    """

    id: str = Field(default="null")
    name: str = Field(default="null")
    description: str = Field(default="null")
    task: str = Field(default="null")
    stats: AlgorithmStats = Field(default=AlgorithmStats(gigaflops=1, trainable_parameters=1))
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
