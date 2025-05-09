# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from pydantic import BaseModel, Field


class CenterCrop(BaseModel):
    ratio: float = Field(
        title="Crop ratio",
        description="Ratio of original dimensions to keep when cropping"
    )


class RandomResizeCrop(BaseModel):
    ratio: float = Field(
        title="Resize ratio",
        description="Ratio of original dimensions to apply during resize operation"
    )


class RandomAffine(BaseModel):
    degrees: float = Field(
        title="Rotation degrees",
        description="Maximum rotation angle in degrees"
    )
    translate_x: float | None = Field(
        default=None,
        title="Horizontal translation",
        description="Maximum horizontal translation as a fraction of image width"
    )
    translate_y: float | None = Field(
        default=None,
        title="Vertical translation",
        description="Maximum vertical translation as a fraction of image height"
    )
    scale: float | None = Field(
        default=None,
        title="Scale factor",
        description="Scaling factor for the image during affine transformation"
    )


class GaussianBlur(BaseModel):
    kernel_size: int = Field(
        title="Kernel size",
        description="Size of the Gaussian kernel"
    )

class Tiling(BaseModel):
    adaptive_tiling: bool = Field(
        title="Adaptive tiling",
        description="Whether to use adaptive tiling based on image content"
    )
    tile_size: int = Field(
        title="Tile size",
        description="Size of each tile in pixels"
    )
    tile_overlap: int = Field(
        title="Tile overlap",
        description="Overlap between adjacent tiles in pixels"
    )


class AugmentationParameters(BaseModel):
    """Configuration parameters for data augmentation during training."""

    center_crop: CenterCrop | None = Field(
        default=None,
        title="Center crop",
        description="Settings for center cropping images"
    )
    random_resize_crop: RandomResizeCrop | None = Field(
        default=None,
        title="Random resize crop",
        description="Settings for random resize and crop augmentation"
    )
    random_affine: RandomAffine | None = Field(
        default=None,
        title="Random affine",
        description="Settings for random affine transformations"
    )
    random_horizontal_flip: bool = Field(
        default=False,
        title="Random horizontal flip",
        description="Randomly flip images horizontally along the vertical axis (swap left and right)"
    )
    gaussian_blur: GaussianBlur | None = Field(
        default=None,
        title="Gaussian blur",
        description="Settings for Gaussian blur augmentation"
    )
    tiling: Tiling | None = Field(
        default=None,
        title="Tiling",
        description="Settings for image tiling"
    )


class DatasetPreparationParameters(BaseModel):
    """Parameters for dataset preparation before training."""

    augmentation: AugmentationParameters


class EarlyStopping(BaseModel):
    patience: int = Field(
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
