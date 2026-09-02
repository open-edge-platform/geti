# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Tests for the torchreid ReID provider.

The provider is exercised through an injected fake extractor, so the tests run
without torch/torchreid installed. The fake mimics torchreid's contract: called
with a list of ``(H, W, 3)`` RGB crops, it returns a tensor-like object whose
``detach().cpu().numpy()`` yields the descriptors.
"""

from __future__ import annotations

import numpy as np

from getitrack.reid.torchreid_provider import TorchReIDProvider


class _FakeTensor:
    """Numpy-backed stand-in for a torch tensor (detach/cpu/numpy chain)."""

    def __init__(self, array: np.ndarray) -> None:
        self._array = array

    def detach(self) -> _FakeTensor:
        return self

    def cpu(self) -> _FakeTensor:
        return self

    def numpy(self) -> np.ndarray:
        return self._array


class _FakeExtractor:
    """Records the crops it was called with and returns one row per crop."""

    def __init__(self, dim: int = 16) -> None:
        self.dim = dim
        self.last_crops: list[np.ndarray] | None = None

    def __call__(self, images: list[np.ndarray]) -> _FakeTensor:
        self.last_crops = images
        rows = np.stack([np.full(self.dim, i + 1, dtype=np.float32) for i in range(len(images))])
        return _FakeTensor(rows)


def _provider(dim: int = 16) -> tuple[TorchReIDProvider, _FakeExtractor]:
    extractor = _FakeExtractor(dim=dim)
    return TorchReIDProvider("osnet_x1_0", extractor=extractor), extractor


class TestExtract:
    def test_shape_dtype_and_normalisation(self):
        provider, _ = _provider(dim=16)
        frame = np.zeros((120, 200, 3), dtype=np.uint8)
        boxes = np.array([[10, 10, 60, 90], [100, 20, 180, 110]], dtype=np.float32)
        feats = provider.extract(frame, boxes)
        assert feats.shape == (2, 16)
        assert feats.dtype == np.float32
        assert np.allclose(np.linalg.norm(feats, axis=1), 1.0, atol=1e-5)

    def test_one_crop_per_box(self):
        provider, extractor = _provider()
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        provider.extract(frame, np.array([[0, 0, 10, 10], [20, 20, 40, 40], [5, 5, 15, 15]], dtype=np.float32))
        assert extractor.last_crops is not None
        assert len(extractor.last_crops) == 3

    def test_crops_are_rgb_contiguous(self):
        provider, extractor = _provider()
        # Distinct per-channel values in BGR: B=10, G=20, R=200.
        frame = np.zeros((50, 50, 3), dtype=np.uint8)
        frame[:, :, 0], frame[:, :, 1], frame[:, :, 2] = 10, 20, 200
        provider.extract(frame, np.array([[0, 0, 20, 20]], dtype=np.float32))
        assert extractor.last_crops is not None
        crop = extractor.last_crops[0]
        assert crop.flags["C_CONTIGUOUS"]
        # After BGR->RGB the first channel is R (200), the last is B (10).
        assert crop[0, 0, 0] == 200
        assert crop[0, 0, 2] == 10

    def test_empty_boxes_before_first_infer(self):
        provider, _ = _provider(dim=16)
        feats = provider.extract(np.zeros((10, 10, 3), dtype=np.uint8), np.empty((0, 4), dtype=np.float32))
        # Feature width is unknown before the first inference, so it is 0.
        assert feats.shape == (0, 0)

    def test_empty_boxes_after_first_infer_uses_known_dim(self):
        provider, _ = _provider(dim=16)
        provider.extract(np.zeros((60, 60, 3), dtype=np.uint8), np.array([[0, 0, 30, 30]], dtype=np.float32))
        feats = provider.extract(np.zeros((10, 10, 3), dtype=np.uint8), np.empty((0, 4), dtype=np.float32))
        assert feats.shape == (0, 16)

    def test_degenerate_box_does_not_crash(self):
        provider, extractor = _provider()
        frame = np.zeros((50, 50, 3), dtype=np.uint8)
        # Zero-area and out-of-bounds boxes are clamped to a 1-pixel crop.
        feats = provider.extract(frame, np.array([[10, 10, 10, 10], [-5, -5, 3, 3]], dtype=np.float32))
        assert feats.shape == (2, 16)
        assert extractor.last_crops is not None
        assert all(crop.size > 0 for crop in extractor.last_crops)
