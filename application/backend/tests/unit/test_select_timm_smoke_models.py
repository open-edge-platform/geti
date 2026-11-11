# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
from pathlib import Path

import pytest

from app.select_timm_smoke_models import select_lightest_per_family


@pytest.fixture
def snapshot_path(tmp_path: Path) -> Path:
    backbones = [
        {"family": "resnet", "model_name": "resnet50.a1_in1k", "gigaflops": 4.1},
        {"family": "resnet", "model_name": "resnet10t.c3_in1k", "gigaflops": 1.1},
        {"family": "beit", "model_name": "beit_base_patch16_224.in22k", "gigaflops": 35.1},
        {"family": "vision_transformer_sam", "model_name": "samvit_base_patch16.sa1b", "gigaflops": 972.1},
        {"family": "vision_transformer_sam", "model_name": "samvit_large_patch16.sa1b", "gigaflops": 2900.0},
    ]
    path = tmp_path / "snapshot.json"
    path.write_text(json.dumps({"backbones": backbones}), encoding="utf-8")
    return path


def test_selects_lightest_backbone_per_family_sorted_by_family(snapshot_path: Path) -> None:
    selected, skipped = select_lightest_per_family(snapshot_path)

    assert selected == [
        ("beit", "beit_base_patch16_224.in22k"),
        ("resnet", "resnet10t.c3_in1k"),
        ("vision_transformer_sam", "samvit_base_patch16.sa1b"),
    ]
    assert skipped == []


def test_skips_families_whose_lightest_backbone_exceeds_budget(snapshot_path: Path) -> None:
    selected, skipped = select_lightest_per_family(snapshot_path, max_gigaflops=300.0)

    assert selected == [
        ("beit", "beit_base_patch16_224.in22k"),
        ("resnet", "resnet10t.c3_in1k"),
    ]
    assert skipped == [("vision_transformer_sam", "samvit_base_patch16.sa1b", 972.1)]


@pytest.mark.parametrize(("max_gigaflops", "expected_selected"), [(35.1, 2), (35.0, 1)])
def test_budget_is_inclusive(snapshot_path: Path, max_gigaflops: float, expected_selected: int) -> None:
    selected, _ = select_lightest_per_family(snapshot_path, max_gigaflops=max_gigaflops)

    assert len(selected) == expected_selected
