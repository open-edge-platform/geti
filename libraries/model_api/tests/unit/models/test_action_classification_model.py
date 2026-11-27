#
# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#

"""Unit tests for ActionClassificationModel."""

from __future__ import annotations

import pathlib
from dataclasses import dataclass, field
from unittest.mock import MagicMock

import numpy as np
import pytest
from model_api.adapters.inference_adapter import InferenceAdapter
from model_api.models.action_classification import ActionClassificationModel
from model_api.models.model import WrapperError

rng = np.random.default_rng(0)

_RT_INFO_ERROR = RuntimeError(
    "Cannot get runtime attribute. Path to runtime attribute is incorrect.",
)


@dataclass
class FakeMetadata:
    names: set = field(default_factory=set)
    shape: list = field(default_factory=list)
    layout: str = ""
    precision: str = ""
    type: str = ""
    meta: dict = field(default_factory=dict)


def _make_adapter(
    input_shape=(1, 1, 3, 8, 224, 224),
    output_shape=(1, 10),
    layout="NSCTHW",
):
    adapter = MagicMock(spec=InferenceAdapter)
    video_meta = FakeMetadata(shape=list(input_shape), layout=layout)
    inputs = {"video": video_meta}

    out_meta = FakeMetadata(shape=list(output_shape))
    outputs = {"output": out_meta}

    adapter.get_input_layers.return_value = inputs
    adapter.get_output_layers.return_value = outputs
    adapter.get_rt_info.side_effect = _RT_INFO_ERROR
    adapter.embed_preprocessing = MagicMock()
    adapter.load_model.return_value = None
    adapter.infer_sync.return_value = {"output": np.zeros(output_shape)}
    return adapter


# ---------------------------------------------------------------------------
# TestInit
# ---------------------------------------------------------------------------
class TestActionClassificationModelInit:
    def test_nscthw_layout(self):
        adapter = _make_adapter(
            input_shape=(1, 1, 3, 8, 224, 224),
            layout="NSCTHW",
        )
        model = ActionClassificationModel(adapter, configuration={})
        assert model.nscthw_layout is True
        assert model.n == 1
        assert model.s == 1
        assert model.c == 3
        assert model.t == 8
        assert model.h == 224
        assert model.w == 224

    def test_nsthwc_layout(self):
        adapter = _make_adapter(
            input_shape=(1, 1, 8, 224, 224, 3),
            layout="NSTHWC",
        )
        model = ActionClassificationModel(adapter, configuration={})
        assert model.nscthw_layout is False
        assert model.n == 1
        assert model.s == 1
        assert model.t == 8
        assert model.h == 224
        assert model.w == 224
        assert model.c == 3

    def test_image_blob_name(self):
        adapter = _make_adapter()
        model = ActionClassificationModel(adapter, configuration={})
        assert model.image_blob_name == "video"
        assert model.image_blob_names == ["video"]


# ---------------------------------------------------------------------------
# TestClipSize
# ---------------------------------------------------------------------------
class TestClipSize:
    def test_returns_t(self):
        adapter = _make_adapter(input_shape=(1, 1, 3, 16, 112, 112), layout="NSCTHW")
        model = ActionClassificationModel(adapter, configuration={})
        assert model.clip_size == 16


# ---------------------------------------------------------------------------
# Test_get_inputs
# ---------------------------------------------------------------------------
class TestGetInputs:
    def test_finds_6d_inputs(self):
        adapter = _make_adapter()
        model = ActionClassificationModel(adapter, configuration={})
        assert model.image_blob_names == ["video"]

    def test_error_on_non_6d_input(self):
        adapter = _make_adapter()

        adapter.get_input_layers.return_value = {
            "video": FakeMetadata(shape=[1, 1, 3, 8, 224, 224], layout="NSCTHW"),
            "extra_input": FakeMetadata(shape=[1, 3, 224, 224], layout="NCHW"),
        }
        with pytest.raises(WrapperError):
            ActionClassificationModel(adapter, configuration={})

    def test_error_on_no_6d_input(self):
        adapter = _make_adapter()
        adapter.get_input_layers.return_value = {
            "image": FakeMetadata(shape=[1, 3, 224, 224], layout="NCHW"),
        }
        with pytest.raises(WrapperError):
            ActionClassificationModel(adapter, configuration={})


# ---------------------------------------------------------------------------
# TestBasePreprocess
# ---------------------------------------------------------------------------
class TestBasePreprocess:
    def test_preprocess_produces_dict(self):
        adapter = _make_adapter(
            input_shape=(1, 1, 3, 4, 64, 64),
            layout="NSCTHW",
        )
        model = ActionClassificationModel(adapter, configuration={})
        # 4 frames of 64x64x3
        frames = rng.integers(0, 255, (4, 64, 64, 3), dtype=np.uint8)
        dict_inputs, meta = model.base_preprocess(frames)
        assert "video" in dict_inputs
        assert "original_shape" in meta
        assert "resized_shape" in meta

    def test_preprocess_nscthw_output_shape(self):
        adapter = _make_adapter(
            input_shape=(1, 1, 3, 4, 64, 64),
            layout="NSCTHW",
        )
        model = ActionClassificationModel(adapter, configuration={})
        frames = rng.integers(0, 255, (4, 64, 64, 3), dtype=np.uint8)
        dict_inputs, _ = model.base_preprocess(frames)
        out = dict_inputs["video"]
        # shape order: batch, segments, channels, time, height, width
        assert out.shape[0] == 1  # N
        assert out.shape[1] == 1  # S
        assert out.shape[2] == 3  # C
        assert out.shape[3] == 4  # T

    def test_preprocess_nsthwc_output_shape(self):
        adapter = _make_adapter(
            input_shape=(1, 1, 4, 64, 64, 3),
            layout="NSTHWC",
        )
        model = ActionClassificationModel(adapter, configuration={})
        frames = rng.integers(0, 255, (4, 64, 64, 3), dtype=np.uint8)
        dict_inputs, _ = model.base_preprocess(frames)
        out = dict_inputs["video"]
        # shape order: batch, segments, time, height, width, channels
        assert out.shape[0] == 1  # N
        assert out.shape[1] == 1  # S
        assert out.ndim == 6

    def test_preprocess_t_mismatch_raises(self):
        adapter = _make_adapter(
            input_shape=(1, 1, 3, 8, 64, 64),
            layout="NSCTHW",
        )
        model = ActionClassificationModel(adapter, configuration={})
        # 4 frames but model expects 8
        frames = rng.integers(0, 255, (4, 64, 64, 3), dtype=np.uint8)
        with pytest.raises(RuntimeError, match="input shape"):
            model.base_preprocess(frames)


