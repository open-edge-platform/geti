# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
import numpy as np
import pytest
import tifffile

from app.models.ome import OmeContainerFormat
from app.services.ome.reader import InvalidOmeImageError, MediaStorage, OmeTiffReader
from tests.conftest import ome_pixel_value


@pytest.fixture
def fxt_reader() -> OmeTiffReader:
    return OmeTiffReader()


class TestOmeTiffReaderParse:
    @pytest.mark.parametrize(
        "size_t, size_c, size_z",
        [
            pytest.param(1, 3, 1, id="XYC"),
            pytest.param(1, 2, 5, id="XYCZ"),
            pytest.param(3, 4, 2, id="XYCZT"),
            pytest.param(1, 1, 1, id="XY_single_channel"),
        ],
    )
    def test_parse_dimensions(self, fxt_reader, fxt_ome_tiff_factory, size_t, size_c, size_z):
        path = fxt_ome_tiff_factory(size_t=size_t, size_c=size_c, size_z=size_z)

        parsed = fxt_reader.parse(MediaStorage(root=path))

        info = parsed.info
        assert info.container_format == OmeContainerFormat.OME_TIFF
        assert (info.size_x, info.size_y) == (48, 32)
        assert (info.size_z, info.size_c, info.size_t) == (size_z, size_c, size_t)
        assert info.plane_count == size_z * size_t
        assert info.pixel_type == "uint16"
        assert len(info.channels) == size_c
        assert info.channel_mapping == []
        assert info.pyramid_levels == []
        assert not info.is_big_tiff
        assert "<OME" in parsed.raw_metadata

    def test_parse_channel_metadata(self, fxt_reader, fxt_ome_tiff_factory):
        path = fxt_ome_tiff_factory(
            size_c=2,
            significant_bits=12,
            channels={"Name": ["DAPI", "GFP"], "EmissionWavelength": [461.0, 510.0], "Color": [65535, 16711935]},
        )

        info = fxt_reader.parse(MediaStorage(root=path)).info

        assert info.significant_bits == 12
        assert [(c.index, c.name, c.emission_wavelength) for c in info.channels] == [
            (0, "DAPI", 461.0),
            (1, "GFP", 510.0),
        ]
        # OME colors are signed 32-bit RGBA integers
        assert [c.color for c in info.channels] == ["#0000ff", "#00ff00"]

    def test_parse_pyramidal_bigtiff(self, fxt_reader, fxt_ome_tiff_factory):
        path = fxt_ome_tiff_factory(height=64, width=96, pyramid_levels=3, bigtiff=True)

        info = fxt_reader.parse(MediaStorage(root=path)).info

        assert info.is_big_tiff
        assert [(level.width, level.height, level.scale) for level in info.pyramid_levels] == [
            (96, 64, [1.0, 1.0]),
            (48, 32, [2.0, 2.0]),
            (24, 16, [4.0, 4.0]),
        ]

    def test_parse_interleaved_rgb(self, fxt_reader, tmp_path):
        path = tmp_path / "rgb.ome.tiff"
        tifffile.imwrite(path, np.zeros((32, 48, 3), np.uint8), ome=True, photometric="rgb")

        info = fxt_reader.parse(MediaStorage(root=path)).info

        assert info.size_c == 3
        assert [c.index for c in info.channels] == [0, 1, 2]

    def test_parse_rejects_non_ome_tiff(self, fxt_reader, tmp_path):
        path = tmp_path / "plain.tiff"
        tifffile.imwrite(path, np.zeros((32, 48), np.uint8))

        with pytest.raises(InvalidOmeImageError, match="not an OME-TIFF"):
            fxt_reader.parse(MediaStorage(root=path))

    def test_parse_rejects_garbage(self, fxt_reader, tmp_path):
        path = tmp_path / "garbage.ome.tiff"
        path.write_bytes(b"definitely not a tiff")

        with pytest.raises(InvalidOmeImageError):
            fxt_reader.parse(MediaStorage(root=path))


class TestOmeTiffReaderReadPlane:
    @pytest.mark.parametrize("z, t", [(0, 0), (2, 0), (0, 1), (1, 2)])
    def test_read_plane_selects_the_right_pages(self, fxt_reader, fxt_ome_tiff_factory, z, t):
        path = fxt_ome_tiff_factory(size_t=3, size_c=4, size_z=3)

        planes = fxt_reader.read_plane(MediaStorage(root=path), z=z, t=t, channels=[3, 0])

        assert planes.shape == (2, 32, 48)
        assert planes.dtype == np.uint16
        assert planes[0, 0, 0] == ome_pixel_value(t=t, c=3, z=z)
        assert planes[1, 0, 0] == ome_pixel_value(t=t, c=0, z=z)

    def test_read_plane_at_pyramid_level(self, fxt_reader, fxt_ome_tiff_factory):
        path = fxt_ome_tiff_factory(size_z=2, height=64, width=96, pyramid_levels=3)

        planes = fxt_reader.read_plane(MediaStorage(root=path), z=1, t=0, channels=[2], level=2)

        assert planes.shape == (1, 16, 24)
        assert planes[0, 0, 0] == ome_pixel_value(t=0, c=2, z=1)

    def test_read_plane_interleaved_rgb(self, fxt_reader, tmp_path):
        path = tmp_path / "rgb.ome.tiff"
        data = np.zeros((32, 48, 3), np.uint8)
        data[..., 0], data[..., 1], data[..., 2] = 10, 20, 30
        tifffile.imwrite(path, data, ome=True, photometric="rgb")

        planes = fxt_reader.read_plane(MediaStorage(root=path), z=0, t=0, channels=[2, 1, 0])

        assert [int(plane[0, 0]) for plane in planes] == [30, 20, 10]

    @pytest.mark.parametrize("z, t, channel", [(3, 0, 0), (0, 2, 0), (0, 0, 5)])
    def test_read_plane_out_of_range(self, fxt_reader, fxt_ome_tiff_factory, z, t, channel):
        path = fxt_ome_tiff_factory(size_t=2, size_c=3, size_z=3)

        with pytest.raises(ValueError, match="out of range"):
            fxt_reader.read_plane(MediaStorage(root=path), z=z, t=t, channels=[channel])

    def test_read_plane_unknown_level(self, fxt_reader, fxt_ome_tiff_factory):
        path = fxt_ome_tiff_factory()

        with pytest.raises(ValueError, match="level"):
            fxt_reader.read_plane(MediaStorage(root=path), z=0, t=0, channels=[0], level=1)
