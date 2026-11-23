# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import pytest

from app.models.ome import OmeImageInfo, RgbProjection
from app.services.base import InvalidImageError
from app.services.ome.rgb_channel_projection import MetadataRgbChannelProjectionStrategy


def _info(size_c, channels=None):
    return OmeImageInfo(
        size_x=5,
        size_y=4,
        size_c=size_c,
        dimension_order="XYCZT",
        pixel_type="uint16",
        channels=channels or [],
    )


@pytest.mark.parametrize("size_c", [1, 2, 3, 5])
def test_fallback_channel_projection(size_c):
    projection = MetadataRgbChannelProjectionStrategy().compute(_info(size_c))

    assert isinstance(projection, RgbProjection)
    assert projection.model_dump(mode="json") == {
        "mode": "rgb",
        "channels": [
            {"channel": index, "target": target}
            for index, target in enumerate(("red", "green", "blue")[: min(size_c, 3)])
        ],
    }
    assert projection.source_channels == tuple(range(min(size_c, 3)))


def test_wavelength_projection_precedes_rgb_identity():
    assert MetadataRgbChannelProjectionStrategy().compute(
        _info(
            3,
            [
                {"index": 0, "emission_wavelength": 461, "color": "#0000ff"},
                {"index": 1, "emission_wavelength": 510, "color": "#00ff00"},
                {"index": 2, "emission_wavelength": 650, "color": "#ff0000"},
            ],
        )
    ).model_dump(mode="json")["channels"] == [
        {"channel": 2, "target": "red"},
        {"channel": 1, "target": "green"},
        {"channel": 0, "target": "blue"},
    ]


def test_wavelength_collision_prefers_color_then_index():
    info = _info(
        4,
        [
            {"index": 0, "emission_wavelength": 650, "color": "#aa8800"},
            {"index": 1, "emission_wavelength": 660, "color": "#ff0000"},
            {"index": 2, "emission_wavelength": 0.670, "emission_wavelength_unit": "um", "color": "#ff0000"},
            {"index": 3, "emission_wavelength": 520, "color": "#00ff00"},
        ],
    )
    assert MetadataRgbChannelProjectionStrategy().compute(info).model_dump(mode="json")["channels"] == [
        {"channel": 1, "target": "red"},
        {"channel": 3, "target": "green"},
    ]


@pytest.mark.parametrize("wavelength", [None, "520", 0, -1, float("nan"), float("inf"), -float("inf")])
def test_incomplete_or_invalid_wavelengths_use_fallback(wavelength):
    info = _info(
        2,
        [
            {"index": 0, "emission_wavelength": 460},
            {"index": 1, "emission_wavelength": wavelength},
        ],
    )
    assert MetadataRgbChannelProjectionStrategy().compute(info).model_dump(mode="json")["channels"] == [
        {"channel": 0, "target": "red"},
        {"channel": 1, "target": "green"},
    ]


@pytest.mark.parametrize(
    ("wavelength", "target"),
    [(499.9, "blue"), (500, "green"), (580, "green"), (580.1, "red")],
)
def test_wavelength_boundaries(wavelength, target):
    projection = MetadataRgbChannelProjectionStrategy().compute(
        _info(1, [{"index": 0, "emission_wavelength": wavelength}])
    )

    assert projection.model_dump(mode="json") == {"mode": "rgb", "channels": [{"channel": 0, "target": target}]}


@pytest.mark.parametrize(
    ("wavelength", "unit"),
    [(520, "nm"), (0.52, "\u00b5m"), (0.52, "um"), (0.00052, "mm"), (5.2e-7, "m"), (520000, "pm")],
)
def test_wavelength_unit_conversion(wavelength, unit):
    projection = MetadataRgbChannelProjectionStrategy().compute(
        _info(1, [{"index": 0, "emission_wavelength": wavelength, "emission_wavelength_unit": unit}])
    )

    assert projection.channels[0].target == "green"


@pytest.mark.parametrize(
    "channels",
    [
        [{"index": 0}],
        [{"index": 0, "emission_wavelength": 520}],
        [{"emission_wavelength": 520}, {"index": 1, "emission_wavelength": 650}],
        [{"index": "0", "emission_wavelength": 520}, {"index": 1, "emission_wavelength": 650}],
        [
            {"index": 0, "emission_wavelength": 520, "emission_wavelength_unit": "unsupported"},
            {"index": 1, "emission_wavelength": 650},
        ],
    ],
)
def test_incomplete_metadata_uses_index_order(channels):
    projection = MetadataRgbChannelProjectionStrategy().compute(_info(2, channels))

    assert projection.model_dump(mode="json")["channels"] == [
        {"channel": 0, "target": "red"},
        {"channel": 1, "target": "green"},
    ]


@pytest.mark.parametrize("color", [None, "#808080"])
def test_collision_without_color_signal_prefers_lowest_source_index(color):
    info = _info(
        2,
        [
            {"index": 1, "emission_wavelength": 650, "color": color},
            {"index": 0, "emission_wavelength": 660, "color": color},
        ],
    )

    projection = MetadataRgbChannelProjectionStrategy().compute(info)

    assert projection.source_channels == (0,)
    assert projection.channels[0].target == "red"


def test_red_hue_collision_uses_circular_distance():
    info = _info(
        2,
        [
            {"index": 0, "emission_wavelength": 650, "color": "#ff8000"},
            {"index": 1, "emission_wavelength": 660, "color": "#ff0010"},
        ],
    )

    assert MetadataRgbChannelProjectionStrategy().compute(info).source_channels == (1,)


def test_wavelength_projection_can_select_channels_beyond_first_three():
    info = _info(
        4,
        [
            {"index": 0, "emission_wavelength": 650, "color": "#ff8000"},
            {"index": 1, "emission_wavelength": 520},
            {"index": 2, "emission_wavelength": 461},
            {"index": 3, "emission_wavelength": 660, "color": "#ff0000"},
        ],
    )

    projection = MetadataRgbChannelProjectionStrategy().compute(info)

    assert projection.source_channels == (3, 1, 2)


def test_invalid_hex_color_raises_explicit_error():
    info = _info(1, [{"index": 0, "emission_wavelength": 650, "color": "#gg0000"}])

    with pytest.raises(InvalidImageError, match="Invalid OME channel color"):
        MetadataRgbChannelProjectionStrategy().compute(info)


def test_projection_is_deterministic_and_does_not_mutate_metadata():
    info = _info(
        3,
        [
            {"index": 0, "emission_wavelength": 461},
            {"index": 1, "emission_wavelength": 650},
            {"index": 2, "emission_wavelength": 520},
        ],
    )
    original = info.model_dump(mode="json")
    strategy = MetadataRgbChannelProjectionStrategy()

    first = strategy.compute(info)
    second = strategy.compute(info)
    reordered = strategy.compute(info.model_copy(update={"channels": list(reversed(info.channels))}))

    assert first == second == reordered
    assert info.model_dump(mode="json") == original
