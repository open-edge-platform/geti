# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from pydantic import BaseModel, Field


class CenterCrop(BaseModel):
    ratio: float = Field(gt=0, title="Crop ratio", description="Ratio of original dimensions to keep when cropping")


class RandomResizeCrop(BaseModel):
    ratio: float = Field(
        gt=0, title="Resize ratio", description="Ratio of original dimensions to apply during resize operation"
    )


class RandomAffine(BaseModel):
    degrees: float = Field(gt=0, title="Rotation degrees", description="Maximum rotation angle in degrees")
    translate_x: float | None = Field(
        default=None,
        title="Horizontal translation",
        description="Maximum horizontal translation as a fraction of image width",
    )
    translate_y: float | None = Field(
        default=None,
        title="Vertical translation",
        description="Maximum vertical translation as a fraction of image height",
    )
    scale: float | None = Field(
        default=None, title="Scale factor", description="Scaling factor for the image during affine transformation"
    )


class GaussianBlur(BaseModel):
    kernel_size: int = Field(gt=0, title="Kernel size", description="Size of the Gaussian kernel")


class Tiling(BaseModel):
    adaptive_tiling: bool = Field(
        title="Adaptive tiling", description="Whether to use adaptive tiling based on image content"
    )
    tile_size: int = Field(gt=0, title="Tile size", description="Size of each tile in pixels")
    tile_overlap: int = Field(gt=0, title="Tile overlap", description="Overlap between adjacent tiles in pixels")


class AugmentationParameters(BaseModel):
    """Configuration parameters for data augmentation during training."""

    center_crop: CenterCrop | None = Field(
        default=None, title="Center crop", description="Settings for center cropping images"
    )
    random_resize_crop: RandomResizeCrop | None = Field(
        default=None, title="Random resize crop", description="Settings for random resize and crop augmentation"
    )
    random_affine: RandomAffine | None = Field(
        default=None, title="Random affine", description="Settings for random affine transformations"
    )
    random_horizontal_flip: bool = Field(
        default=False,
        title="Random horizontal flip",
        description="Randomly flip images horizontally along the vertical axis (swap left and right)",
    )
    gaussian_blur: GaussianBlur | None = Field(
        default=None, title="Gaussian blur", description="Settings for Gaussian blur augmentation"
    )
    tiling: Tiling | None = Field(default=None, title="Tiling", description="Settings for image tiling")
