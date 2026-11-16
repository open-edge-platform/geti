# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

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

    @model_validator(mode="after")
    def validate_dimension_order(self) -> "OmeImageInfo":
        order = self.dimension_order.upper()
        if not {"X", "Y", "C"}.issubset(set(order)):
            raise ValueError("dimension_order must include X, Y and C axes")
        return self
