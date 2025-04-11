# INTEL CONFIDENTIAL
#
# Copyright (C) 2024 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and
# your use of them is governed by the express license under which they were provided to
# you ("License"). Unless the License provides otherwise, you may not use, modify, copy,
# publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is,
# with no express or implied warranties, other than those that are expressly stated
# in the License.

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
