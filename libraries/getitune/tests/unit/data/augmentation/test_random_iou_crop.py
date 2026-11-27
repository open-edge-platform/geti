# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""The batched ``RandomIoUCrop.make_params`` must keep torchvision's sampling semantics."""

from __future__ import annotations

import torch
import torchvision.transforms.v2 as tvt_v2
from torchvision import tv_tensors

from getitune.data.augmentation.transforms import RandomIoUCrop

SIZE = 400


def _inputs(boxes: list[list[float]]) -> list:
    image = tv_tensors.Image(torch.zeros(3, SIZE, SIZE, dtype=torch.uint8))
    return [
        image,
        tv_tensors.BoundingBoxes(  # pyrefly: ignore[no-matching-overload]
            torch.tensor(boxes, dtype=torch.float32), format="XYXY", canvas_size=(SIZE, SIZE)
        ),  # pyrefly: ignore[no-matching-overload]
    ]


BOXES: list[list[float]] = [[10, 10, 60, 50], [200, 220, 260, 300], [300, 40, 380, 120], [120, 330, 150, 390]]


def test_returned_crops_satisfy_every_torchvision_constraint() -> None:
    crop = RandomIoUCrop(sampler_options=[0.3, 0.5])
    torch.manual_seed(0)
    for _ in range(200):
        params = crop.make_params(_inputs(BOXES))
        assert params, "no leave-as-is option configured, a crop must be returned"
        assert crop.min_aspect_ratio <= params["width"] / params["height"] <= crop.max_aspect_ratio
        assert params["left"] >= 0
        assert params["left"] + params["width"] <= SIZE
        assert params["top"] >= 0
        assert params["top"] + params["height"] <= SIZE
        assert params["is_within_crop_area"].any()


def test_sampling_statistics_match_torchvision() -> None:
    crop = RandomIoUCrop()

    def stats(make_params, n: int = 1500) -> tuple[float, float]:
        torch.manual_seed(1)
        results = [make_params(_inputs(BOXES)) for _ in range(n)]
        none = sum(not r for r in results) / n
        area = sum(1.0 if not r else r["width"] * r["height"] / SIZE**2 for r in results) / n
        return none, area

    new_none, new_area = stats(crop.make_params)
    ref_none, ref_area = stats(lambda f: tvt_v2.RandomIoUCrop.make_params(crop, f))

    assert abs(new_none - ref_none) < 0.04
    assert abs(new_area - ref_area) < 0.04


def test_transform_runs_end_to_end() -> None:
    crop = RandomIoUCrop(sampler_options=[0.3])
    torch.manual_seed(2)
    image, boxes = crop(*_inputs(BOXES))
    assert image.shape[-2] <= SIZE
    assert image.shape[-1] <= SIZE
    assert boxes.shape == (len(BOXES), 4)
