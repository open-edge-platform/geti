# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Global motion compensation (GMC): frame-to-frame camera-motion estimation.

`BaseMotionEstimator` owns the machinery shared by every method: grayscale
conversion, optional downscaling, previous-frame caching, and rescaling the
estimated translation back to full resolution. Subclasses implement only
`_estimate`, the affine fit between two grayscale frames, and register
themselves under a `GMCMethod` via the subclass hook so `from_config` can build
them by name.

The estimate is a ``2x3`` partial-affine (similarity) matrix mapping the previous
frame onto the current one, in the convention consumed by BoT-SORT's state warp.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, ClassVar

import cv2
import numpy as np

if TYPE_CHECKING:
    from getitrack.config import GMCConfig, GMCMethod

_IDENTITY = np.eye(2, 3, dtype=np.float32)


class BaseMotionEstimator(ABC):
    """Estimate the affine camera motion between consecutive frames.

    Concrete estimators set the ``method`` ClassVar and implement `_estimate`.
    Instances are stateful: each `estimate` call caches the frame for the next
    call, so a fresh estimator (or `reset`) is needed per sequence.
    """

    method: ClassVar[GMCMethod]
    _REGISTRY: ClassVar[dict[GMCMethod, type[BaseMotionEstimator]]] = {}

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        # Register only leaf estimators that set a concrete ``method``; abstract
        # intermediates (e.g. the shared feature-matching base) define none.
        method = cls.__dict__.get("method")
        if method is not None:
            BaseMotionEstimator._REGISTRY[method] = cls

    def __init__(self, *, downscale: int = 2) -> None:
        """Initialise with the frame downscale factor (>= 1)."""
        self._downscale = max(1, int(downscale))
        self._prev_gray: np.ndarray | None = None

    @classmethod
    def from_config(cls, config: GMCConfig) -> BaseMotionEstimator:
        """Build the estimator selected by ``config.method``."""
        estimator_cls = cls._REGISTRY.get(config.method)
        if estimator_cls is None:
            known = sorted(m.value for m in cls._REGISTRY)
            msg = f"no GMC estimator registered for method {config.method!r}; known: {known}"
            raise ValueError(msg)
        return estimator_cls(downscale=config.downscale)

    def reset(self) -> None:
        """Forget the cached previous frame, so the next estimate is identity."""
        self._prev_gray = None

    def estimate(self, frame_bgr: np.ndarray) -> np.ndarray:
        """Return the ``2x3`` affine mapping the previous frame onto this one.

        The first call (or the first after `reset`) returns the identity, since
        there is no previous frame to compare against.
        """
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        scale_x = scale_y = 1.0
        if self._downscale > 1:
            height, width = gray.shape[:2]
            # Clamp to at least one pixel so a large downscale on a small frame
            # never produces a zero resize dimension.
            resized_width = max(1, width // self._downscale)
            resized_height = max(1, height // self._downscale)
            scale_x = width / resized_width
            scale_y = height / resized_height
            gray = cv2.resize(gray, (resized_width, resized_height))
        if self._prev_gray is None:
            self._prev_gray = gray
            return _IDENTITY.copy()
        warp = self._estimate(self._prev_gray, gray)
        self._prev_gray = gray
        # Rotation/scale is downscale-invariant; only translation must be rescaled
        # back to full-resolution pixels, using the actual per-axis resize ratios.
        warp[0, 2] *= scale_x
        warp[1, 2] *= scale_y
        return warp

    @abstractmethod
    def _estimate(self, prev_gray: np.ndarray, curr_gray: np.ndarray) -> np.ndarray:
        """Fit the ``2x3`` affine from ``prev_gray`` to ``curr_gray`` (downscaled)."""
