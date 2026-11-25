# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from io import BytesIO
from unittest.mock import MagicMock, Mock, patch
from uuid import uuid4

import numpy as np
import pytest
from PIL import Image

from app.models import MediaStorage
from app.models.ome import OmeImageMetadata
from app.services.base import InvalidImageError
from app.services.ome.materialization import (
    _MAX_ROW_BYTES,
    _MAX_STRIP_HEIGHT,
    _STRIP_PIXELS,
    OmeTrainingMaterializer,
    _write_plane,
)


@pytest.mark.parametrize(
    "projection",
    [
        {"mode": "rgb", "channels": [{"channel": 2, "target": "red"}, {"channel": 0, "target": "blue"}]},
        {"mode": "grayscale", "channel": 1},
    ],
)
@pytest.mark.parametrize(("width", "height", "reads"), [(2301, _MAX_STRIP_HEIGHT + 13, 2), (_STRIP_PIXELS + 17, 1, 2)])
def test_streamed_plane_pixels_coordinates_and_bounded_reads(projection, width, height, reads):
    """Decode streamed PNGs and verify full-resolution pixels across both tile boundaries."""
    info = OmeImageMetadata(
        size_x=width,
        size_y=height,
        size_c=3,
        size_z=4,
        size_t=3,
        pixel_type="uint16",
        dimension_order="XYCZT",
        channel_projection=projection,
    )
    pixels = np.arange(3 * height * width, dtype=np.uint32).reshape(3, height, width).astype(np.uint16)
    handle = Mock()

    def read_region(*, level, region, z, t, channels):
        assert level == 0
        assert (z, t) == (3, 2)
        assert region.height <= _MAX_STRIP_HEIGHT
        assert region.width * region.height <= _STRIP_PIXELS
        assert channels == info.channel_projection.source_channels
        return pixels[list(channels), region.y : region.y + region.height, region.x : region.x + region.width]

    handle.read_region.side_effect = read_region
    content = BytesIO()
    _write_plane(content, handle, info, Mock(z_index=3, t_index=2))
    expected_channels = (pixels.astype(np.float64) / 65535 * 255).astype(np.uint8)
    if projection["mode"] == "rgb":
        expected = np.stack(
            [expected_channels[2], np.zeros((height, width), dtype=np.uint8), expected_channels[0]], axis=2
        )
    else:
        expected = expected_channels[1]
    with Image.open(BytesIO(content.getvalue())) as png:
        png.verify()
    with Image.open(BytesIO(content.getvalue())) as png:
        assert png.mode == ("RGB" if projection["mode"] == "rgb" else "L")
        np.testing.assert_array_equal(np.array(png), expected)
    assert handle.read_region.call_count == reads


@pytest.mark.parametrize(
    ("projection", "components"),
    [
        ({"mode": "grayscale", "channel": 0}, 1),
        ({"mode": "rgb", "channels": [{"channel": 0, "target": "red"}]}, 3),
    ],
)
def test_scanline_budget_rejected_before_reading_or_writing(projection, components):
    """Reject unsupported scanlines explicitly rather than downsampling training coordinates."""
    info = OmeImageMetadata(
        size_x=_MAX_ROW_BYTES // components + 1,
        size_y=1,
        pixel_type="uint8",
        dimension_order="XYCZT",
        channel_projection=projection,
    )
    stream, handle = BytesIO(), Mock()
    with pytest.raises(InvalidImageError, match="scanline budget"):
        _write_plane(stream, handle, info, Mock(z_index=0, t_index=0))
    assert not stream.getvalue()
    handle.read_region.assert_not_called()


@pytest.mark.parametrize(("width", "height"), [(4096, 4096), (8192, 2048)])
def test_typical_planes_use_sixteen_full_width_reads(width, height):
    """Keep the measured read-count improvement without allocating or downsampling a whole source plane."""
    info = OmeImageMetadata(
        size_x=width,
        size_y=height,
        pixel_type="uint16",
        dimension_order="XYCZT",
        channel_projection={"mode": "grayscale", "channel": 0},
    )
    handle = Mock()

    def read_region(*, level, region, z, t, channels):
        assert level == 0
        assert region.x == 0 and region.width == width
        assert region.height <= _MAX_STRIP_HEIGHT
        assert region.width * region.height <= _STRIP_PIXELS
        return np.zeros((1, region.height, region.width), dtype=np.uint16)

    handle.read_region.side_effect = read_region
    stream = BytesIO()
    _write_plane(stream, handle, info, Mock(z_index=0, t_index=0))
    assert handle.read_region.call_count == 16
    assert sum(call.kwargs["region"].height for call in handle.read_region.call_args_list) == height
    with Image.open(BytesIO(stream.getvalue())) as png:
        assert png.size == (width, height)
        png.verify()


def test_wrong_region_shape_is_rejected():
    info = OmeImageMetadata(
        size_x=10,
        size_y=8,
        pixel_type="uint8",
        dimension_order="XYCZT",
        channel_projection={"mode": "grayscale", "channel": 0},
    )
    handle = Mock()
    handle.read_region.return_value = np.zeros((1, 4, 5), dtype=np.uint8)
    with pytest.raises(InvalidImageError, match="dimensions"):
        _write_plane(BytesIO(), handle, info, Mock(z_index=0, t_index=0))


@pytest.mark.parametrize("existing", [False, True])
def test_failed_materialization_closes_handles_and_removes_only_its_partial_file(tmp_path, existing):
    """Keep the caller's existing files intact while cleaning incomplete writes and reader handles."""
    service = Mock()
    service.validate_ome_plane_selection.return_value = OmeImageMetadata(
        size_x=10,
        size_y=8,
        dimension_order="XYCZT",
        pixel_type="uint8",
        channel_projection={"mode": "grayscale", "channel": 0},
    )
    service.get_media_storage.return_value = MediaStorage(root=tmp_path / "source.ome.tiff")
    plane = Mock(id=uuid4(), ome_image_id=uuid4(), z_index=0, t_index=0)
    materializer = OmeTrainingMaterializer(service, tmp_path)
    path = tmp_path / f"{plane.id}.png"
    if existing:
        path.write_bytes(b"existing")

    def fail_write(stream, handle, info, selected_plane):
        stream.write(b"partial")
        raise InvalidImageError("Decoding failed")

    reader = MagicMock()
    with (
        patch.object(materializer._registry, "get_reader", return_value=reader),
        patch("app.services.ome.materialization._write_plane", side_effect=fail_write),
        pytest.raises(FileExistsError if existing else InvalidImageError),
    ):
        materializer.materialize(uuid4(), plane)
    if existing:
        assert path.read_bytes() == b"existing"
        reader.open.assert_not_called()
    else:
        assert not path.exists()
        reader.open.return_value.__exit__.assert_called_once()
    assert materializer.write_projections([str(plane.id)]) is None
