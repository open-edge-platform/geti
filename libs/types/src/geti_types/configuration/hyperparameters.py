# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from pydantic import BaseModel, Field

from .augmentation import AugmentationParameters


class DatasetPreparationParameters(BaseModel):
    """Parameters for dataset preparation before training."""

    augmentation: AugmentationParameters


class EarlyStopping(BaseModel):
    patience: int = Field(
        gt=0,
        title="Patience",
        description="Number of epochs with no improvement after which training will be stopped"
    )


class TrainingHyperParameters(BaseModel):
    """Hyperparameters for model training process."""

    max_epochs: int = Field(gt=0, title="Maximum epochs", description="Maximum number of training epochs to run")
    early_stopping: EarlyStopping | None = Field(
        default=None,
        title="Early stopping",
        description="Configuration for early stopping mechanism"
    )
    learning_rate: float = Field(gt=0, lt=1, title="Learning rate", description="Base learning rate for the optimizer")
    max_detection_per_image: int | None = Field(
        default=None,
        gt=0,
        title="Maximum number of detections per image",
        description="Maximum number of objects that can be detected in a single image, only applicable for instance segmentation models"
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
