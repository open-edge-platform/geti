# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""IOU configuration validation and factory integration."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from getitrack.algorithms import IOUTracker
from getitrack.algorithms.configs.iou import IOUConfig
from getitrack.config import AlgorithmType, TrackerConfig
from getitrack.core.base import BaseTracker
from getitrack.core.registry import resolve_tracker_config


def test_defaults():
    config = IOUConfig()
    assert config.algorithm == AlgorithmType.IOU
    assert config.score_threshold == 0.1
    assert config.high_score_threshold == 0.5
    assert config.iou_threshold == 0.5
    assert config.lifecycle.min_hits == 2
    assert config.match_class_only is True


@pytest.mark.parametrize("config", [IOUConfig(), {"algorithm": "iou"}, TrackerConfig(algorithm=AlgorithmType.IOU)])
def test_factory(config):
    assert isinstance(BaseTracker.from_config(config), IOUTracker)
    assert isinstance(resolve_tracker_config({"algorithm": "iou"}), IOUConfig)


def test_yaml_roundtrip_and_factory(tmp_path):
    config = IOUConfig(iou_threshold=0.7, high_score_threshold=0.8, match_class_only=False)
    path = tmp_path / "iou.yaml"
    config.to_yaml(path)
    assert TrackerConfig.from_yaml(path) == config
    assert BaseTracker.from_config(path).config == config


def test_recipe():
    path = Path(__file__).parents[2] / "configs" / "iou.yaml"
    assert BaseTracker.from_config(path).config == IOUConfig()


@pytest.mark.parametrize(
    "values",
    [
        {"iou_threshold": -0.1},
        {"iou_threshold": 1.1},
        {"iou_threshold": float("nan")},
        {"score_threshold": -0.1},
        {"high_score_threshold": 1.1},
        {"lifecycle": {"min_hits": 0}},
        {"distance_metric": "giou"},
        {"algorithm": "sort"},
        {"unknown_threshold": 0.3},
    ],
)
def test_invalid_config(values):
    with pytest.raises(ValidationError):
        IOUConfig(**values)
