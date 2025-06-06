# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from pydantic import BaseModel, Field


class CenterCrop(BaseModel):
    enable: bool = Field(
        default=False,
        title="Enable center crop",
        description="Whether to apply center cropping to the image",
    )
    ratio: float = Field(
        gt=0.0, default=1.0, title="Crop ratio", description="Ratio of original dimensions to keep when cropping"
    )


class RandomResizeCrop(BaseModel):
    enable: bool = Field(
        default=False,
        title="Enable random resize crop",
        description="Whether to apply random resize and crop to the image",
    )
    ratio: float = Field(
        gt=0.0,
        default=1.0,
        title="Crop resize ratio",
        description="Ratio of original dimensions to apply during resize crop operation",
    )


class RandomAffine(BaseModel):
    enable: bool = Field(
        default=False,
        title="Enable random affine",
        description="Whether to apply random affine transformations to the image",
    )
    degrees: float = Field(
        ge=0.0, default=0.0, title="Rotation degrees", description="Maximum rotation angle in degrees"
    )
    translate_x: float = Field(
        default=0.0,
        title="Horizontal translation",
        description="Maximum horizontal translation as a fraction of image width",
    )
    translate_y: float = Field(
        default=0.0,
        title="Vertical translation",
        description="Maximum vertical translation as a fraction of image height",
    )
    scale: float = Field(
        default=1.0, title="Scale factor", description="Scaling factor for the image during affine transformation"
    )


class RandomHorizontalFlip(BaseModel):
    enable: bool = Field(
        default=False,
        title="Enable random horizontal flip",
        description="Whether to apply random flip images horizontally along the vertical axis (swap left and right)",
    )


class RandomVerticalFlip(BaseModel):
    enable: bool = Field(
        default=False,
        title="Enable random vertical flip",
        description="Whether to apply random flip images vertically along the horizontal axis (swap top and bottom)",
    )


class RandomIOUCrop(BaseModel):
    enable: bool = Field(
        default=False,
        title="Enable random IoU crop",
        description="Whether to apply random cropping based on IoU criteria",
    )


class ColorJitter(BaseModel):
    enable: bool = Field(
        default=False,
        title="Enable color jitter",
        description="Whether to apply random color jitter to the image",
    )


class GaussianBlur(BaseModel):
    enable: bool = Field(
        default=False,
        title="Enable Gaussian blur",
        description="Whether to apply Gaussian blur to the image",
    )
    kernel_size: int = Field(gt=0, default=3, title="Kernel size", description="Size of the Gaussian kernel")


class Tiling(BaseModel):
    enable: bool = Field(
        default=False,
        title="Enable tiling",
        description="Whether to apply tiling to the image",
    )
    adaptive_tiling: bool = Field(
        default=False, title="Adaptive tiling", description="Whether to use adaptive tiling based on image content"
    )
    tile_size: int = Field(gt=0, default=128, title="Tile size", description="Size of each tile in pixels")
    tile_overlap: int = Field(
        gt=0, default=64, title="Tile overlap", description="Overlap between adjacent tiles in pixels"
    )


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
    random_horizontal_flip: RandomHorizontalFlip | None = Field(
        default=None,
        title="Random horizontal flip",
        description="Randomly flip images horizontally along the vertical axis (swap left and right)",
    )
    random_vertical_flip: RandomVerticalFlip | None = Field(
        default=None,
        title="Random vertical flip",
        description="Randomly flip images vertically along the horizontal axis (swap top and bottom)",
    )
    random_iou_crop: RandomIOUCrop | None = Field(
        default=None,
        title="Random IoU crop",
        description="Randomly crop images based on Intersection over Union (IoU) criteria",
    )
    color_jitter: ColorJitter | None = Field(
        default=None,
        title="Color jitter",
        description="Settings for random color jitter (brightness, contrast, saturation, hue)",
    )
    gaussian_blur: GaussianBlur | None = Field(
        default=None, title="Gaussian blur", description="Settings for Gaussian blur augmentation"
    )
    tiling: Tiling | None = Field(default=None, title="Tiling", description="Settings for image tiling")
