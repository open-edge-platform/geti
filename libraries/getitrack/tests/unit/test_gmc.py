# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Tests for the global motion compensation (camera-motion) estimators."""

from __future__ import annotations

import numpy as np
import pytest

from getitrack.config import GMCConfig, GMCMethod
from getitrack.motion.gmc import (
    BaseMotionEstimator,
    ECCEstimator,
    ORBEstimator,
    SIFTEstimator,
    SparseOptFlowEstimator,
)

_IDENTITY = np.eye(2, 3, dtype=np.float32)


def _textured(height: int = 200, width: int = 200) -> np.ndarray:
    """A corner-rich frame: bright squares scattered on a dark background."""
    rng = np.random.default_rng(0)
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    for _ in range(80):
        y = int(rng.integers(6, height - 8))
        x = int(rng.integers(6, width - 8))
        frame[y : y + 4, x : x + 4] = 255
    return frame


def _rich_scene(size: int = 240) -> np.ndarray:
    """A scene of varied-size, varied-intensity rectangles with distinct corners.

    The distinct grey levels give descriptor-based methods (ORB/SIFT) unambiguous
    matches that survive the ratio test.
    """
    rng = np.random.default_rng(3)
    frame = np.full((size, size, 3), 40, dtype=np.uint8)
    for _ in range(70):
        x, y = int(rng.integers(10, size - 30)), int(rng.integers(10, size - 30))
        w, h = int(rng.integers(6, 26)), int(rng.integers(6, 26))
        frame[y : y + h, x : x + w] = int(rng.integers(80, 256))
    return frame


class TestFromConfig:
    def test_dispatches_by_method(self):
        cases = [
            (GMCMethod.SPARSE_OPT_FLOW, SparseOptFlowEstimator),
            (GMCMethod.ECC, ECCEstimator),
            (GMCMethod.ORB, ORBEstimator),
            (GMCMethod.SIFT, SIFTEstimator),
        ]
        for method, expected in cases:
            assert isinstance(BaseMotionEstimator.from_config(GMCConfig(method=method)), expected)

    def test_passes_downscale(self):
        estimator = BaseMotionEstimator.from_config(GMCConfig(downscale=4))
        assert estimator._downscale == 4


class TestFirstFrameAndReset:
    def test_first_frame_is_identity(self):
        estimator = SparseOptFlowEstimator(downscale=1)
        assert np.array_equal(estimator.estimate(_textured()), _IDENTITY)

    def test_reset_returns_to_identity(self):
        estimator = SparseOptFlowEstimator(downscale=1)
        estimator.estimate(_textured())
        estimator.reset()
        assert np.array_equal(estimator.estimate(_textured()), _IDENTITY)


class TestTranslationRecovery:
    def test_sparse_optflow_recovers_shift(self):
        estimator = SparseOptFlowEstimator(downscale=1)
        base = _textured()
        shifted = np.roll(base, shift=7, axis=1)  # content moves +7 in x
        estimator.estimate(base)
        warp = estimator.estimate(shifted)
        assert warp[0, 2] == pytest.approx(7.0, abs=2.0)
        assert warp[1, 2] == pytest.approx(0.0, abs=2.0)

    def test_downscale_rescales_translation(self):
        estimator = SparseOptFlowEstimator(downscale=2)
        base = _textured()
        shifted = np.roll(base, shift=8, axis=1)
        estimator.estimate(base)
        warp = estimator.estimate(shifted)
        # Estimation runs at half resolution; the returned translation is in
        # full-resolution pixels, so it should still recover ~8 not ~4.
        assert warp[0, 2] == pytest.approx(8.0, abs=2.5)

    def test_large_downscale_on_small_frame_does_not_crash(self):
        # A downscale larger than the frame would floor a resize dimension to
        # zero (and OpenCV would raise) without the clamp; estimate must run.
        estimator = SparseOptFlowEstimator(downscale=32)
        assert np.array_equal(estimator.estimate(_textured(height=20, width=20)), _IDENTITY)
        warp = estimator.estimate(_textured(height=20, width=20))
        assert warp.shape == (2, 3)


class TestECC:
    def test_returns_affine_shape(self):
        estimator = ECCEstimator(downscale=1)
        estimator.estimate(_textured())
        warp = estimator.estimate(np.roll(_textured(), shift=4, axis=1))
        assert warp.shape == (2, 3)
        assert warp.dtype == np.float32
        assert np.all(np.isfinite(warp))


class TestFeatureMethods:
    @pytest.mark.parametrize("estimator_cls", [ORBEstimator, SIFTEstimator])
    def test_first_frame_is_identity(self, estimator_cls):
        estimator = estimator_cls(downscale=1)
        assert np.array_equal(estimator.estimate(_rich_scene()), _IDENTITY)

    @pytest.mark.parametrize("estimator_cls", [ORBEstimator, SIFTEstimator])
    def test_recovers_translation(self, estimator_cls):
        estimator = estimator_cls(downscale=1)
        base = _rich_scene()
        shifted = np.roll(base, shift=7, axis=1)
        estimator.estimate(base)
        warp = estimator.estimate(shifted)
        assert warp[0, 2] == pytest.approx(7.0, abs=2.0)
        assert warp[1, 2] == pytest.approx(0.0, abs=2.0)

    def test_low_texture_frame_falls_back_to_identity(self):
        # A blank frame yields no keypoints; the estimate must not raise.
        estimator = ORBEstimator(downscale=1)
        blank = np.zeros((120, 120, 3), dtype=np.uint8)
        estimator.estimate(blank)
        assert np.array_equal(estimator.estimate(blank), _IDENTITY)
