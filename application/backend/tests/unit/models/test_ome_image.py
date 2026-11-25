# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.api.schemas.media import MediaViewAdapter
from app.db.schema import MediaDB
from app.models import OmeImageInfo
from app.models.media import ImageFormat, MediaAdapter, MediaType, OmePlane
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


def test_plane_orm_round_trip_preserves_public_parent_field():
    parent_id = uuid4()
    row = MediaDB(
        id=str(uuid4()),
        project_id=str(uuid4()),
        type=MediaType.OME_PLANE,
        name="specimen_z12_t1",
        format=ImageFormat.PNG,
        width=48,
        height=32,
        size=0,
        source_id=None,
        parent_id=str(parent_id),
        z_index=12,
        t_index=1,
    )
    plane = MediaAdapter.validate_python(row)
    assert isinstance(plane, OmePlane)
    assert plane.ome_image_id == parent_id
    view = MediaViewAdapter.validate_python(plane, from_attributes=True).model_dump(mode="json")
    assert view["ome_image_id"] == str(parent_id)
    assert "parent_id" not in view
    assert "video_id" not in view
    assert "frame_index" not in view
    assert "frame_index" not in plane.model_dump()
    assert MediaAdapter.validate_python(plane.model_dump()) == plane


@pytest.mark.parametrize("coordinate", ["z_index", "t_index"])
def test_plane_rejects_negative_coordinates(coordinate):
    with pytest.raises(ValidationError, match=coordinate):
        OmePlane.model_validate(
            {
                "id": uuid4(),
                "project_id": uuid4(),
                "type": "ome_plane",
                "name": "plane",
                "format": "png",
                "width": 48,
                "height": 32,
                "size": 0,
                "source_id": None,
                "ome_image_id": uuid4(),
                "z_index": 0,
                "t_index": 0,
                coordinate: -1,
            }
        )
