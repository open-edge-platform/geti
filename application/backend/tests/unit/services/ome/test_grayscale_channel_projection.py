# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import pytest
from pydantic import ValidationError

from app.models.ome import GrayscaleProjection, OmeImageInfo
from app.services.base import InvalidImageError
from app.services.ome.grayscale_channel_projection import SingleChannelGrayscaleProjectionStrategy
from app.services.ome.protocols import ChannelProjectionStrategy


def _info(size_c: int) -> OmeImageInfo:
    return OmeImageInfo(size_x=5, size_y=4, size_c=size_c, dimension_order="XYCZT", pixel_type="uint16")


@pytest.mark.parametrize("size_c", [1, 3, 5])
def test_default_selects_first_source_channel(size_c):
    strategy: ChannelProjectionStrategy = SingleChannelGrayscaleProjectionStrategy()

    projection = strategy.compute(_info(size_c))

    assert isinstance(projection, GrayscaleProjection)
    assert projection.model_dump(mode="json") == {"mode": "grayscale", "channel": 0}
    assert projection.source_channels == (0,)


@pytest.mark.parametrize(("channel", "size_c"), [(0, 1), (1, 3), (2, 3), (4, 5)])
def test_configured_channel_is_preserved_without_rgb_expansion(channel, size_c):
    projection = SingleChannelGrayscaleProjectionStrategy(channel=channel).compute(_info(size_c))

    assert projection == GrayscaleProjection(channel=channel)
    assert projection.source_channels == (channel,)
    assert len(projection.source_channels) == 1


@pytest.mark.parametrize(("channel", "size_c"), [(1, 1), (3, 3), (4, 3)])
def test_rejects_channel_at_or_above_size_c(channel, size_c):
    strategy = SingleChannelGrayscaleProjectionStrategy(channel=channel)

    with pytest.raises(InvalidImageError, match=f"Grayscale source channel {channel} is outside SizeC"):
        strategy.compute(_info(size_c))


@pytest.mark.parametrize("channel", [-1, -3])
def test_rejects_negative_source_channel(channel):
    with pytest.raises(ValidationError, match="greater than or equal to 0"):
        SingleChannelGrayscaleProjectionStrategy(channel=channel)


def test_selection_does_not_depend_on_wavelength_or_display_metadata():
    info = _info(2).model_copy(
        update={
            "channels": [
                {"index": 0, "emission_wavelength": 650, "color": "#ff0000", "enabled": True},
                {"index": 1, "emission_wavelength": 461, "color": "#0000ff", "enabled": False},
            ]
        }
    )
    original = info.model_dump(mode="json")
    strategy = SingleChannelGrayscaleProjectionStrategy(channel=1)

    assert strategy.compute(info) == strategy.compute(_info(2)) == GrayscaleProjection(channel=1)
    assert info.model_dump(mode="json") == original


def test_reused_strategy_checks_each_images_channel_count():
    strategy = SingleChannelGrayscaleProjectionStrategy(channel=2)

    assert strategy.compute(_info(3)) == GrayscaleProjection(channel=2)
    with pytest.raises(InvalidImageError, match="outside SizeC"):
        strategy.compute(_info(2))
    assert strategy.compute(_info(5)) == GrayscaleProjection(channel=2)
