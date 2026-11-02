# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
import numpy as np
import pytest

from app.models.ome import (
    ChannelDisplaySetting,
    ChannelMapping,
    OmeChannel,
    OmeContainerFormat,
    OmeImageInfo,
    RgbTarget,
)
from app.services.ome.rendering import (
    InvalidChannelSettingsError,
    apply_window,
    compose_rgb,
    default_display_settings,
    settings_hash,
    validate_display_settings,
)


def _info(size_c: int, channel_mapping: list[ChannelMapping]) -> OmeImageInfo:
    return OmeImageInfo(
        container_format=OmeContainerFormat.OME_TIFF,
        size_x=4,
        size_y=4,
        size_c=size_c,
        dimension_order="XYCZT",
        pixel_type="uint16",
        channels=[OmeChannel(index=index) for index in range(size_c)],
        channel_mapping=channel_mapping,
        pyramid_levels=[],
    )


class TestApplyWindow:
    @pytest.mark.parametrize(
        "value, expected",
        [
            pytest.param(50, 0, id="below_min_clipped"),
            pytest.param(100, 0, id="at_min"),
            pytest.param(150, 128, id="midpoint"),
            pytest.param(200, 255, id="at_max"),
            pytest.param(4000, 255, id="above_max_clipped"),
        ],
    )
    def test_apply_window(self, value, expected):
        result = apply_window(np.array([[value]], dtype=np.uint16), window_min=100, window_max=200)

        assert result.dtype == np.uint8
        assert result[0, 0] == expected


class TestComposeRgb:
    def test_compose_maps_channels_to_targets(self):
        data = {0: np.full((2, 2), 255.0), 1: np.full((2, 2), 0.0)}
        mappings = [
            ChannelMapping(channel=0, target=RgbTarget.BLUE, window_min=0, window_max=255),
            ChannelMapping(channel=1, target=RgbTarget.RED, window_min=0, window_max=255),
        ]

        rgb = compose_rgb(data, mappings)

        assert rgb.shape == (2, 2, 3)
        assert rgb[0, 0].tolist() == [0, 0, 255]

    def test_disabled_channel_contributes_nothing(self):
        data = {0: np.full((2, 2), 255.0)}
        settings = [
            ChannelDisplaySetting(channel=0, target=RgbTarget.GREEN, window_min=0, window_max=255, enabled=False)
        ]

        assert compose_rgb(data, settings).max() == 0

    def test_same_channel_on_all_targets_is_grayscale(self):
        data = {0: np.full((2, 2), 128.0)}
        mappings = [ChannelMapping(channel=0, target=target, window_min=0, window_max=255) for target in RgbTarget]

        assert compose_rgb(data, mappings)[0, 0].tolist() == [128, 128, 128]


class TestDisplaySettings:
    def test_default_settings_auto_contrast_and_list_unmapped_channels(self):
        info = _info(
            size_c=2,
            channel_mapping=[ChannelMapping(channel=0, target=RgbTarget.RED, window_min=0, window_max=65535)],
        )
        samples = {0: np.arange(1000, 2001, dtype=np.uint16), 1: np.zeros(10, dtype=np.uint16)}

        settings = default_display_settings(info, samples)

        assert [(s.channel, s.target, s.enabled) for s in settings] == [
            (0, RgbTarget.RED, True),
            (1, RgbTarget.GREEN, False),
        ]
        assert 1000 <= settings[0].window_min < settings[0].window_max <= 2000

    def test_default_settings_fall_back_to_training_window_for_constant_channel(self):
        info = _info(
            size_c=1,
            channel_mapping=[ChannelMapping(channel=0, target=RgbTarget.RED, window_min=0, window_max=4095)],
        )

        settings = default_display_settings(info, {0: np.full(10, 7, dtype=np.uint16)})

        assert (settings[0].window_min, settings[0].window_max) == (0, 4095)

    def test_validate_rejects_out_of_range_channel(self):
        settings = [ChannelDisplaySetting(channel=3, target=RgbTarget.RED, window_min=0, window_max=1)]

        with pytest.raises(InvalidChannelSettingsError, match="does not exist"):
            validate_display_settings(_info(size_c=3, channel_mapping=[]), settings)

    def test_validate_rejects_duplicate_enabled_target(self):
        settings = [
            ChannelDisplaySetting(channel=0, target=RgbTarget.RED, window_min=0, window_max=1),
            ChannelDisplaySetting(channel=1, target=RgbTarget.RED, window_min=0, window_max=1),
        ]

        with pytest.raises(InvalidChannelSettingsError, match="same RGB target"):
            validate_display_settings(_info(size_c=3, channel_mapping=[]), settings)

    def test_validate_allows_duplicate_target_when_disabled(self):
        settings = [
            ChannelDisplaySetting(channel=0, target=RgbTarget.RED, window_min=0, window_max=1),
            ChannelDisplaySetting(channel=1, target=RgbTarget.RED, window_min=0, window_max=1, enabled=False),
        ]

        validate_display_settings(_info(size_c=3, channel_mapping=[]), settings)

    def test_window_min_must_be_below_window_max(self):
        with pytest.raises(ValueError, match="window_min"):
            ChannelDisplaySetting(channel=0, target=RgbTarget.RED, window_min=5, window_max=5)

    def test_settings_hash_changes_with_settings(self):
        base = [ChannelDisplaySetting(channel=0, target=RgbTarget.RED, window_min=0, window_max=10)]
        changed = [ChannelDisplaySetting(channel=0, target=RgbTarget.RED, window_min=0, window_max=11)]

        assert settings_hash(base) == settings_hash(list(base))
        assert settings_hash(base) != settings_hash(changed)
