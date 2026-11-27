"""Classification result type."""

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import TYPE_CHECKING, Generator

from .base import Result
from .utils import array_shape_to_str

if TYPE_CHECKING:
    import numpy as np


class Label:
    """Entity representing a predicted label."""

    def __init__(
        self,
        id: int | None = None,
        name: str | None = None,
        confidence: float | None = None,
    ) -> None:
        self.name = name
        self.confidence = confidence
        self.id = id

    def __iter__(self) -> Generator:
        output = (self.id, self.name, self.confidence)
        for i in output:
            yield i

    def __str__(self) -> str:
        return f"{self.id} ({self.name}): {self.confidence:.3f}"


class ClassificationResult(Result):
    """Results for classification models."""

    def __init__(
        self,
        top_labels: list[Label] | None = None,
        saliency_map: np.ndarray | None = None,
        feature_vector: np.ndarray | None = None,
        raw_scores: np.ndarray | None = None,
    ) -> None:
        self.top_labels = top_labels
        self.saliency_map = saliency_map
        self.feature_vector = feature_vector
        self.raw_scores = raw_scores

    def __str__(self) -> str:
        assert self.top_labels is not None
        labels = ", ".join(str(label) for label in self.top_labels)
        return (
            f"{labels}, {array_shape_to_str(self.saliency_map)}, {array_shape_to_str(self.feature_vector)}, "
            f"{array_shape_to_str(self.raw_scores)}"
        )
