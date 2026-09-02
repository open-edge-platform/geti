# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Tests for the bounded per-track appearance gallery and EMA."""

import numpy as np
import pytest

from getitrack.reid.gallery import AppearanceGallery


def _gallery(**overrides) -> AppearanceGallery:
    params = {"gallery_size": 3, "use_ema": False, "ema_alpha": 0.9, "admission_threshold": 10.0}
    params.update(overrides)
    return AppearanceGallery(**params)


class TestBoundedFIFO:
    def test_gallery_is_bounded_and_fifo(self):
        gallery = _gallery(gallery_size=3, use_ema=False)
        feats = [np.array([np.cos(t), np.sin(t)], dtype=np.float32) for t in np.linspace(0.0, 1.0, 5)]
        for f in feats:
            gallery.update(f)
        # Capacity is respected: only the last 3 descriptors are retained.
        assert len(gallery) == 3
        # The two most-recently-added features are near-zero distance; the
        # evicted earliest one is farther, confirming FIFO eviction order.
        assert float(gallery.distance(feats[4][None, :])[0]) == pytest.approx(0.0, abs=1e-5)
        assert float(gallery.distance(feats[2][None, :])[0]) == pytest.approx(0.0, abs=1e-5)
        assert float(gallery.distance(feats[0][None, :])[0]) > 1e-3

    def test_empty_gallery_reports_nan_distance(self):
        gallery = _gallery()
        assert gallery.is_empty
        dist = gallery.distance(np.array([[1.0, 0.0]], dtype=np.float32))
        assert np.isnan(dist[0])


class TestAdmissionGate:
    def test_dissimilar_feature_is_rejected(self):
        gallery = _gallery(gallery_size=5, use_ema=False, admission_threshold=0.2)
        assert gallery.update(np.array([1.0, 0.0], dtype=np.float32)) is True
        # Orthogonal (distance ~1.0) exceeds the 0.2 gate and is rejected.
        assert gallery.update(np.array([0.0, 1.0], dtype=np.float32)) is False
        assert len(gallery) == 1


class TestEMA:
    def test_ema_update_math(self):
        gallery = _gallery(use_ema=True, ema_alpha=0.9, admission_threshold=2.0)
        gallery.update(np.array([1.0, 0.0], dtype=np.float32), confidence=1.0)
        gallery.update(np.array([0.0, 1.0], dtype=np.float32), confidence=1.0)
        # w = (1 - 0.9) * 1.0 = 0.1 -> raw = 0.9*[1,0] + 0.1*[0,1] = [0.9, 0.1], then L2-normalised.
        expected = np.array([0.9, 0.1], dtype=np.float32)
        expected /= np.linalg.norm(expected)
        # distance to the (unnormalised) raw direction is ~0 since cosine ignores scale.
        assert float(gallery.distance(expected[None, :])[0]) == pytest.approx(0.0, abs=1e-5)

    def test_confidence_scales_ema_step(self):
        gallery = _gallery(use_ema=True, ema_alpha=0.9, admission_threshold=2.0)
        gallery.update(np.array([1.0, 0.0], dtype=np.float32), confidence=1.0)
        gallery.update(np.array([0.0, 1.0], dtype=np.float32), confidence=0.5)
        # w = (1 - 0.9) * 0.5 = 0.05 -> raw = 0.95*[1,0] + 0.05*[0,1] = [0.95, 0.05].
        expected = np.array([0.95, 0.05], dtype=np.float32)
        assert float(gallery.distance(expected[None, :])[0]) == pytest.approx(0.0, abs=1e-5)

    def test_ema_mode_matches_the_running_feature(self):
        gallery = _gallery(use_ema=True, ema_alpha=0.5, admission_threshold=2.0)
        gallery.update(np.array([1.0, 0.0], dtype=np.float32))
        assert float(gallery.distance(np.array([[1.0, 0.0]], dtype=np.float32))[0]) == pytest.approx(0.0, abs=1e-5)


class TestGallerySizeEffect:
    """`gallery_size` must actually change matching, in both modes."""

    def test_smaller_gallery_forgets_older_features(self):
        # use_ema=False: only the FIFO is queried, so eviction is directly visible.
        feats = [
            np.array([1.0, 0.0], dtype=np.float32),
            np.array([0.0, 1.0], dtype=np.float32),
            np.array([-1.0, 0.0], dtype=np.float32),
        ]
        big = _gallery(gallery_size=3, use_ema=False, admission_threshold=10.0)
        small = _gallery(gallery_size=1, use_ema=False, admission_threshold=10.0)
        for f in feats:
            big.update(f)
            small.update(f)
        # The size-3 gallery still recognises the earliest feature; the size-1
        # gallery has evicted everything but the most recent one.
        assert float(big.distance(feats[0][None, :])[0]) == pytest.approx(0.0, abs=1e-5)
        assert float(small.distance(feats[0][None, :])[0]) > 0.1

    def test_fifo_is_queried_in_ema_mode_too(self):
        # In EMA mode the FIFO entries are also representatives, so a raw feature
        # still in the gallery is matchable even when the EMA has drifted away.
        gallery = _gallery(gallery_size=5, use_ema=True, ema_alpha=0.9, admission_threshold=2.0)
        gallery.update(np.array([1.0, 0.0], dtype=np.float32))
        gallery.update(np.array([0.0, 1.0], dtype=np.float32))
        # The EMA is dominated by [1, 0], but [0, 1] is retained in the FIFO.
        assert float(gallery.distance(np.array([[0.0, 1.0]], dtype=np.float32))[0]) == pytest.approx(0.0, abs=1e-5)
