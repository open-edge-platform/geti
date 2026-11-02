# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
from enum import StrEnum
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .base import BaseEntity


class OmeContainerFormat(StrEnum):
    """Container format of an OME image."""

    OME_TIFF = "ome_tiff"
    OME_ZARR = "ome_zarr"


class RgbTarget(StrEnum):
    """Display/training RGB channel a source channel is projected onto."""

    RED = "red"
    GREEN = "green"
    BLUE = "blue"

    @property
    def rgb_index(self) -> int:
        """Index of the target in an RGB array."""
        return list(RgbTarget).index(self)


class OmeChannel(BaseModel):
    """Channel description extracted from the OME metadata."""

    index: int
    name: str | None = None
    color: str | None = Field(default=None, description="Declared display color, as '#rrggbb'")
    emission_wavelength: float | None = Field(default=None, description="Emission wavelength in nanometers")


class OmePyramidLevel(BaseModel):
    """Resolution level of a pyramidal OME image."""

    level: int
    width: int
    height: int
    scale: list[float] = Field(description="Per-axis downscale factor relative to the full-resolution level")


class ChannelMapping(BaseModel):
    """Projection of a source channel onto an RGB target, with the intensity window used for the projection."""

    model_config = ConfigDict(frozen=True)

    channel: int = Field(ge=0)
    target: RgbTarget
    window_min: float
    window_max: float

    @model_validator(mode="after")
    def _validate_window(self) -> Self:
        if self.window_min >= self.window_max:
            raise ValueError(f"window_min ({self.window_min}) must be < window_max ({self.window_max})")
        return self


class ChannelDisplaySetting(ChannelMapping):
    """User-tunable display setting of a channel in the annotator."""

    enabled: bool = True


class OmeImageInfo(BaseEntity):
    """
    Structure of an OME image derived from its OME metadata, immutable after ingest.

    Attributes:
        container_format: OME container format
        size_x: Width of the full-resolution level
        size_y: Height of the full-resolution level
        size_z: Number of Z slices
        size_c: Number of channels
        size_t: Number of time points
        dimension_order: Axis order declared by the metadata, e.g. 'XYCZT'
        pixel_type: Pixel type, e.g. 'uint16'
        significant_bits: Number of meaningful bits per pixel, if declared
        series_index: Index of the image series used within the container
        is_big_tiff: Whether the container is encoded as BigTIFF
        channels: Channel descriptions
        channel_mapping: Fixed channel->RGB projection used to materialize training data
        pyramid_levels: Resolution levels, empty if the image is not pyramidal
    """

    container_format: OmeContainerFormat
    size_x: int
    size_y: int
    size_z: int = 1
    size_c: int = 1
    size_t: int = 1
    dimension_order: str
    pixel_type: str
    significant_bits: int | None = None
    series_index: int = 0
    is_big_tiff: bool = False
    channels: list[OmeChannel]
    channel_mapping: list[ChannelMapping]
    pyramid_levels: list[OmePyramidLevel]

    @property
    def plane_count(self) -> int:
        """Number of annotatable (Z, T) planes."""
        return self.size_z * self.size_t

    def plane_index(self, z: int, t: int) -> int:
        """Linear index of the (z, t) plane, used as the leaf media frame index."""
        return z + t * self.size_z


class OmeChannelView(BaseModel):
    """Display settings of the channels of an OME image."""

    settings: list[ChannelDisplaySetting]
    is_default: bool
