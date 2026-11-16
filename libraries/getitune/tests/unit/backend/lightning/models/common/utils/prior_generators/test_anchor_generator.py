# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Tests for anchor generation."""

import pytest
import torch

from getitune.backend.lightning.models.common.utils.prior_generators import AnchorGenerator


def test_rectangular_stride() -> None:
    generator = AnchorGenerator(strides=[(4, 6)], ratios=[1.0], scales=[1, 2])
    featmap_size = (2, 2)
    indices = torch.tensor([1, 2, 4, 7])
    priors = generator.grid_priors([featmap_size], device="cpu")[0]
    expected = torch.tensor([[-4, -4, 4, 4], [4, -2, 8, 2], [-2, 2, 2, 6], [2, 0, 10, 8]], dtype=torch.float32)

    torch.testing.assert_close(priors[indices], expected)
    torch.testing.assert_close(generator.sparse_priors(indices, featmap_size, 0, device="cpu"), expected)
    with pytest.warns(UserWarning, match="grid_anchors.*would be deprecated"):
        anchors = generator.grid_anchors([featmap_size], device="cpu")[0]
    torch.testing.assert_close(anchors, priors)
    flags = generator.valid_flags([featmap_size], (5, 5), device="cpu")[0]
    torch.testing.assert_close(flags, torch.tensor([True, False, True, False]).repeat_interleave(2))
