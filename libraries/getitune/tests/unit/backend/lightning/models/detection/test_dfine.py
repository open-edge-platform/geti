# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#
"""Test of D-Fine."""

import pytest
import torch

from getitune.backend.lightning.models.base import DataInputParams
from getitune.backend.lightning.models.detection.d_fine import DFine
from getitune.backend.lightning.models.detection.necks.dfine_hybrid_encoder import HybridEncoder
from getitune.data.entity.sample import PredictionBatch


class TestDFine:
    @pytest.fixture
    def fxt_model(self) -> DFine:
        return DFine(
            label_info=3,
            model_name="dfine_hgnetv2_x",
            data_input_params=DataInputParams((640, 640), (0.0, 0.0, 0.0), (1.0, 1.0, 1.0)),
            pretrained=False,
        )

    def test_loss(self, fxt_model, fxt_detection_batch):
        fxt_model(fxt_detection_batch)

    def test_predict(self, fxt_model, fxt_detection_batch):
        fxt_model.eval()
        output = fxt_model(fxt_detection_batch)
        assert isinstance(output, PredictionBatch)

    def test_export(self, fxt_model):
        fxt_model.eval()
        output = fxt_model.forward_for_tracing(torch.randn(1, 3, 640, 640))
        assert len(output) == 3

    def test_eval_with_non_default_input_size(self):
        # dfine_hgnetv2_m caches encoder positional embeddings, which must follow the input size
        model = DFine(
            label_info=3,
            model_name="dfine_hgnetv2_m",
            data_input_params=DataInputParams((1024, 1024), (0.0, 0.0, 0.0), (1.0, 1.0, 1.0)),
            pretrained=False,
        )
        model.eval()
        output = model.forward_for_tracing(torch.randn(1, 3, 1024, 1024))
        assert len(output) == 3


@pytest.mark.parametrize(
    ("model_name", "eval_spatial_size", "expected"),
    [
        ("dfine_hgnetv2_m", None, [640, 640]),
        ("dfine_hgnetv2_m", (1024, 1024), [1024, 1024]),
        ("deim_dfine_hgnetv2_m", (800, 800), [800, 800]),
        # configurations without cached embeddings compute them on the fly
        ("dfine_hgnetv2_x", (1024, 1024), None),
    ],
)
def test_hybrid_encoder_eval_spatial_size(model_name, eval_spatial_size, expected):
    encoder = HybridEncoder(model_name=model_name, eval_spatial_size=eval_spatial_size)
    assert encoder.eval_spatial_size == expected
    assert "eval_spatial_size" not in HybridEncoder.encoder_cfg["dfine_hgnetv2_x"]
    assert HybridEncoder.encoder_cfg["dfine_hgnetv2_m"]["eval_spatial_size"] == [640, 640]
