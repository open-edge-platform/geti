# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import numpy as np
from model_api.models.result import ClassificationResult, Label


def test_label_init():
    label = Label(id=0, name="cat", confidence=0.95)
    assert label.id == 0
    assert label.name == "cat"
    assert label.confidence == 0.95


def test_label_str():
    label = Label(id=1, name="dog", confidence=0.85)
    s = str(label)
    assert "1" in s
    assert "dog" in s
    assert "0.850" in s


def test_label_iter():
    label = Label(id=2, name="bird", confidence=0.75)
    values = list(label)
    assert values == [2, "bird", 0.75]


def test_classification_result_init():
    labels = [Label(id=0, name="cat", confidence=0.9)]
    sal = np.ones((3, 10, 10))
    fv = np.array([1.0, 2.0])
    raw = np.array([0.1, 0.9])
    result = ClassificationResult(
        top_labels=labels,
        saliency_map=sal,
        feature_vector=fv,
        raw_scores=raw,
    )
    assert result.top_labels is labels
    assert result.saliency_map is sal


def test_classification_result_init_defaults():
    result = ClassificationResult()
    assert result.top_labels is None
    assert result.saliency_map is None


def test_classification_result_str():
    labels = [
        Label(id=0, name="cat", confidence=0.9),
        Label(id=1, name="dog", confidence=0.1),
    ]
    result = ClassificationResult(top_labels=labels)
    s = str(result)
    assert "cat" in s
    assert "dog" in s
    assert "0.900" in s
