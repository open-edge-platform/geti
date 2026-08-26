# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Bounded per-track appearance memory (gallery + EMA).

An `AppearanceGallery` holds the appearance history of a single track in two
representations:

- a fixed-capacity FIFO gallery of recent descriptors, and
- an exponential-moving-average (EMA) descriptor, optionally confidence-scaled.

A cosine admission gate rejects descriptors too dissimilar from the track's
current representation. A tracker keeps one `AppearanceGallery` per track id,
feeds it the matched detection's descriptor via `update`, and queries the
appearance distance of candidate detections via `distance`.
"""

from __future__ import annotations

from collections import deque

import numpy as np

from getitrack.matching.appearance import cosine_distance, l2_normalize


class AppearanceGallery:
    """Fixed-capacity appearance memory for one track.

    The FIFO gallery is always maintained and queried. When ``use_ema`` is set,
    the running EMA descriptor is queried as one extra representative alongside
    the FIFO entries, and `distance` reports the minimum cosine distance over the
    combined set.

    Attributes:
        gallery_size: Maximum number of descriptors retained in the FIFO
            gallery. The oldest descriptor is evicted once the cap is reached.
        use_ema: When true, the running EMA descriptor is queried in addition to
            the FIFO gallery entries.
        ema_alpha: EMA retention factor in ``(0, 1)``. Higher values keep more
            history. The update is ``ema = (1 - w) * ema + w * feature`` with
            ``w = (1 - ema_alpha) * confidence``.
        admission_threshold: Maximum cosine distance a new descriptor may have
            from the current representation to be admitted. Descriptors above it
            are rejected. Set high (>= 2.0) to admit everything.
    """

    def __init__(
        self,
        *,
        gallery_size: int,
        use_ema: bool,
        ema_alpha: float,
        admission_threshold: float,
    ) -> None:
        self.gallery_size = gallery_size
        self.use_ema = use_ema
        self.ema_alpha = ema_alpha
        self.admission_threshold = admission_threshold
        self._gallery: deque[np.ndarray] = deque(maxlen=gallery_size)
        self._ema: np.ndarray | None = None

    @property
    def is_empty(self) -> bool:
        """True until the first descriptor has been admitted."""
        return self._ema is None and len(self._gallery) == 0

    def __len__(self) -> int:
        return len(self._gallery)

    def update(self, feature: np.ndarray, *, confidence: float = 1.0) -> bool:
        """Admit a descriptor into the memory, subject to the admission gate.

        Args:
            feature: ``(D,)`` appearance descriptor of the matched detection.
            confidence: Detection score in ``[0, 1]`` scaling the EMA step.

        Returns:
            True if the descriptor was admitted, False if the admission gate
            rejected it as too dissimilar from the current representation.
        """
        feat = l2_normalize(np.asarray(feature, dtype=np.float32).reshape(-1))
        representatives = self._representatives()
        if representatives is not None and representatives.shape[0] > 0:
            gate_distance = float(cosine_distance(feat[None, :], representatives).min())
            if gate_distance > self.admission_threshold:
                return False
        if self.use_ema:
            if self._ema is None:
                self._ema = feat
            else:
                weight = (1.0 - self.ema_alpha) * float(confidence)
                self._ema = l2_normalize((1.0 - weight) * self._ema + weight * feat)
        self._gallery.append(feat)
        return True

    def distance(self, features: np.ndarray) -> np.ndarray:
        """Return each candidate's appearance distance to this track.

        Args:
            features: ``(N, D)`` candidate detection descriptors.

        Returns:
            ``(N,)`` float32 cosine distances: the minimum distance over the
            FIFO gallery entries (and, when ``use_ema`` is set, the EMA
            descriptor). An empty memory yields all ``NaN`` (no appearance
            information available).
        """
        candidates = np.asarray(features, dtype=np.float32)
        representatives = self._representatives()
        if representatives is None or representatives.shape[0] == 0:
            return np.full((candidates.shape[0],), np.nan, dtype=np.float32)
        distances = cosine_distance(candidates, representatives)
        return distances.min(axis=1).astype(np.float32)

    def _representatives(self) -> np.ndarray | None:
        """Return the descriptor set queried against, or None when empty.

        The FIFO gallery entries, plus the EMA descriptor when ``use_ema`` is set.
        """
        reps = list(self._gallery)
        if self.use_ema and self._ema is not None:
            reps.append(self._ema)
        if not reps:
            return None
        return np.stack(reps, axis=0)
