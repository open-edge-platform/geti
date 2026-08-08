# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Shared geometry and the IoU-family distance-metric base class.

Concrete metrics self-register by declaring a ``method`` class variable, so
`BaseDistanceMetric.from_metric` dispatches by `DistanceMetric` the way
`BaseTracker.from_config` resolves algorithms. Every metric is callable as
``metric(boxes_a, boxes_b) -> cost``. All geometry operates on ``xyxy`` arrays.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, ClassVar, NamedTuple

import numpy as np

if TYPE_CHECKING:
    from getitrack.config import DistanceMetric

_BBOX_COLS = 4
_EPS = 1e-7
_CIOU_V_SCALE = 4.0 / (np.pi**2)

_DISTANCE_REGISTRY: dict[DistanceMetric, type[BaseDistanceMetric]] = {}


def _check_shape(arr: np.ndarray, name: str) -> None:
    if arr.ndim != 2 or arr.shape[1] != _BBOX_COLS:
        msg = f"{name} must have shape (N, {_BBOX_COLS}); got {arr.shape}"
        raise ValueError(msg)


def _check_finite(arr: np.ndarray, name: str) -> None:
    if arr.size and not np.isfinite(arr).all():
        msg = f"{name} contains non-finite values (NaN or inf)"
        raise ValueError(msg)


def iou_matrix(boxes_a: np.ndarray, boxes_b: np.ndarray) -> np.ndarray:
    """Return the ``(M, N)`` pairwise IoU similarity (not cost) in ``[0, 1]``.

    Raises on wrong shape or non-finite values.
    """
    _check_shape(boxes_a, "boxes_a")
    _check_shape(boxes_b, "boxes_b")
    _check_finite(boxes_a, "boxes_a")
    _check_finite(boxes_b, "boxes_b")
    m, n = boxes_a.shape[0], boxes_b.shape[0]
    if m == 0 or n == 0:
        return np.zeros((m, n), dtype=np.float32)

    a = boxes_a.astype(np.float32, copy=False)
    b = boxes_b.astype(np.float32, copy=False)
    x1a, y1a, x2a, y2a = a.T
    x1b, y1b, x2b, y2b = b.T

    x_min_i = np.empty((m, n), dtype=np.float32)
    y_min_i = np.empty_like(x_min_i)
    inter_w = np.empty_like(x_min_i)
    inter_h = np.empty_like(x_min_i)

    np.maximum(x1a[:, None], x1b[None, :], out=x_min_i)
    np.minimum(x2a[:, None], x2b[None, :], out=inter_w)
    np.maximum(y1a[:, None], y1b[None, :], out=y_min_i)
    np.minimum(y2a[:, None], y2b[None, :], out=inter_h)
    np.subtract(inter_w, x_min_i, out=inter_w)
    np.subtract(inter_h, y_min_i, out=inter_h)
    np.clip(inter_w, 0.0, None, out=inter_w)
    np.clip(inter_h, 0.0, None, out=inter_h)

    inter = inter_w * inter_h
    area_a = (x2a - x1a) * (y2a - y1a)
    area_b = (x2b - x1b) * (y2b - y1b)
    union = area_a[:, None] + area_b[None, :] - inter
    return (inter / np.maximum(union, _EPS)).astype(np.float32)


class _PairwiseTerms(NamedTuple):
    """Broadcast geometry terms shared by the IoU-family distance metrics.

    Every field is an ``(M, N)`` float32 array aligning ``boxes_a`` rows with
    ``boxes_b`` columns.
    """

    iou: np.ndarray
    """Plain IoU in ``[0, 1]``."""

    union: np.ndarray
    """Union area of each pair."""

    enclosing_area: np.ndarray
    """Area of the smallest axis-aligned box enclosing each pair."""

    enclosing_diag_sq: np.ndarray
    """Squared diagonal length of that enclosing box (``c^2``)."""

    center_dist_sq: np.ndarray
    """Squared Euclidean distance between box centres (``rho^2``)."""

    aspect_v: np.ndarray
    """CIoU aspect-ratio consistency term ``v`` in ``[0, 1)``."""


