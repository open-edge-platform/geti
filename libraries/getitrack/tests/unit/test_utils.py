# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Tests for getitrack.utils bbox-format conversions."""

import numpy as np
import pytest

from getitrack.utils import xyah_to_xyxy, xyxy_to_xyah


class TestConversions:
    def test_xyxy_xyah_roundtrip(self):
        boxes = np.array(
            [[10.0, 20.0, 30.0, 60.0], [0.0, 0.0, 100.0, 50.0]],
        )
        xyah = xyxy_to_xyah(boxes)
        back = xyah_to_xyxy(xyah)
        np.testing.assert_allclose(back, boxes, atol=1e-6)

    @pytest.mark.parametrize(
        "box",
        [
            np.array([[0.0, 5.0, 10.0, 5.0]]),
            np.array([[10.0, 0.0, 5.0, 10.0]]),
        ],
    )
    def test_invalid_geometry_raises(self, box):
        with pytest.raises(ValueError, match="positive width and height"):
            xyxy_to_xyah(box)
