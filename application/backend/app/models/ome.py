# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from typing import Literal

from pydantic import Field, model_validator

from .base import BaseValueObject


class Region(BaseValueObject):
    """A rectangle in pixel coordinates relative to a selected pyramid level."""

    x: int = Field(ge=0, description="Left coordinate of the region in pixels.")
    y: int = Field(ge=0, description="Top coordinate of the region in pixels.")
    width: int = Field(gt=0, description="Region width in pixels.")
    height: int = Field(gt=0, description="Region height in pixels.")


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
