# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import pytest

from sc_sdk.entities.color import Color

red = 40
red_hex = "28"
green = 210
green_hex = "d2"
blue = 43
blue_hex = "2b"
alpha = 255
alpha_hex = "ff"
color_hex = f"{red_hex}{green_hex}{blue_hex}"

color = Color.from_hex_str(color_hex)


@pytest.mark.ScSdkComponent
class TestColor:
    def test_color(self):
        """
        <b>Description:</b>
        Check that Color can correctly return the value

        <b>Expected results:</b>
        Test passes if the results match
        """

        assert color == Color(red=red, green=green, blue=blue, alpha=alpha)
        assert color.hex_str == f"#{color_hex}{alpha_hex}"
        assert isinstance((color.random()), Color)
        assert color.rgb_tuple == (red, green, blue)
        assert color.bgr_tuple == (blue, green, red)
        assert repr(color) == f"Color(red={red}, green={green}, blue={blue}, alpha={alpha})"
        assert color.red == red
        assert color.green == green
        assert color.blue == blue

        color.red = 68
        color.green = 54
        color.blue = 32
        color.alpha = 0
        assert color.hex_str == "#44362000"
