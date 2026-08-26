# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Tests for the torchreid-to-OpenVINO export bridge.

Only the cache and filename logic is exercised; the actual conversion needs
torch/torchreid/openvino, so these tests stay on the cache-hit path (a
pre-created IR) and never trigger the heavy imports.
"""

from __future__ import annotations

import os
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

    def test_in_place_weights_update_changes_stem(self, tmp_path):
        # Replacing a checkpoint in place must invalidate the cache key, so the
        # stem must reflect the file contents, not just its path.
        weights = tmp_path / "model.pth.tar"
        weights.write_bytes(b"first checkpoint")
        first = _cache_stem("osnet_x1_0", (256, 128), weights)
        # Rewrite in place with different contents and a later mtime.
        weights.write_bytes(b"second checkpoint, larger payload")
        os.utime(weights, ns=(2_000_000_000_000, 2_000_000_000_000))
        second = _cache_stem("osnet_x1_0", (256, 128), weights)
        assert first != second

    def test_missing_weights_file_falls_back_to_path(self):
        # A non-existent checkpoint still produces a stable, path-based stem.
        assert _cache_stem("osnet_x1_0", (256, 128), "missing.pth.tar")


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
