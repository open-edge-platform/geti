#
# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#

"""Unit tests for ClassificationModel and related helpers."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from unittest.mock import MagicMock, mock_open, patch

import numpy as np
import pytest
from model_api.adapters.inference_adapter import InferenceAdapter
from model_api.models.classification import (
    ClassificationModel,
    GreedyLabelsResolver,
    ProbabilisticLabelsResolver,
    SimpleLabelsGraph,
    _append_xai_names,
    _get_non_xai_names,
    sigmoid_numpy,
)
from model_api.models.model import WrapperError

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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
    input_shape=(1, 3, 224, 224),
    output_shape=(1, 10),
    layout="NCHW",
    rt_info=None,
):
    adapter = MagicMock(spec=InferenceAdapter)
    image_meta = FakeMetadata(shape=list(input_shape), layout=layout)
    inputs = {"image": image_meta}

    out_meta = FakeMetadata(shape=list(output_shape))
    outputs = {"output": out_meta}

    adapter.get_input_layers.return_value = inputs
    adapter.get_output_layers.return_value = outputs
    adapter.get_rt_info.side_effect = rt_info or _RT_INFO_ERROR
    adapter.embed_preprocessing = MagicMock()
    adapter.load_model.return_value = None
    adapter.infer_sync.return_value = {"output": np.zeros(output_shape)}
    return adapter


def _hierarchical_config(
    num_multiclass_heads=1,
    num_single_label_classes=3,
    num_multilabel_classes=0,
    groups=None,
    label_to_idx=None,
    class_to_group_idx=None,
    head_ranges=None,
    edges=None,
):
    groups = groups or [["cat", "dog", "bird"]]
    label_to_idx = label_to_idx or {"cat": 0, "dog": 1, "bird": 2}
    class_to_group_idx = class_to_group_idx or {"cat": 0, "dog": 0, "bird": 0}
    head_ranges = head_ranges or {"0": [0, 3]}
    edges = edges or []
    return json.dumps(
        {
            "cls_heads_info": {
                "num_multiclass_heads": num_multiclass_heads,
                "num_single_label_classes": num_single_label_classes,
                "num_multilabel_classes": num_multilabel_classes,
                "head_idx_to_logits_range": head_ranges,
                "all_groups": groups,
                "label_to_idx": label_to_idx,
                "class_to_group_idx": class_to_group_idx,
            },
            "label_tree_edges": edges,
        },
    )


# ---------------------------------------------------------------------------
# ClassificationModel constructor tests
# ---------------------------------------------------------------------------


class TestClassificationModelInit:
    def test_single_label_setup(self):
        adapter = _make_adapter(output_shape=(1, 10))
        model = ClassificationModel(adapter, configuration={})
        assert not model.params.multilabel
        assert not model.params.hierarchical
        assert len(model.out_layer_names) >= 1

    def test_multilabel_setup(self):
        adapter = _make_adapter(output_shape=(1, 10))
        model = ClassificationModel(adapter, configuration={"multilabel": True})
        assert model.params.multilabel

    def test_hierarchical_setup(self):
        adapter = _make_adapter(output_shape=(1, 3))
        config = _hierarchical_config()
        model = ClassificationModel(
            adapter,
            configuration={
                "hierarchical": True,
                "hierarchical_config": config,
            },
        )
        assert model.params.hierarchical
        assert hasattr(model, "hierarchical_info")

    def test_hierarchical_missing_config_raises(self):
        adapter = _make_adapter(output_shape=(1, 3))
        with pytest.raises(WrapperError):
            ClassificationModel(
                adapter,
                configuration={"hierarchical": True, "hierarchical_config": ""},
            )

    def test_hierarchical_probabilistic_resolver(self):
        adapter = _make_adapter(output_shape=(1, 3))
        config = _hierarchical_config()
        model = ClassificationModel(
            adapter,
            configuration={
                "hierarchical": True,
                "hierarchical_config": config,
                "hierarchical_postproc": "probabilistic",
            },
        )
        assert isinstance(model.labels_resolver, ProbabilisticLabelsResolver)


# ---------------------------------------------------------------------------
# _load_labels
# ---------------------------------------------------------------------------


class TestLoadLabels:
    def test_correct_format(self):
        adapter = _make_adapter(output_shape=(1, 3))
        lines = "0 cat,\n1 dog,\n2 bird,\n"
        with patch("model_api.models.classification.Path.open", mock_open(read_data=lines)):
            model = ClassificationModel(adapter, configuration={"path_to_labels": "labels.txt"})
        assert model._labels == ["cat", "dog", "bird"]  # noqa: SLF001

    def test_bad_format_raises(self):
        adapter = _make_adapter(output_shape=(1, 3))
        lines = "cat\ndog\nbird\n"
        with (
            patch("model_api.models.classification.Path.open", mock_open(read_data=lines)),
            pytest.raises(WrapperError),
        ):
            ClassificationModel(adapter, configuration={"path_to_labels": "labels.txt"})


# ---------------------------------------------------------------------------
# _verify_single_output
# ---------------------------------------------------------------------------


class TestVerifySingleOutput:
    def test_2d_valid(self):
        adapter = _make_adapter(output_shape=(1, 10))
        ClassificationModel(adapter, configuration={})

    def test_4d_valid(self):
        adapter = _make_adapter(output_shape=(1, 10, 1, 1))
        ClassificationModel(adapter, configuration={})

    def test_3d_raises(self):
        adapter = _make_adapter(output_shape=(1, 10, 5))
        with pytest.raises(WrapperError):
            ClassificationModel(adapter, configuration={})

    def test_4d_wrong_dims_raises(self):
        adapter = _make_adapter(output_shape=(1, 10, 3, 3))
        with pytest.raises(WrapperError):
            ClassificationModel(adapter, configuration={})

    def test_label_insertion_other(self):
        adapter = _make_adapter(output_shape=(1, 4))
        model = ClassificationModel(
            adapter,
            configuration={"labels": ["a", "b", "c"]},
        )
        assert model._labels[0] == "other"  # noqa: SLF001
        assert len(model._labels) == 4  # noqa: SLF001

    def test_model_classes_gt_labels_raises(self):
        adapter = _make_adapter(output_shape=(1, 10))
        with pytest.raises(WrapperError):
            ClassificationModel(
                adapter,
                configuration={"labels": ["a", "b"]},
            )


# ---------------------------------------------------------------------------
# postprocess
# ---------------------------------------------------------------------------


class TestPostprocess:
    def test_multiclass_path(self):
        adapter = _make_adapter(output_shape=(1, 5))
        model = ClassificationModel(adapter, configuration={"topk": 2})
        logits = np.array([[0.1, 0.5, 0.2, 0.05, 0.15]])
        outputs = {"output": logits}
        result = model.postprocess(outputs, {})
        assert len(result.top_labels) == 2

    def test_multilabel_path(self):
        adapter = _make_adapter(output_shape=(1, 3))
        model = ClassificationModel(
            adapter,
            configuration={"multilabel": True, "confidence_threshold": 0.3},
        )
        logits = np.array([2.0, -2.0, 2.0])
        outputs = {"output": logits}
        result = model.postprocess(outputs, {})
        assert len(result.top_labels) == 2

    def test_hierarchical_path(self):
        adapter = _make_adapter(output_shape=(1, 3))
        config = _hierarchical_config()
        model = ClassificationModel(
            adapter,
            configuration={
                "hierarchical": True,
                "hierarchical_config": config,
            },
        )
        logits = np.array([5.0, 1.0, 0.5])
        outputs = {"output": logits}
        result = model.postprocess(outputs, {})
        assert len(result.top_labels) >= 1

    def test_with_raw_scores(self):
        adapter = _make_adapter(output_shape=(1, 5))
        model = ClassificationModel(
            adapter,
            configuration={"output_raw_scores": True},
        )
        logits = np.array([[0.1, 0.5, 0.2, 0.05, 0.15]])
        outputs = {"output": logits}
        result = model.postprocess(outputs, {})
        assert result.raw_scores.size > 0


# ---------------------------------------------------------------------------
# get_saliency_maps
# ---------------------------------------------------------------------------


class TestGetSaliencyMaps:
    def test_non_hierarchical_passthrough(self):
        adapter = _make_adapter(output_shape=(1, 5))
        model = ClassificationModel(adapter, configuration={})
        sal = np.array([1.0, 2.0])
        outputs = {"saliency_map": sal}
        result = model.get_saliency_maps(outputs)
        np.testing.assert_array_equal(result, sal)

    def test_missing_key_returns_empty(self):
        adapter = _make_adapter(output_shape=(1, 5))
        model = ClassificationModel(adapter, configuration={})
        result = model.get_saliency_maps({})
        assert result.size == 0

    def test_hierarchical_reordering(self):
        adapter = _make_adapter(output_shape=(1, 3))
        config = _hierarchical_config(
            label_to_idx={"cat": 0, "dog": 1, "bird": 2},
            class_to_group_idx={"cat": 0, "dog": 0, "bird": 0},
        )
        model = ClassificationModel(
            adapter,
            configuration={
                "hierarchical": True,
                "hierarchical_config": config,
                "labels": ["bird", "cat", "dog"],
            },
        )
        saliency = np.array([[np.array([1]), np.array([2]), np.array([3])]])
        outputs = {"saliency_map": saliency}
        result = model.get_saliency_maps(outputs)
        np.testing.assert_array_equal(result[0][0], np.array([3]))
        np.testing.assert_array_equal(result[0][1], np.array([1]))
        np.testing.assert_array_equal(result[0][2], np.array([2]))


# ---------------------------------------------------------------------------
# get_all_probs
# ---------------------------------------------------------------------------


class TestGetAllProbs:
    def test_multilabel_sigmoid(self):
        adapter = _make_adapter(output_shape=(1, 3))
        model = ClassificationModel(adapter, configuration={"multilabel": True})
        logits = np.array([0.0, 0.0, 0.0])
        probs = model.get_all_probs(logits)
        np.testing.assert_allclose(probs, 0.5, atol=1e-6)

    def test_hierarchical_softmax_and_sigmoid(self):
        adapter = _make_adapter(output_shape=(1, 5))
        config = _hierarchical_config(
            num_multiclass_heads=1,
            num_single_label_classes=3,
            num_multilabel_classes=2,
            groups=[["cat", "dog", "bird"], ["sunny"], ["rainy"]],
            label_to_idx={"cat": 0, "dog": 1, "bird": 2, "sunny": 3, "rainy": 4},
            class_to_group_idx={"cat": 0, "dog": 0, "bird": 0, "sunny": 1, "rainy": 2},
            head_ranges={"0": [0, 3]},
        )
        model = ClassificationModel(
            adapter,
            configuration={"hierarchical": True, "hierarchical_config": config},
        )
        logits = np.array([1.0, 2.0, 3.0, 0.0, 0.0])
        probs = model.get_all_probs(logits)
        assert probs.shape == (5,)
        assert abs(probs[:3].sum() - 1.0) < 0.01
        np.testing.assert_allclose(probs[3:], 0.5, atol=1e-6)

    def test_single_label_softmax(self):
        adapter = _make_adapter(output_shape=(1, 3))
        model = ClassificationModel(adapter, configuration={})
        logits = np.array([[1.0, 2.0, 3.0]])
        probs = model.get_all_probs(logits)
        assert abs(probs.sum() - 1.0) < 0.01

    def test_single_label_already_softmaxed(self):
        adapter = _make_adapter(output_shape=(1, 3))
        model = ClassificationModel(adapter, configuration={})
        logits = np.array([[0.2, 0.3, 0.5]])
        probs = model.get_all_probs(logits)
        np.testing.assert_allclose(probs, [0.2, 0.3, 0.5], atol=1e-6)


# ---------------------------------------------------------------------------
# get_hierarchical_predictions
# ---------------------------------------------------------------------------


class TestGetHierarchicalPredictions:
    def test_multiclass_heads(self):
        adapter = _make_adapter(output_shape=(1, 3))
        config = _hierarchical_config()
        model = ClassificationModel(
            adapter,
            configuration={"hierarchical": True, "hierarchical_config": config},
        )
        logits = np.array([5.0, 1.0, 0.5])
        labels = model.get_hierarchical_predictions(logits)
        assert any(lbl.name == "cat" for lbl in labels)

    def test_multilabel_classes_in_hierarchical(self):
        adapter = _make_adapter(output_shape=(1, 5))
        config = _hierarchical_config(
            num_multiclass_heads=1,
            num_single_label_classes=3,
            num_multilabel_classes=2,
            groups=[["cat", "dog", "bird"], ["sunny"], ["rainy"]],
            label_to_idx={"cat": 0, "dog": 1, "bird": 2, "sunny": 3, "rainy": 4},
            class_to_group_idx={"cat": 0, "dog": 0, "bird": 0, "sunny": 1, "rainy": 2},
            head_ranges={"0": [0, 3]},
        )
        model = ClassificationModel(
            adapter,
            configuration={
                "hierarchical": True,
                "hierarchical_config": config,
                "confidence_threshold": 0.3,
            },
        )
        logits = np.array([5.0, 1.0, 0.5, 5.0, -5.0])
        labels = model.get_hierarchical_predictions(logits)
        label_names = [lbl.name for lbl in labels]
        assert "cat" in label_names
        assert "sunny" in label_names


# ---------------------------------------------------------------------------
# get_multilabel_predictions
# ---------------------------------------------------------------------------


class TestGetMultilabelPredictions:
    def test_filter_by_threshold(self):
        adapter = _make_adapter(output_shape=(1, 4))
        model = ClassificationModel(
            adapter,
            configuration={
                "multilabel": True,
                "confidence_threshold": 0.5,
                "labels": ["a", "b", "c", "d"],
            },
        )
        logits = np.array([10.0, -10.0, 10.0, -10.0])
        labels = model.get_multilabel_predictions(logits)
        assert len(labels) == 2
        names = [lbl.name for lbl in labels]
        assert "a" in names
        assert "c" in names


# ---------------------------------------------------------------------------
# get_multiclass_predictions
# ---------------------------------------------------------------------------


class TestGetMulticlassPredictions:
    def test_softmax_topk(self):
        adapter = _make_adapter(output_shape=(1, 5))
        model = ClassificationModel(
            adapter,
            configuration={"topk": 3, "labels": ["a", "b", "c", "d", "e"]},
        )
        outputs = {"output": np.array([[0.1, 5.0, 0.2, 0.05, 0.15]])}
        labels = model.get_multiclass_predictions(outputs)
        assert len(labels) == 3
        assert labels[0].name == "b"


# ---------------------------------------------------------------------------
# sigmoid_numpy
# ---------------------------------------------------------------------------


class TestSigmoidNumpy:
    def test_basic(self):
        result = sigmoid_numpy(np.array([0.0]))
        np.testing.assert_allclose(result, 0.5, atol=1e-6)

    def test_large_positive(self):
        result = sigmoid_numpy(np.array([100.0]))
        np.testing.assert_allclose(result, 1.0, atol=1e-6)

    def test_large_negative(self):
        result = sigmoid_numpy(np.array([-100.0]))
        np.testing.assert_allclose(result, 0.0, atol=1e-6)


# ---------------------------------------------------------------------------
# GreedyLabelsResolver
# ---------------------------------------------------------------------------


class TestGreedyLabelsResolver:
    def _make_config(self):
        return {
            "cls_heads_info": {
                "label_to_idx": {"animal": 0, "cat": 1, "dog": 2},
                "all_groups": [["animal"], ["cat", "dog"]],
            },
            "label_tree_edges": [["cat", "animal"], ["dog", "animal"]],
        }

    def test_resolve_labels_with_predecessors(self):
        config = self._make_config()
        resolver = GreedyLabelsResolver(config)
        predictions = [("animal", 0.9), ("cat", 0.8)]
        labels = resolver.resolve_labels(predictions)
        names = [lbl.name for lbl in labels]
        assert "animal" in names
        assert "cat" in names

    def test_resolve_missing_predecessor(self):
        """When 'animal' is not a candidate (score=0), 'cat' should not be added
        because get_predecessors returns [] when a predecessor is missing."""
        config = self._make_config()
        resolver = GreedyLabelsResolver(config)
        # Only 'cat' predicted, 'animal' has 0 score so not a candidate
        predictions = [("cat", 0.8)]
        labels = resolver.resolve_labels(predictions)
        names = [lbl.name for lbl in labels]
        # 'cat' requires 'animal' as predecessor; since 'animal' is not a candidate,
        # get_predecessors returns [], so 'cat' should not appear in output
        assert "cat" not in names


# ---------------------------------------------------------------------------
# ProbabilisticLabelsResolver
# ---------------------------------------------------------------------------


class TestProbabilisticLabelsResolver:
    def _make_config(self):
        return {
            "cls_heads_info": {
                "label_to_idx": {"animal": 0, "cat": 1, "dog": 2},
                "all_groups": [["animal"], ["cat", "dog"]],
            },
            "label_tree_edges": [["cat", "animal"], ["dog", "animal"]],
        }

    def test_resolve_labels(self):
        config = self._make_config()
        resolver = ProbabilisticLabelsResolver(config)
        predictions = [("animal", 0.9), ("cat", 0.8)]
        labels = resolver.resolve_labels(predictions)
        assert len(labels) >= 1

    def test_suppress_descendant_output(self):
        config = self._make_config()
        resolver = ProbabilisticLabelsResolver(config)
        hard = {"animal": 0.0, "cat": 1.0, "dog": 1.0}
        result = resolver._suppress_descendant_output(hard)  # noqa: SLF001
        assert result["cat"] == 0.0
        assert result["dog"] == 0.0

    def test_resolve_exclusive_labels(self):
        config = self._make_config()
        resolver = ProbabilisticLabelsResolver(config)
        label_to_prob = {"animal": 0.9, "cat": 0.8, "dog": 0.0}
        result = resolver._resolve_exclusive_labels(label_to_prob)  # noqa: SLF001
        assert result["animal"] == 1.0
        assert result["cat"] == 1.0
        assert result["dog"] == 0.0

    def test_add_missing_ancestors(self):
        config = self._make_config()
        resolver = ProbabilisticLabelsResolver(config)
        label_to_prob = {"cat": 0.8}
        result = resolver._add_missing_ancestors(label_to_prob)  # noqa: SLF001
        assert "animal" in result
        assert result["animal"] == 0.0


# ---------------------------------------------------------------------------
# SimpleLabelsGraph
# ---------------------------------------------------------------------------


class TestSimpleLabelsGraph:
    def test_add_edge_and_get_children(self):
        g = SimpleLabelsGraph(["a", "b", "c"])
        g.add_edge("a", "b")
        assert "b" in g.get_children("a")

    def test_get_parent(self):
        g = SimpleLabelsGraph(["a", "b"])
        g.add_edge("a", "b")
        assert g.get_parent("b") == "a"
        assert g.get_parent("a") is None

    def test_get_ancestors(self):
        g = SimpleLabelsGraph(["a", "b", "c"])
        g.add_edge("a", "b")
        g.add_edge("b", "c")
        ancestors = g.get_ancestors("c")
        assert "c" in ancestors
        assert "b" in ancestors
        assert "a" in ancestors

    def test_topological_sort(self):
        g = SimpleLabelsGraph(["a", "b", "c"])
        g.add_edge("a", "b")
        g.add_edge("b", "c")
        order = g.topological_sort()
        assert order.index("a") < order.index("b")
        assert order.index("b") < order.index("c")

    def test_topological_sort_cycle_detection(self):
        g = SimpleLabelsGraph(["a", "b"])
        g._adj["a"].append("b")  # noqa: SLF001
        g._adj["b"].append("a")  # noqa: SLF001
        with pytest.raises(RuntimeError):
            g.topological_sort()

    def test_cache_invalidation(self):
        g = SimpleLabelsGraph(["a", "b"])
        _ = g.get_labels_in_topological_order()
        assert g._topological_order_cache is not None  # noqa: SLF001
        g.add_edge("a", "b")
        assert g._topological_order_cache is None  # noqa: SLF001

    def test_get_labels_uses_cache(self):
        g = SimpleLabelsGraph(["a", "b"])
        g.add_edge("a", "b")
        result1 = g.get_labels_in_topological_order()
        result2 = g.get_labels_in_topological_order()
        assert result1 is result2


# ---------------------------------------------------------------------------
# _get_non_xai_names / _append_xai_names
# ---------------------------------------------------------------------------


class TestXaiHelpers:
    def test_get_non_xai_names_filters(self):
        names = ["output", "saliency_map", "feature_vector", "other"]
        result = _get_non_xai_names(names)
        assert result == ["output", "other"]

    def test_get_non_xai_names_no_xai(self):
        names = ["output", "other"]
        result = _get_non_xai_names(names)
        assert result == ["output", "other"]

    def test_append_xai_names_adds(self):
        output_names = ["output"]
        _append_xai_names({"output": 1, "saliency_map": 2, "feature_vector": 3}, output_names)
        assert "saliency_map" in output_names
        assert "feature_vector" in output_names

    def test_append_xai_names_none_present(self):
        output_names = ["output"]
        _append_xai_names({"output": 1}, output_names)
        assert len(output_names) == 1


# ---------------------------------------------------------------------------
# Additional coverage tests
# ---------------------------------------------------------------------------


class TestClassificationModelPreload:
    def test_preload_true_calls_load(self):
        """Line 69: preload=True triggers self.load()."""
        adapter = _make_adapter(output_shape=(1, 10))
        ClassificationModel(adapter, configuration={}, preload=True)
        adapter.load_model.assert_called()


class TestGreedyLabelsResolverDuplicateSkip:
    def test_duplicate_candidate_skipped(self):
        """Line 332: duplicate label in candidates is skipped."""
        config = {
            "cls_heads_info": {
                "label_to_idx": {"animal": 0, "cat": 1, "dog": 2},
                "all_groups": [["cat", "dog"], ["animal"]],
            },
            "label_tree_edges": [["cat", "animal"], ["dog", "animal"]],
        }
        resolver = GreedyLabelsResolver(config)
        # "cat" is max in group 0, "animal" is the single element in group 1
        # Processing "cat" adds predecessors ["animal", "cat"]
        # Processing "animal" finds it already in output_labels → continue (line 332)
        predictions = [("animal", 0.9), ("cat", 0.8), ("dog", 0.3)]
        labels = resolver.resolve_labels(predictions)
        names = [lbl.name for lbl in labels]
        assert "animal" in names
        assert "cat" in names
