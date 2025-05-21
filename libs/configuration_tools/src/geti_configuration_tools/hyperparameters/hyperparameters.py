# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from pydantic import BaseModel, Field

from .augmentation import AugmentationParameters


class DatasetPreparationParameters(BaseModel):
    """Parameters for dataset preparation before training."""

    augmentation: AugmentationParameters


class EarlyStopping(BaseModel):
    enable: bool = Field(
        default=False,
        title="Enable early stopping",
        description="Whether to stop training early when performance stops improving"
    )
    patience: int = Field(
        gt=0,
        default=1,
        title="Patience",
        description="Number of epochs with no improvement after which training will be stopped",
    )


class MaxEpochs(BaseModel):
    max_epochs: int = Field(
        gt=0,
        default=1000,
        title="Maximum epochs",
        description="Maximum number of training epochs to run",
    )


class MaxDetectionPerImage(BaseModel):
    enable: bool = Field(
        default=False,
        title="Enable maximum detection per image",
        description="Whether to limit the number of detections per image"
    )
    max_detection_per_image: int = Field(
        default=10000,
        gt=0,
        title="Maximum number of detections per image",
        description=(
            "Maximum number of objects that can be detected in a single image, "
            "only applicable for instance segmentation models"
        ),
    )


class LearningRate(BaseModel):
    learning_rate: float = Field(
        gt=0.0, lt=1.0, default=0.001, title="Learning rate", description="Base learning rate for the optimizer"
    )


class TrainingHyperParameters(BaseModel):
    """Hyperparameters for model training process."""

    max_epochs: MaxEpochs | None = Field(
        default=None, title="Maximum epochs", description="Maximum number of training epochs to run"
    )
    early_stopping: EarlyStopping | None = Field(
        default=None, title="Early stopping", description="Configuration for early stopping mechanism"
    )
    learning_rate: LearningRate | None = Field(
        default=None, title="Learning rate", description="Base learning rate for the optimizer"
    )
    max_detection_per_image: MaxDetectionPerImage | None = Field(
        default=None,
        title="Maximum number of detections per image",
        description=(
            "Maximum number of objects that can be detected in a single image, "
            "only applicable for instance segmentation models"
        ),
    )


class EvaluationParameters(BaseModel):
    """Parameters for model evaluation."""

    metric: None = Field(
        default=None, title="Evaluation metric", description="Metric used to evaluate model performance"
    )


class Hyperparameters(BaseModel):
    """Complete set of configurable parameters for model training and evaluation."""

    dataset_preparation: DatasetPreparationParameters
    training: TrainingHyperParameters
    evaluation: EvaluationParameters
