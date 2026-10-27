# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for the RF-DETR mixin export helpers."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
import torch
from rfdetr.models.backbone.projector import LayerNorm as ProjectorLayerNorm

from getitune.backend.lightning.models.common.rfdetr_mixin import (
    _fp16_safe_layer_norm_forward,
    _fp16_safe_projector_norms,
)
from getitune.backend.lightning.models.instance_segmentation.base import LightningInstanceSegModel
from getitune.backend.lightning.models.instance_segmentation.rfdetr_inst import RFDETRInst
from getitune.types.export import ExportFormat


@pytest.fixture
def fxt_projector_norm() -> ProjectorLayerNorm:
    torch.manual_seed(0)
    norm = ProjectorLayerNorm(64)
    with torch.no_grad():
        norm.weight.normal_()
        norm.bias.normal_()
    return norm


class TestFP16SafeLayerNorm:
    @pytest.mark.parametrize("magnitude", [1e-3, 1.0, 500.0])
    def test_matches_original_layer_norm(self, fxt_projector_norm: ProjectorLayerNorm, magnitude: float) -> None:
        x = torch.randn(2, 64, 4, 5) * magnitude
        with torch.no_grad():
            expected = fxt_projector_norm(x)
            actual = _fp16_safe_layer_norm_forward(fxt_projector_norm, x)
        torch.testing.assert_close(actual, expected, rtol=1e-4, atol=1e-5)

    def test_constant_input_returns_bias(self, fxt_projector_norm: ProjectorLayerNorm) -> None:
        x = torch.full((1, 64, 2, 2), 7.0)
        with torch.no_grad():
            out = _fp16_safe_layer_norm_forward(fxt_projector_norm, x)
        torch.testing.assert_close(out, fxt_projector_norm.bias.view(1, -1, 1, 1).expand_as(out))

    def test_fp16_does_not_overflow(self, fxt_projector_norm: ProjectorLayerNorm) -> None:
        """Activations of ~436 (seen in issue #7806) push the channel sum of squares past FP16's max."""
        x = torch.randn(1, 64, 4, 4) * 436.0
        assert (x - x.mean(dim=1, keepdim=True)).square().sum(dim=1).max() > torch.finfo(torch.float16).max
        with torch.no_grad():
            expected = fxt_projector_norm(x)
            actual = _fp16_safe_layer_norm_forward(fxt_projector_norm.half(), x.half())
        assert torch.isfinite(actual).all()
        torch.testing.assert_close(actual.float(), expected, rtol=1e-2, atol=2e-2)


class TestFP16SafeProjectorNorms:
    def test_patches_and_restores(self, fxt_projector_norm: ProjectorLayerNorm) -> None:
        module = torch.nn.Sequential(fxt_projector_norm)
        with _fp16_safe_projector_norms(module):
            assert fxt_projector_norm.forward.__func__ is _fp16_safe_layer_norm_forward
        assert "forward" not in vars(fxt_projector_norm)
        assert fxt_projector_norm.forward.__func__ is ProjectorLayerNorm.forward

    def test_restores_on_error(self, fxt_projector_norm: ProjectorLayerNorm) -> None:
        with pytest.raises(RuntimeError), _fp16_safe_projector_norms(fxt_projector_norm):
            raise RuntimeError
        assert "forward" not in vars(fxt_projector_norm)


class TestRFDETRMixinExport:
    def test_export_uses_fp16_safe_projector_norms(self, tmp_path: Path) -> None:
        model = RFDETRInst(model_name="rfdetr_seg_n", label_info=3, pretrained=False)
        norms = [m for m in model.modules() if isinstance(m, ProjectorLayerNorm)]
        assert norms
        seen_during_export: list[bool] = []

        def fake_export(*_args, **_kwargs) -> Path:
            seen_during_export.extend(n.forward.__func__ is _fp16_safe_layer_norm_forward for n in norms)
            return tmp_path / "model.xml"

        with patch.object(LightningInstanceSegModel, "export", fake_export):
            model.export(tmp_path, "model", ExportFormat.OPENVINO)

        assert seen_during_export
        assert all(seen_during_export)
        assert all("forward" not in vars(n) for n in norms)
