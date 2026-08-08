# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Tests for getitrack.utils bbox-format conversions."""

import numpy as np
import pytest

from getitrack.utils import cxcywh_to_xyxy, xyah_to_xyxy, xyxy_to_cxcywh, xyxy_to_xyah


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

    def test_xyxy_cxcywh_roundtrip(self):
        boxes = np.array([[10.0, 20.0, 30.0, 60.0], [0.0, 0.0, 100.0, 50.0]])
        back = cxcywh_to_xyxy(xyxy_to_cxcywh(boxes))
        np.testing.assert_allclose(back, boxes, atol=1e-6)

    def test_xyxy_to_cxcywh_known_values(self):
        # [x1, y1, x2, y2] -> [cx, cy, w, h]; unlike xyah, size is width not aspect.
        got = xyxy_to_cxcywh(np.array([[10.0, 20.0, 30.0, 60.0]]))
        np.testing.assert_allclose(got, [[20.0, 40.0, 20.0, 40.0]], atol=1e-6)

    def test_cxcywh_tolerates_zero_area(self):
        # No aspect division, so a zero-size box round-trips without raising.
        np.testing.assert_allclose(
            cxcywh_to_xyxy(xyxy_to_cxcywh(np.array([[5.0, 5.0, 5.0, 5.0]]))), [[5.0, 5.0, 5.0, 5.0]]
        )
