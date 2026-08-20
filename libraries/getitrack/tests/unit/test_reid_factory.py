# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Tests for `build_reid_provider` backend dispatch.

The provider classes and the export bridge are monkeypatched, so dispatch is
verified without torch/torchreid/openvino installed: the tests assert which
backend is chosen and with what arguments.
"""

from __future__ import annotations

import warnings
from pathlib import Path

import pytest

from getitrack.config import ReIDBackend, ReIDConfig
from getitrack.reid.factory import _torch_device, build_reid_provider


class TestDispatch:
    def test_disabled_returns_none(self):
        assert build_reid_provider(ReIDConfig(enabled=False)) is None

    def test_enabled_without_source_returns_none(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            cfg = ReIDConfig(enabled=True)
        assert build_reid_provider(cfg) is None

    def test_torch_requires_model_name(self):
        cfg = ReIDConfig(enabled=True, backend=ReIDBackend.TORCH, model_path=Path("weights.pth.tar"))
        with pytest.raises(ValueError, match="requires model_name"):
            build_reid_provider(cfg)

    def test_torch_dispatch(self, monkeypatch):
        captured: dict[str, object] = {}

        def fake_torch(model_name, *, weights_path, device, input_size) -> str:
            captured.update(model_name=model_name, weights_path=weights_path, device=device, input_size=input_size)
            return "TORCH_PROVIDER"

        monkeypatch.setattr("getitrack.reid.torchreid_provider.TorchReIDProvider", fake_torch)
        cfg = ReIDConfig(
            enabled=True, backend=ReIDBackend.TORCH, model_name="osnet_x1_0", device="CPU", input_size=(128, 64)
        )
        assert build_reid_provider(cfg) == "TORCH_PROVIDER"
        assert captured["model_name"] == "osnet_x1_0"
        assert captured["device"] == "cpu"
        assert captured["input_size"] == (128, 64)

    def test_openvino_export_dispatch(self, monkeypatch, tmp_path):
        export_calls: dict[str, object] = {}
        ov_calls: dict[str, object] = {}
        exported = tmp_path / "exported.xml"

        def fake_export(model_name, input_size, *, weights_path, cache_dir) -> Path:
            export_calls.update(
                model_name=model_name, input_size=input_size, weights_path=weights_path, cache_dir=cache_dir
            )
            return exported

        def fake_ov(model_path, *, input_size, device) -> str:
            ov_calls.update(model_path=model_path, input_size=input_size, device=device)
            return "OV_PROVIDER"

        monkeypatch.setattr("getitrack.reid.export.export_torchreid_to_openvino", fake_export)
        monkeypatch.setattr("getitrack.reid.openvino_provider.OpenVINOReIDProvider", fake_ov)
        cfg = ReIDConfig(enabled=True, backend=ReIDBackend.OPENVINO, model_name="osnet_x1_0", device="CPU")
        assert build_reid_provider(cfg) == "OV_PROVIDER"
        assert export_calls["model_name"] == "osnet_x1_0"
        assert ov_calls["model_path"] == exported
        assert ov_calls["device"] == "CPU"

    def test_openvino_prebuilt_ir_dispatch(self, monkeypatch, tmp_path):
        ov_calls: dict[str, object] = {}

        def fake_ov(model_path, *, input_size, device) -> str:
            ov_calls.update(model_path=model_path, input_size=input_size, device=device)
            return "OV_PROVIDER"

        monkeypatch.setattr("getitrack.reid.openvino_provider.OpenVINOReIDProvider", fake_ov)
        ir = tmp_path / "model.xml"
        cfg = ReIDConfig(enabled=True, backend=ReIDBackend.OPENVINO, model_path=ir)
        assert build_reid_provider(cfg) == "OV_PROVIDER"
        assert ov_calls["model_path"] == ir


class TestTorchDevice:
    @pytest.mark.parametrize(
        ("value", "expected"),
        [("CPU", "cpu"), ("cpu", "cpu"), ("GPU", "cuda"), ("gpu", "cuda"), ("cuda", "cuda"), ("cuda:1", "cuda:1")],
    )
    def test_mapping(self, value, expected):
        assert _torch_device(value) == expected
