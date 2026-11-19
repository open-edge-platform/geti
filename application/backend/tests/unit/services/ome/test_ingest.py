# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from unittest.mock import MagicMock

import numpy as np

from app.models.ome import OmeImageInfo, RgbChannelAssignment, RgbProjection
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


def test_large_non_pyramidal_thumbnail_samples_rows():
    handle = MagicMock()
    handle.info = OmeImageInfo(size_x=40000, size_y=30000, size_c=1, dimension_order="XYCZT", pixel_type="uint16")
    handle.read_region.side_effect = lambda *, region, **_: np.full((1, 1, region.width), 65535, dtype=np.uint16)
    thumbnail = create_ingest_thumbnail(
        handle, RgbProjection(channels=(RgbChannelAssignment(channel=0, target="red"),))
    )
    assert thumbnail.size == (256, 192)
    assert thumbnail.getpixel((0, 0)) == (255, 0, 0)
    assert handle.read_region.call_count == 192
    assert all(call.kwargs["region"].height == 1 for call in handle.read_region.call_args_list)