# ---------------------------------------------------------------------------
# TestChangeLayout
# ---------------------------------------------------------------------------
class TestChangeLayout:
    def test_nscthw_transpose(self):
        adapter = _make_adapter(
            input_shape=(1, 1, 3, 2, 4, 4),
            layout="NSCTHW",
        )
        model = ActionClassificationModel(adapter, configuration={})
        # list of T frames, each (H, W, C)
        frames = [np.zeros((4, 4, 3)) for _ in range(2)]
        result = model._change_layout(frames)  # noqa: SLF001
        # Should be (1, 1, C, T, H, W)
        assert result.shape == (1, 1, 3, 2, 4, 4)

    def test_nsthwc_passthrough(self):
        adapter = _make_adapter(
            input_shape=(1, 1, 2, 4, 4, 3),
            layout="NSTHWC",
        )
        model = ActionClassificationModel(adapter, configuration={})
        frames = [np.zeros((4, 4, 3)) for _ in range(2)]
        result = model._change_layout(frames)  # noqa: SLF001
        # Should be (1, 1, T, H, W, C)
        assert result.shape == (1, 1, 2, 4, 4, 3)


# ---------------------------------------------------------------------------
# TestPostprocess
# ---------------------------------------------------------------------------
class TestPostprocess:
    def test_argmax_and_label(self):
        adapter = _make_adapter(output_shape=(1, 5))
        model = ActionClassificationModel(
            adapter,
            configuration={"labels": ["walk", "run", "jump", "sit", "stand"]},
        )
        logits = np.array([[0.1, 0.9, 0.3, 0.05, 0.2]])
        result = model.postprocess({"output": logits}, {})
        assert len(result.top_labels) == 1
        label = result.top_labels[0]
        assert label.id == 1
        assert label.name == "run"
        assert label.confidence == pytest.approx(0.9)

    def test_postprocess_empty_labels(self):
        adapter = _make_adapter(output_shape=(1, 3))
        model = ActionClassificationModel(
            adapter,
            configuration={"labels": ["a", "b", "c"]},
        )
        logits = np.array([[5.0, 1.0, 2.0]])
        result = model.postprocess({"output": logits}, {})
        assert result.top_labels[0].id == 0
        assert result.top_labels[0].name == "a"

    def test_postprocess_single_output(self):
        adapter = _make_adapter(output_shape=(1, 2))
        model = ActionClassificationModel(
            adapter,
            configuration={"labels": ["cat", "dog"]},
        )
        logits = np.array([[0.2, 0.8]])
        result = model.postprocess({"output": logits}, {})
        assert result.top_labels[0].id == 1


# ---------------------------------------------------------------------------
# TestParameters
# ---------------------------------------------------------------------------
class TestParameters:
    def test_has_expected_keys(self):
        params = ActionClassificationModel.parameters()
        assert "labels" in params
        assert "path_to_labels" in params
        assert "resize_type" in params
        assert "reverse_input_channels" in params
        assert "mean_values" in params
        assert "scale_values" in params


# ---------------------------------------------------------------------------
# Additional coverage tests
# ---------------------------------------------------------------------------


class TestActionClassificationPathToLabels:
    def test_path_to_labels_loads_labels(self):
        """Line 80: labels loaded from path_to_labels file."""
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("action1\naction2\n")
            label_path = f.name
        try:
            adapter = _make_adapter()
            model = ActionClassificationModel(
                adapter,
                configuration={"path_to_labels": label_path},
                preload=False,
            )
            assert model._labels == ["action1", "action2"]  # noqa: SLF001
        finally:
            pathlib.Path(label_path).unlink()


class TestActionClassificationNo6DInput:
    def test_no_6d_input_raises(self):
        """Line 117: error when no 6D input found."""
        adapter = _make_adapter(input_shape=(1, 3, 224, 224), layout="NCHW")
        with pytest.raises(WrapperError, match="Failed to identify the input"):
            ActionClassificationModel(adapter, configuration={})

    def test_empty_inputs_raises_no_6d(self):
        """Line 117: error when inputs dict is empty (no 6D layer found)."""
        adapter = MagicMock(spec=InferenceAdapter)
        adapter.get_input_layers.return_value = {}
        adapter.get_output_layers.return_value = {"output": FakeMetadata(shape=[1, 10])}
        adapter.get_rt_info.side_effect = _RT_INFO_ERROR
        adapter.embed_preprocessing = MagicMock()
        with pytest.raises(WrapperError, match="no 6D input layer found"):
            ActionClassificationModel(adapter, configuration={})