def _pairwise_terms(boxes_a: np.ndarray, boxes_b: np.ndarray) -> _PairwiseTerms:
    """Derive the shared geometry the extended IoU metrics build on.

    Computes the intersection, union, enclosing-box, centre-distance, and aspect
    terms in one pass so each metric picks the subset it needs.
    """
    a = boxes_a.astype(np.float32, copy=False)
    b = boxes_b.astype(np.float32, copy=False)
    x1a, y1a, x2a, y2a = a.T
    x1b, y1b, x2b, y2b = b.T

    inter_w = np.clip(np.minimum(x2a[:, None], x2b[None, :]) - np.maximum(x1a[:, None], x1b[None, :]), 0.0, None)
    inter_h = np.clip(np.minimum(y2a[:, None], y2b[None, :]) - np.maximum(y1a[:, None], y1b[None, :]), 0.0, None)
    inter = inter_w * inter_h

    wa, ha = x2a - x1a, y2a - y1a
    wb, hb = x2b - x1b, y2b - y1b
    area_a = (wa * ha)[:, None]
    area_b = (wb * hb)[None, :]
    union = area_a + area_b - inter
    iou = inter / np.maximum(union, _EPS)

    enc_w = np.maximum(x2a[:, None], x2b[None, :]) - np.minimum(x1a[:, None], x1b[None, :])
    enc_h = np.maximum(y2a[:, None], y2b[None, :]) - np.minimum(y1a[:, None], y1b[None, :])
    enclosing_area = enc_w * enc_h
    enclosing_diag_sq = enc_w * enc_w + enc_h * enc_h

    cxa, cya = (x1a + x2a) * 0.5, (y1a + y2a) * 0.5
    cxb, cyb = (x1b + x2b) * 0.5, (y1b + y2b) * 0.5
    center_dist_sq = (cxa[:, None] - cxb[None, :]) ** 2 + (cya[:, None] - cyb[None, :]) ** 2

    atan_a = np.arctan(wa / np.maximum(ha, _EPS))[:, None]
    atan_b = np.arctan(wb / np.maximum(hb, _EPS))[None, :]
    aspect_v = _CIOU_V_SCALE * (atan_b - atan_a) ** 2

    return _PairwiseTerms(
        iou=iou.astype(np.float32),
        union=union.astype(np.float32),
        enclosing_area=enclosing_area.astype(np.float32),
        enclosing_diag_sq=enclosing_diag_sq.astype(np.float32),
        center_dist_sq=center_dist_sq.astype(np.float32),
        aspect_v=aspect_v.astype(np.float32),
    )


class BaseDistanceMetric(ABC):
    """Pairwise ``xyxy`` box-distance cost for detection-to-track association.

    Subclasses supply only `_compute` and declare a ``method`` class variable to
    self-register. Stateless: construct once and reuse. Instances are callable
    via `__call__`, which validates inputs before delegating to `_compute`.
    """

    method: ClassVar[DistanceMetric]

    def __init_subclass__(cls, **kwargs: object) -> None:
        """Register a concrete metric under its declared ``method``."""
        super().__init_subclass__(**kwargs)
        method = getattr(cls, "method", None)
        if method is None:
            return  # intermediate subclass without a method; nothing to register
        if method in _DISTANCE_REGISTRY:
            msg = f"distance metric '{method}' already registered by {_DISTANCE_REGISTRY[method].__name__}"
            raise ValueError(msg)
        _DISTANCE_REGISTRY[method] = cls

    @classmethod
    def from_metric(cls, metric: DistanceMetric) -> BaseDistanceMetric:
        """Build the metric registered for ``metric``; raises `KeyError` if none is registered."""
        try:
            metric_cls = _DISTANCE_REGISTRY[metric]
        except KeyError as exc:  # pragma: no cover - registry is populated at package import
            known = sorted(known_metric.value for known_metric in _DISTANCE_REGISTRY)
            msg = f"no distance metric registered for '{metric}'; registered: {known}"
            raise KeyError(msg) from exc
        return metric_cls()

    def __call__(self, boxes_a: np.ndarray, boxes_b: np.ndarray) -> np.ndarray:
        """Return the ``(M, N)`` float32 cost matrix (``1 - similarity``) for the two ``xyxy`` box sets.

        Validates the inputs and short-circuits empty sets, then delegates the
        metric formula to `_compute`.
        """
        _check_shape(boxes_a, "boxes_a")
        _check_shape(boxes_b, "boxes_b")
        _check_finite(boxes_a, "boxes_a")
        _check_finite(boxes_b, "boxes_b")
        if boxes_a.shape[0] == 0 or boxes_b.shape[0] == 0:
            return np.zeros((boxes_a.shape[0], boxes_b.shape[0]), dtype=np.float32)
        return self._compute(boxes_a, boxes_b)

    @abstractmethod
    def _compute(self, boxes_a: np.ndarray, boxes_b: np.ndarray) -> np.ndarray:
        """Return the ``(M, N)`` cost for already-validated, non-empty ``xyxy`` box sets."""
