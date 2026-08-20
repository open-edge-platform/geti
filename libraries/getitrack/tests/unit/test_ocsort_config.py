# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Tests for OCSortConfig validation and defaults."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from getitrack.algorithms.configs.ocsort import OCSortConfig
from getitrack.config import AlgorithmType, TrackerConfig
from getitrack.core.registry import resolve_tracker_config


class TestDefaults:
    def test_reference_defaults(self):
        cfg = OCSortConfig()
        assert cfg.algorithm == AlgorithmType.OCSORT
        assert cfg.det_threshold == pytest.approx(0.6)
        assert cfg.iou_threshold == pytest.approx(0.3)
        assert cfg.delta_t == 3
        assert cfg.inertia == pytest.approx(0.2)
        assert cfg.use_byte is False

    def test_match_threshold_is_one_minus_iou_threshold(self):
        cfg = OCSortConfig(iou_threshold=0.3)
        assert cfg.match_threshold == pytest.approx(0.7)


class TestValidation:
    def test_low_floor_at_or_above_det_threshold_rejected(self):
        with pytest.raises(ValidationError, match="score_threshold must be below det_threshold"):
            OCSortConfig(score_threshold=0.6, det_threshold=0.6)

    def test_out_of_range_inertia_rejected(self):
        with pytest.raises(ValidationError):
            OCSortConfig(inertia=1.5)

    def test_delta_t_must_be_positive(self):
        with pytest.raises(ValidationError):
            OCSortConfig(delta_t=0)

    def test_algorithm_cannot_be_overridden(self):
        with pytest.raises(ValidationError):
            OCSortConfig.model_validate({"algorithm": AlgorithmType.BYTETRACK})

    def test_unknown_field_rejected(self):
        with pytest.raises(ValidationError):
            OCSortConfig.model_validate({"nonexistent": 1})


class TestResolution:
    def test_resolve_dispatches_to_ocsort_config(self):
        resolved = resolve_tracker_config({"algorithm": "ocsort", "det_threshold": 0.5})
        assert isinstance(resolved, OCSortConfig)
        assert resolved.det_threshold == pytest.approx(0.5)

    def test_model_dump_round_trip(self):
        cfg = OCSortConfig(det_threshold=0.55, use_byte=True, inertia=0.25)
        restored = resolve_tracker_config(cfg.model_dump())
        assert restored == cfg

    def test_base_from_yaml_round_trip(self, tmp_path):
        cfg = OCSortConfig(det_threshold=0.55, delta_t=5, use_byte=True)
        path = tmp_path / "ocsort.yaml"
        cfg.to_yaml(path)
        assert TrackerConfig.from_yaml(path) == cfg
