# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from pydantic import BaseModel, Field


class AugmentationParameters(BaseModel):
    """
    Configuration parameters for data augmentation during training.

    Attributes:
        horizontal_flip: Whether to flip images horizontally (swap left and right)
        vertical_flip: Whether to flip images vertically (swap up and down)
        gaussian_blur: Whether to apply Gaussian blur augmentation
        random_rotate: Whether to apply random rotation augmentation
    """
    horizontal_flip: bool = Field(
        title="Horizontal flip",
        description="Flip the image along the vertical axis (swap left and right)"
    )
    vertical_flip: bool = Field(
        title="Vertical flip",
        description="Flip the image along the horizontal axis (swap up and down)"
    )
    gaussian_blur: bool = Field(
        title="Gaussian blur",
        description="Apply Gaussian blur to the image"
    )
    random_rotate: bool = Field(
        title="Random rotate",
        description="Apply random rotation to the image"
    )


class DatasetPreparationParameters(BaseModel):
    """
    Parameters for dataset preparation before training.

    Attributes:
        augmentation: Configuration for image augmentation techniques
    """
    augmentation: AugmentationParameters


class TrainingHyperParameters(BaseModel):
    """
    Hyperparameters for model training process.

    Attributes:
        max_epochs: Maximum number of training epochs
        early_stopping_epochs: Number of epochs with no improvement after which training will stop
        learning_rate: Learning rate for optimization algorithm
        learning_rate_warmup_epochs: Number of epochs for learning rate warmup
        batch_size: Number of samples in each training batch
    """
    max_epochs: int = Field(gt=0, description="Max number of epochs")
    early_stopping_epochs: int = Field(gt=0)
    learning_rate: float = Field(gt=0, lt=1)
    learning_rate_warmup_epochs: int = Field(ge=0)
    batch_size: int = Field(ge=1, le=2048)


class EvaluationParameters(BaseModel):
    """
    Parameters for model evaluation.

    Attributes:
        metric: Evaluation metric to use (currently a placeholder)
    """
    metric: None = None


class Hyperparameters(BaseModel):
    """
    Complete set of configurable parameters for model training and evaluation.

    Attributes:
        dataset_preparation: Parameters for dataset preparation
        training: Hyperparameters for training
        evaluation: Parameters for model evaluation
    """
    dataset_preparation: DatasetPreparationParameters
    training: TrainingHyperParameters
    evaluation: EvaluationParameters
