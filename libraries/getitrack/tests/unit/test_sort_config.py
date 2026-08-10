# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Tests for SortConfig validation and defaults."""

from __future__ import annotations

import pytest

from getitrack.algorithms.configs.sort import SortConfig
from getitrack.config import AlgorithmType, TrackerConfig
from getitrack.core.registry import resolve_tracker_config


class TestDefaults:
    def test_reference_defaults(self):
        cfg = SortConfig()
        assert cfg.algorithm == AlgorithmType.SORT
        assert cfg.iou_threshold == pytest.approx(0.3)
        assert cfg.match_class_only is True

    def test_match_threshold_is_one_minus_iou_threshold(self):
        cfg = SortConfig(iou_threshold=0.3)
        assert cfg.match_threshold == pytest.approx(0.7)


class TestResolution:
    def test_resolve_dispatches_to_sort_config(self):
        resolved = resolve_tracker_config({"algorithm": "sort", "iou_threshold": 0.5})
        assert isinstance(resolved, SortConfig)
        assert resolved.iou_threshold == pytest.approx(0.5)

    def test_base_from_yaml_round_trip(self, tmp_path):
        cfg = SortConfig(iou_threshold=0.4, match_class_only=False)
        path = tmp_path / "sort.yaml"
        cfg.to_yaml(path)
        assert TrackerConfig.from_yaml(path) == cfg
