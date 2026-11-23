# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import pytest
from pydantic import ValidationError

from app.models import OmeImageInfo
from app.models.ome import OmeImageMetadata


@pytest.fixture
def image_info_data() -> dict[str, object]:
    return {"size_x": 48, "size_y": 32, "dimension_order": "XYCZT", "pixel_type": "uint16"}


def test_metadata_defaults(image_info_data: dict[str, object]) -> None:
    info = OmeImageInfo.model_validate(image_info_data)

    assert info.container_format == "ome_tiff"
    assert info.series_index == 0
    assert info.is_big_tiff is False
    assert info.channels == []
    assert info.pyramid_levels == []
    assert info.raw_metadata is None


@pytest.mark.parametrize("container_format", ["ome_tiff", "ome_zarr"])
def test_supported_container_formats(image_info_data: dict[str, object], container_format: str) -> None:
    info = OmeImageInfo.model_validate({**image_info_data, "container_format": container_format})

    assert info.container_format == container_format


@pytest.mark.parametrize("container_format", ["tiff", "zarr", "OME_TIFF", "", None])
def test_rejects_unsupported_container_formats(image_info_data: dict[str, object], container_format: object) -> None:
    with pytest.raises(ValidationError, match="container_format"):
        OmeImageInfo.model_validate({**image_info_data, "container_format": container_format})


@pytest.mark.parametrize("series_index", [0, 1, 10])
def test_nonnegative_series_indices(image_info_data: dict[str, object], series_index: int) -> None:
    info = OmeImageInfo.model_validate({**image_info_data, "series_index": series_index})

    assert info.series_index == series_index


@pytest.mark.parametrize("series_index", [-1, -10])
def test_rejects_negative_series_indices(image_info_data: dict[str, object], series_index: int) -> None:
    with pytest.raises(ValidationError, match="series_index"):
        OmeImageInfo.model_validate({**image_info_data, "series_index": series_index})


@pytest.mark.parametrize(
    "projection",
    [
        {"mode": "rgb", "channels": [{"channel": 0, "target": "red"}]},
        {"mode": "grayscale", "channel": 0},
    ],
)
def test_metadata_uses_channel_projection(image_info_data: dict[str, object], projection: dict[str, object]) -> None:
    metadata = OmeImageMetadata.model_validate({**image_info_data, "channel_projection": projection})

    assert metadata.model_dump(mode="json")["channel_projection"] == projection
    assert "channel_mapping" not in metadata.model_dump(mode="json")
    assert "channel_mapping" not in OmeImageMetadata.model_json_schema(mode="serialization")["properties"]


@pytest.mark.parametrize("include_projection", [False, True])
def test_metadata_rejects_channel_mapping(image_info_data: dict[str, object], include_projection: bool) -> None:
    projection = {"mode": "rgb", "channels": [{"channel": 0, "target": "red"}]}
    data = {**image_info_data, "channel_mapping": projection}
    if include_projection:
        data["channel_projection"] = projection

    with pytest.raises(ValidationError, match="channel_mapping"):
        OmeImageMetadata.model_validate(data)
