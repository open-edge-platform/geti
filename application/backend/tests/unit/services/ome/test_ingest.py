# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from unittest.mock import MagicMock, patch

import numpy as np
import pytest
import tifffile

from app.models import MediaStorage
from app.models.ome import OmeImageInfo, RgbChannelAssignment, RgbProjection
from app.services.ome import OmeTiffReader
from app.services.ome.ingest import create_ingest_thumbnail


def test_thumbnail_uses_lowest_level_and_mid_plane():
    handle = MagicMock()
    handle.info = OmeImageInfo(
        size_x=5,
        size_y=4,
        size_c=1,
        dimension_order="XYCZT",
        pixel_type="uint16",
        channels=[{"index": 0, "window": {"min": 0, "max": 65535}}],
        size_z=5,
        size_t=3,
        pyramid_levels=[{"level": 0, "width": 5, "height": 4}, {"level": 1, "width": 2, "height": 2}],
    )
    handle.read_region.return_value = np.array([[[0, 65535], [32768, 0]]], dtype=np.uint16)
    thumbnail = create_ingest_thumbnail(
        handle, RgbProjection(channels=(RgbChannelAssignment(channel=0, target="red"),))
    )
    handle.read_region.assert_called_once_with(level=1, z=2, t=1, channels=[0])
    rgb = np.asarray(thumbnail)
    assert rgb.tolist() == [[[0, 0, 0], [255, 0, 0]], [[127, 0, 0], [0, 0, 0]]]


def test_large_non_pyramidal_thumbnail_uses_reader_downsampling():
    handle = MagicMock()
    handle.info = OmeImageInfo(size_x=40000, size_y=30000, size_c=1, dimension_order="XYCZT", pixel_type="uint16")
    handle.read_region.return_value = np.full((1, 192, 256), 65535, dtype=np.uint16)
    thumbnail = create_ingest_thumbnail(
        handle, RgbProjection(channels=(RgbChannelAssignment(channel=0, target="red"),))
    )
    assert thumbnail.size == (256, 192)
    assert thumbnail.getpixel((0, 0)) == (255, 0, 0)
    handle.read_region.assert_called_once_with(level=0, z=0, t=0, channels=[0], output_size=(256, 192))


@pytest.mark.parametrize("layout", ["single_strip", "strips", "tiles"])
def test_large_thumbnail_decodes_each_segment_once(tmp_path, layout):
    path = tmp_path / "large.ome.tiff"
    pixels = np.arange(1152 * 1536, dtype=np.uint16).reshape(1152, 1536)
    tifffile.imwrite(
        path,
        pixels,
        ome=True,
        photometric="minisblack",
        metadata={"axes": "YX"},
        compression="lzw",
        rowsperstrip=384 if layout == "strips" else 1152,
        tile=(128, 128) if layout == "tiles" else None,
    )
    with OmeTiffReader().open(MediaStorage(root=path)) as handle:
        keyframe = handle._tiff.series[0].keyframe
        with (
            patch.object(keyframe, "decode", wraps=keyframe.decode) as decode,
            patch.object(tifffile.FileHandle, "read", autospec=True, side_effect=tifffile.FileHandle.read) as read,
            patch.object(tifffile.TiffPageSeries, "asarray", side_effect=AssertionError("eager read")),
        ):
            thumbnail = create_ingest_thumbnail(
                handle, RgbProjection(channels=(RgbChannelAssignment(channel=0, target="red"),))
            )
        decoded_indices = [call.args[1] for call in decode.call_args_list if call.args[0] is not None]
        expected_decodes = {"single_strip": 1, "strips": 3, "tiles": 108}[layout]
        assert len(decoded_indices) == len(set(decoded_indices)) == expected_decodes
        assert read.call_count == expected_decodes

    xs = np.linspace(0, 1535, 256, dtype=int)
    ys = np.linspace(0, 1151, 192, dtype=int)
    expected = (pixels[ys[:, None], xs].astype(np.float64) * (255.0 / 65535)).astype(np.uint8)
    assert thumbnail.size == (256, 192)
    np.testing.assert_array_equal(np.asarray(thumbnail)[..., 0], expected)
    assert not np.asarray(thumbnail)[..., 1:].any()
