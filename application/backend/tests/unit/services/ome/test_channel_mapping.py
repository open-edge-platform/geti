# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
import pytest

from app.models.ome import OmeChannel, OmeContainerFormat, OmeImageInfo, RgbTarget
from app.services.ome.channel_mapping import compute_training_channel_mapping, declared_value_range


def _info(channels: list[OmeChannel], pixel_type: str = "uint8", significant_bits: int | None = None) -> OmeImageInfo:
    return OmeImageInfo(
        container_format=OmeContainerFormat.OME_TIFF,
        size_x=8,
        size_y=8,
        size_c=len(channels),
        dimension_order="XYCZT",
        pixel_type=pixel_type,
        significant_bits=significant_bits,
        channels=channels,
        channel_mapping=[],
        pyramid_levels=[],
    )


def _channels(count: int) -> list[OmeChannel]:
    return [OmeChannel(index=index) for index in range(count)]


def _no_sample() -> tuple[float, float]:
    raise AssertionError("The image should not be sampled for integer pixel types")


def _pairs(info: OmeImageInfo) -> list[tuple[int, RgbTarget]]:
    return [(m.channel, m.target) for m in compute_training_channel_mapping(info, _no_sample)]


class TestDeclaredValueRange:
    @pytest.mark.parametrize(
        "pixel_type, significant_bits, expected",
        [
            ("uint8", None, (0.0, 255.0)),
            ("uint16", None, (0.0, 65535.0)),
            ("uint16", 12, (0.0, 4095.0)),
            ("int16", None, (-32768.0, 32767.0)),
            ("bit", None, (0.0, 1.0)),
            ("float", None, None),
            ("double", None, None),
        ],
    )
    def test_declared_value_range(self, pixel_type, significant_bits, expected):
        assert declared_value_range(pixel_type, significant_bits) == expected


class TestComputeTrainingChannelMapping:
    def test_three_channels_identity(self):
        assert _pairs(_info(_channels(3))) == [(0, RgbTarget.RED), (1, RgbTarget.GREEN), (2, RgbTarget.BLUE)]

    def test_wavelength_mapping_reorders_channels(self):
        # DAPI (blue), GFP (green), Cy5 (red) stored in an order that a naive identity mapping would get wrong
        channels = [
            OmeChannel(index=0, name="Cy5", emission_wavelength=670),
            OmeChannel(index=1, name="DAPI", emission_wavelength=461),
            OmeChannel(index=2, name="GFP", emission_wavelength=510),
        ]

        assert _pairs(_info(channels)) == [(0, RgbTarget.RED), (2, RgbTarget.GREEN), (1, RgbTarget.BLUE)]

    def test_wavelength_collision_prefers_declared_color(self):
        channels = [
            OmeChannel(index=0, emission_wavelength=600, color="#ffff00"),
            OmeChannel(index=1, emission_wavelength=650, color="#ff0000"),
            OmeChannel(index=2, emission_wavelength=460),
        ]

        assert _pairs(_info(channels)) == [(1, RgbTarget.RED), (2, RgbTarget.BLUE)]

    def test_more_than_three_channels_without_wavelength_keeps_first_three(self):
        assert _pairs(_info(_channels(5))) == [(0, RgbTarget.RED), (1, RgbTarget.GREEN), (2, RgbTarget.BLUE)]

    def test_two_channels_pads_blue(self):
        assert _pairs(_info(_channels(2))) == [(0, RgbTarget.RED), (1, RgbTarget.GREEN)]

    def test_single_channel_is_grayscale(self):
        assert _pairs(_info(_channels(1))) == [(0, RgbTarget.RED), (0, RgbTarget.GREEN), (0, RgbTarget.BLUE)]

    def test_window_uses_declared_range(self):
        mapping = compute_training_channel_mapping(_info(_channels(3), "uint16", significant_bits=12), _no_sample)

        assert {(m.window_min, m.window_max) for m in mapping} == {(0.0, 4095.0)}

    def test_window_samples_float_images(self):
        mapping = compute_training_channel_mapping(_info(_channels(3), "float"), lambda: (-1.5, 2.5))

        assert {(m.window_min, m.window_max) for m in mapping} == {(-1.5, 2.5)}

    def test_window_of_constant_float_image_is_widened(self):
        mapping = compute_training_channel_mapping(_info(_channels(3), "float"), lambda: (3.0, 3.0))

        assert {(m.window_min, m.window_max) for m in mapping} == {(3.0, 4.0)}
