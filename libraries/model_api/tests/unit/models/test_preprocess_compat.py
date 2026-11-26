#
# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#

from __future__ import annotations

from dataclasses import dataclass, field
from unittest.mock import MagicMock

import numpy as np
import pytest
from model_api.models.image_model import ImageModel
from model_api.models.ssd import SSD


@dataclass
class FakeMetadata:
    names: set = field(default_factory=set)
    shape: list = field(default_factory=list)
    layout: str = ""
    precision: str = ""
    type: str = ""
    meta: dict = field(default_factory=dict)


def _make_adapter(input_shape=(1, 3, 300, 300), layout="NCHW", extra_inputs=None):
    """Create a minimal mock InferenceAdapter for ImageModel construction."""
    adapter = MagicMock()

    image_meta = FakeMetadata(shape=list(input_shape), layout=layout)
    inputs = {"image": image_meta}
    if extra_inputs:
        inputs.update(extra_inputs)

    adapter.get_input_layers.return_value = inputs
    adapter.get_output_layers.return_value = {"output": FakeMetadata(shape=[1, 1, 200, 7])}
    adapter.get_rt_info.side_effect = RuntimeError(
        "Cannot get runtime attribute. Path to runtime attribute is incorrect.",
    )
    adapter.embed_preprocessing = MagicMock()
    return adapter


class TestPreprocessBackwardCompat:
    """Tests that the old preprocess(image) single-arg call still works."""

    def _make_image_model(self):
        adapter = _make_adapter()
        return ImageModel(adapter, configuration={}, preload=False)

    def test_old_style_single_arg_calls_base_preprocess(self):
        model = self._make_image_model()
        rng = np.random.default_rng(0)
        image = rng.integers(0, 255, (480, 640, 3), dtype=np.uint8)

        with pytest.warns(DeprecationWarning, match="deprecated since model_api v0.4.0"):
            result = model.preprocess(image)

        assert isinstance(result, list)
        assert len(result) == 2
        dict_inputs, meta = result
        assert isinstance(dict_inputs, dict)
        assert "image" in dict_inputs
        assert "original_shape" in meta
        assert "resized_shape" in meta

    def test_new_style_two_arg_works_without_warning(self):
        model = self._make_image_model()
        dict_inputs = {"image": np.zeros((1, 3, 300, 300))}
        meta = {"original_shape": (480, 640, 3), "resized_shape": (300, 300, 3)}

        import warnings

        with warnings.catch_warnings():
            warnings.simplefilter("error", DeprecationWarning)
            result_inputs, result_meta = model.preprocess(dict_inputs, meta)

        assert result_inputs is dict_inputs
        assert result_meta is meta


class TestSSDPreprocessBackwardCompat:
    """Tests backward compat specifically for SSD — the model reported in the bug."""

    def _make_ssd_model(self):
        adapter = _make_adapter(
            extra_inputs={"image_info": FakeMetadata(shape=[1, 3], layout="NC")},
        )
        adapter.get_output_layers.return_value = {
            "detection_out": FakeMetadata(shape=[1, 1, 200, 7]),
        }
        return SSD(adapter, configuration={}, preload=False)

    def test_old_style_call_returns_preprocessed_data(self):
        model = self._make_ssd_model()
        rng = np.random.default_rng(0)
        image = rng.integers(0, 255, (480, 640, 3), dtype=np.uint8)

        with pytest.warns(DeprecationWarning, match="deprecated since model_api v0.4.0"):
            result = model.preprocess(image)

        assert isinstance(result, list)
        assert len(result) == 2
        dict_inputs, meta = result
        assert "image" in dict_inputs
        assert "original_shape" in meta

    def test_new_style_call_adds_image_info_blob(self):
        model = self._make_ssd_model()
        dict_inputs = {"image": np.zeros((1, 3, 300, 300))}
        meta = {"original_shape": (480, 640, 3), "resized_shape": (300, 300, 3)}

        import warnings

        with warnings.catch_warnings():
            warnings.simplefilter("error", DeprecationWarning)
            result_inputs, _ = model.preprocess(dict_inputs, meta)

        # SSD should add image_info blob
        assert "image_info" in result_inputs
        np.testing.assert_array_equal(result_inputs["image_info"], [[300, 300, 1]])

    def test_unpacking_works_like_old_api(self):
        """Simulate the exact geti_sdk call pattern: preprocessed_image, metadata = model.preprocess(image)."""
        model = self._make_ssd_model()
        rng = np.random.default_rng(0)
        image = rng.integers(0, 255, (480, 640, 3), dtype=np.uint8)

        with pytest.warns(DeprecationWarning):
            preprocessed_image, metadata = model.preprocess(image)

        assert isinstance(preprocessed_image, dict)
        assert isinstance(metadata, dict)
