# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Tests for the torchreid-to-OpenVINO export bridge.

Only the cache and filename logic is exercised; the actual conversion needs
torch/torchreid/openvino, so these tests stay on the cache-hit path (a
pre-created IR) and never trigger the heavy imports.
"""

from __future__ import annotations

from pathlib import Path

from getitrack.reid.export import _cache_stem, _default_cache_dir, export_torchreid_to_openvino


class TestCacheStem:
    def test_distinguishes_model_size_and_weights(self):
        stems = {
            _cache_stem("osnet_x1_0", (256, 128), None),
            _cache_stem("osnet_ain_x1_0", (256, 128), None),
            _cache_stem("osnet_x1_0", (128, 64), None),
            _cache_stem("osnet_x1_0", (256, 128), "weights.pth.tar"),
        }
        assert len(stems) == 4

    def test_pretrained_tag_when_no_weights(self):
        assert _cache_stem("osnet_x1_0", (256, 128), None).endswith("pretrained")

    def test_encodes_size(self):
        assert "256x128" in _cache_stem("osnet_x1_0", (256, 128), None)


class TestCacheHit:
    def test_returns_existing_ir_without_export(self, tmp_path):
        # Pre-create the cached IR so the heavy conversion path is never entered.
        xml = tmp_path / f"{_cache_stem('osnet_x1_0', (256, 128), None)}.xml"
        xml.write_text("<net/>")
        out = export_torchreid_to_openvino("osnet_x1_0", (256, 128), cache_dir=tmp_path)
        assert out == xml


class TestDefaultCacheDir:
    def test_under_home_cache(self):
        assert _default_cache_dir() == Path.home() / ".cache" / "getitrack" / "reid"
