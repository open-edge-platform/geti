# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from pydantic import BaseModel, Field


class AugmentationParameters(BaseModel):
    """Configuration parameters for data augmentation during training."""
    horizontal_flip: bool = Field(
        title="Horizontal flip", description="Flip the image along the vertical axis (swap left and right)"
    )
    vertical_flip: bool = Field(
        title="Vertical flip", description="Flip the image along the horizontal axis (swap up and down)"
    )
    gaussian_blur: bool = Field(title="Gaussian blur", description="Apply Gaussian blur to the image")
    random_rotate: bool = Field(title="Random rotate", description="Apply random rotation to the image")


class DatasetPreparationParameters(BaseModel):
    """Parameters for dataset preparation before training."""
    augmentation: AugmentationParameters


class TrainingHyperParameters(BaseModel):
    """Hyperparameters for model training process."""

    max_epochs: int = Field(
        gt=0,
        title="Maximum epochs",
        description="Maximum number of training epochs to run"
    )
    early_stopping_epochs: int = Field(
        gt=0,
        default=None,
        title="Early stopping epochs",
        description="Stop training if no improvement is seen for this many epochs"
    )
    learning_rate: float = Field(
        gt=0,
        lt=1,
        title="Learning rate",
        description="Base learning rate for the optimizer"
    )
    learning_rate_warmup_epochs: int = Field(
        ge=0,
        default=None,
        title="Learning rate warmup epochs",
        description="Number of epochs to gradually increase learning rate from 0 to base value"
    )
    batch_size: int = Field(
        ge=1,
        le=2048,
        title="Batch size",
        description="Number of samples processed in each training batch"
    )


class EvaluationParameters(BaseModel):
    """Parameters for model evaluation."""
    metric: None = Field(
        default=None,
        title="Evaluation metric",
        description="Metric used to evaluate model performance"
    )


class Hyperparameters(BaseModel):
    """Complete set of configurable parameters for model training and evaluation."""
    dataset_preparation: DatasetPreparationParameters
    training: TrainingHyperParameters
    evaluation: EvaluationParameters
