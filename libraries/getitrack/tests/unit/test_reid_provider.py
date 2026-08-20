# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Tests for the ReID feature-provider layer.

The abstract contract and fusion wiring are checked with a lightweight mock so
they run without any inference backend. The OpenVINO provider is exercised
against a tiny CNN exported to IR at test time, so no pretrained weights are
required; it is skipped when ``torch``/``openvino`` are unavailable.
"""

from __future__ import annotations

import numpy as np
import pytest

from getitrack.matching.appearance import l2_normalize
from getitrack.reid.base import ReIDProvider


class _MockReIDProvider(ReIDProvider):
    """Deterministic provider: embeds each box by its geometry, then normalises."""

    def __init__(self, dim: int = 8) -> None:
        self._dim = dim
        self._rng = np.random.default_rng(0)

    def extract(self, frame_bgr: np.ndarray, boxes: np.ndarray) -> np.ndarray:
        box_array = np.asarray(boxes, dtype=np.float32).reshape(-1, 4)
        if box_array.shape[0] == 0:
            return np.empty((0, self._dim), dtype=np.float32)
        raw = self._rng.random((box_array.shape[0], self._dim)).astype(np.float32)
        return l2_normalize(raw)


class TestAbstractContract:
    def test_cannot_instantiate_abstract_base(self):
        with pytest.raises(TypeError):
            ReIDProvider()  # type: ignore[abstract]  # pyrefly: ignore[bad-instantiation]

    def test_mock_returns_normalised_features(self):
        provider = _MockReIDProvider(dim=8)
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        boxes = np.array([[0, 0, 10, 10], [20, 20, 40, 40]], dtype=np.float32)
        feats = provider.extract(frame, boxes)
        assert feats.shape == (2, 8)
        assert feats.dtype == np.float32
        assert np.allclose(np.linalg.norm(feats, axis=1), 1.0, atol=1e-5)

    def test_mock_handles_empty_boxes(self):
        provider = _MockReIDProvider(dim=8)
        frame = np.zeros((10, 10, 3), dtype=np.uint8)
        feats = provider.extract(frame, np.empty((0, 4), dtype=np.float32))
        assert feats.shape == (0, 8)


class TestOpenVINOProvider:
    @staticmethod
    def _export_tiny_ir(tmp_path, height: int, width: int, out_dim: int) -> str:
        torch = pytest.importorskip("torch")
        ov = pytest.importorskip("openvino")
        from torch import nn

        class _TinyReID(nn.Module):
            def __init__(self) -> None:
                super().__init__()
                self.conv = nn.Conv2d(3, 8, kernel_size=3, padding=1)
                self.pool = nn.AdaptiveAvgPool2d(1)
                self.fc = nn.Linear(8, out_dim)

            def forward(self, x: torch.Tensor) -> torch.Tensor:
                x = torch.relu(self.conv(x))
                x = self.pool(x).flatten(1)
                return self.fc(x)

        model = _TinyReID().eval()
        ov_model = ov.convert_model(model, example_input=torch.zeros(1, 3, height, width))
        xml_path = tmp_path / "tiny_reid.xml"
        ov.save_model(ov_model, str(xml_path))
        return str(xml_path)

    def test_extract_shape_dtype_and_normalisation(self, tmp_path):
        pytest.importorskip("torch")
        pytest.importorskip("openvino")
        from getitrack.reid.openvino_provider import OpenVINOReIDProvider

        height, width, out_dim = 64, 32, 16
        xml_path = self._export_tiny_ir(tmp_path, height, width, out_dim)
        provider = OpenVINOReIDProvider(xml_path, input_size=(height, width))
        rng = np.random.default_rng(1)
        frame = (rng.random((120, 200, 3)) * 255).astype(np.uint8)
        boxes = np.array([[10, 10, 60, 90], [100, 20, 180, 110]], dtype=np.float32)
        feats = provider.extract(frame, boxes)
        assert feats.shape == (2, out_dim)
        assert feats.dtype == np.float32
        assert np.allclose(np.linalg.norm(feats, axis=1), 1.0, atol=1e-4)

    def test_degenerate_box_does_not_crash(self, tmp_path):
        pytest.importorskip("torch")
        pytest.importorskip("openvino")
        from getitrack.reid.openvino_provider import OpenVINOReIDProvider

        xml_path = self._export_tiny_ir(tmp_path, 64, 32, 16)
        provider = OpenVINOReIDProvider(xml_path, input_size=(64, 32))
        frame = np.zeros((50, 50, 3), dtype=np.uint8)
        # Zero-area and out-of-bounds boxes are clamped, not rejected.
        boxes = np.array([[10, 10, 10, 10], [-5, -5, 3, 3]], dtype=np.float32)
        feats = provider.extract(frame, boxes)
        assert feats.shape == (2, 16)

    def test_empty_boxes_before_first_infer(self, tmp_path):
        pytest.importorskip("torch")
        pytest.importorskip("openvino")
        from getitrack.reid.openvino_provider import OpenVINOReIDProvider

        xml_path = self._export_tiny_ir(tmp_path, 64, 32, 16)
        provider = OpenVINOReIDProvider(xml_path, input_size=(64, 32))
        feats = provider.extract(np.zeros((10, 10, 3), dtype=np.uint8), np.empty((0, 4), dtype=np.float32))
        # Feature width is unknown before the first inference, so it is 0.
        assert feats.shape == (0, 0)

    def test_requires_a_source(self):
        from getitrack.reid.openvino_provider import OpenVINOReIDProvider

        with pytest.raises(ValueError, match="model_path or compiled_model"):
            OpenVINOReIDProvider()
