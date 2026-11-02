# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
from uuid import UUID

from pydantic import BaseModel

from app.models.ome import ChannelDisplaySetting, OmeChannel, OmeContainerFormat, OmePyramidLevel


class OmeImageInfoView(BaseModel):
    """Structure of an OME image (dimensions, channels and resolution levels)"""

    container_format: OmeContainerFormat
    size_x: int
    size_y: int
    size_z: int
    size_c: int
    size_t: int
    dimension_order: str
    pixel_type: str
    significant_bits: int | None
    is_big_tiff: bool
    channels: list[OmeChannel]
    pyramid_levels: list[OmePyramidLevel]

    model_config = {
        "json_schema_extra": {
            "example": {
                "container_format": "ome_tiff",
                "size_x": 2048,
                "size_y": 2048,
                "size_z": 60,
                "size_c": 3,
                "size_t": 1,
                "dimension_order": "XYCZT",
                "pixel_type": "uint16",
                "significant_bits": 12,
                "is_big_tiff": False,
                "channels": [
                    {"index": 0, "name": "DAPI", "color": "#0000ff", "emission_wavelength": 461},
                    {"index": 1, "name": "GFP", "color": "#00ff00", "emission_wavelength": 510},
                    {"index": 2, "name": "Cy5", "color": "#ff0000", "emission_wavelength": 670},
                ],
                "pyramid_levels": [
                    {"level": 0, "width": 2048, "height": 2048, "scale": [1.0, 1.0]},
                    {"level": 1, "width": 1024, "height": 1024, "scale": [2.0, 2.0]},
                ],
            }
        }
    }


class OmeChannelViewSettings(BaseModel):
    """Display settings of the channels of an OME image"""

    settings: list[ChannelDisplaySetting]

    model_config = {
        "json_schema_extra": {
            "example": {
                "settings": [
                    {"channel": 2, "target": "red", "enabled": True, "window_min": 120, "window_max": 4000},
                    {"channel": 1, "target": "green", "enabled": True, "window_min": 80, "window_max": 2500},
                    {"channel": 0, "target": "blue", "enabled": False, "window_min": 0, "window_max": 4095},
                ]
            }
        }
    }


class OmeChannelViewResponse(OmeChannelViewSettings):
    """Display settings of the channels of an OME image, flagging whether they are server-computed defaults"""

    is_default: bool


class AnnotatedOmePlane(BaseModel):
    """Annotated (Z, T) plane of an OME image"""

    media_id: UUID
    z_index: int
    t_index: int
