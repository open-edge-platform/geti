# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from typing import Annotated, Literal

from pydantic import Field, field_validator, model_validator

from .base import BaseValueObject


class OmeChannelSetting(BaseValueObject):
    """Display color, visibility and intensity window for one source channel."""

    channel: int = Field(ge=0)
    color: str = Field(pattern=r"^#[0-9a-fA-F]{6}$")
    enabled: bool = True
    window_min: float = Field(allow_inf_nan=False)
    window_max: float = Field(allow_inf_nan=False)

    @field_validator("color")
    @classmethod
    def normalize_color(cls, value: str) -> str:
        return value.upper()

    @model_validator(mode="after")
    def validate_window(self) -> "OmeChannelSetting":
        if self.window_min >= self.window_max:
            raise ValueError("window_min must be less than window_max.")
        return self


class OmeChannelSettings(BaseValueObject):
    """A complete display view; unlisted channels are hidden."""

    settings: list[OmeChannelSetting]

    @model_validator(mode="after")
    def validate_channels(self) -> "OmeChannelSettings":
        if len({setting.channel for setting in self.settings}) != len(self.settings):
            raise ValueError("Display channel indices must be unique.")
        return self


class OmeChannelView(OmeChannelSettings):
    """Resolved display settings and whether they are server-computed defaults."""

    is_default: bool


class Region(BaseValueObject):
    """A rectangle in pixel coordinates relative to a selected pyramid level."""

    x: int = Field(ge=0, description="Left coordinate of the region in pixels.")
    y: int = Field(ge=0, description="Top coordinate of the region in pixels.")
    width: int = Field(gt=0, description="Region width in pixels.")
    height: int = Field(gt=0, description="Region height in pixels.")


class RgbChannelAssignment(BaseValueObject):
    """Assign one source channel to one RGB output component."""

    channel: int = Field(ge=0)
    target: Literal["red", "green", "blue"]


class RgbProjection(BaseValueObject):
    """Project selected source channels to a three-channel RGB image."""

    mode: Literal["rgb"] = "rgb"
    channels: tuple[RgbChannelAssignment, ...]

    @property
    def source_channels(self) -> tuple[int, ...]:
        return tuple(assignment.channel for assignment in self.channels)

    @model_validator(mode="after")
    def validate_assignments(self) -> "RgbProjection":
        if len(set(self.source_channels)) != len(self.channels):
            raise ValueError("RGB projection source channels must be unique.")
        if len({assignment.target for assignment in self.channels}) != len(self.channels):
            raise ValueError("RGB projection targets must be unique.")
        return self


class GrayscaleProjection(BaseValueObject):
    """Select one source channel for a single-channel grayscale image."""

    mode: Literal["grayscale"] = "grayscale"
    channel: int = Field(ge=0)

    @property
    def source_channels(self) -> tuple[int, ...]:
        return (self.channel,)


ChannelProjection = Annotated[RgbProjection | GrayscaleProjection, Field(discriminator="mode")]


class OmeImageInfo(BaseValueObject):
    """Structural metadata of an OME image derived from container metadata."""

    size_x: int = Field(gt=0, description="Width of the image in pixels.")
    size_y: int = Field(gt=0, description="Height of the image in pixels.")
    size_z: int = Field(gt=0, default=1, description="Number of z-planes.")
    size_c: int = Field(gt=0, default=1, description="Number of channels.")
    size_t: int = Field(gt=0, default=1, description="Number of timepoints.")
    dimension_order: str = Field(description="Axis order declared by metadata, e.g. XYCZT.")
    pixel_type: str = Field(description="Pixel type declared by metadata, e.g. uint8 or uint16.")
    container_format: Literal["ome_tiff", "ome_zarr"] = Field(
        default="ome_tiff", description="OME container format, e.g. ome_tiff or ome_zarr."
    )
    series_index: int = Field(default=0, ge=0, description="Zero-based index of the image series within the container.")
    is_big_tiff: bool = Field(default=False, description="Whether the container uses the 64-bit BigTIFF format.")
    channels: list[dict[str, object]] = Field(
        default_factory=list,
        description="Per-channel metadata, including index, name, color, emission wavelength and intensity window.",
    )
    pyramid_levels: list[dict[str, object]] = Field(
        default_factory=list,
        description="Resolution levels with level index, width, height and scale factors in XYCZT order.",
    )
    raw_metadata: str | None = Field(
        default=None, description="Original container metadata, such as OME-XML, retained for provenance."
    )

    @model_validator(mode="after")
    def validate_dimension_order(self) -> "OmeImageInfo":
        order = self.dimension_order.upper()
        if not {"X", "Y", "C"}.issubset(set(order)):
            raise ValueError("dimension_order must include X, Y and C axes")
        return self


class OmeImageMetadata(OmeImageInfo):
    """Persisted OME structure, immutable training projection and constituent files."""

    channel_projection: ChannelProjection = Field(
        description="Immutable projection defining RGB or single-channel grayscale output.",
    )
    entrypoint: str | None = None
    files: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_projection_channels(self) -> "OmeImageMetadata":
        if any(channel >= self.size_c for channel in self.channel_projection.source_channels):
            raise ValueError("Channel projection references a channel outside SizeC.")
        return self
