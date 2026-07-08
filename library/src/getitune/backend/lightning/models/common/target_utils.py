# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Shared helpers for preparing model training targets.

This module provides defensive utilities used by the detection and instance
segmentation models when converting a :class:`~getitune.data.entity.sample.SampleBatch`
into model-specific training targets.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from getitune.data.entity.sample import SampleBatch

logger = logging.getLogger(__name__)


def align_sample_batch_annotations(entity: SampleBatch) -> SampleBatch:
    """Align per-image annotation counts (bboxes/labels/masks/keypoints) in place.

    Many detection and instance-segmentation criteria concatenate a sample's
    per-image ``boxes``, ``labels`` and ``masks`` and require their counts to
    match:

    * DETR-style models (RF-DETR, RT-DETR, DEIM/D-FINE, DEIMv2) feed them to a
      Hungarian matcher that adds per-target cost matrices element-wise. A count
      mismatch raises ``RuntimeError: The size of tensor a (N) must match the
      size of tensor b (M) ...`` deep inside the matcher.
    * mmdet-based models (Mask R-CNN, RTMDet-Inst, ATSS, SSD, YOLOX) build
      ``InstanceData`` which enforces that all instance-level fields share the
      same length.

    The data pipeline should already guarantee consistent counts, but geometric
    transforms (cropping, tiling, bounding-box sanitization) can occasionally
    drop one annotation type without dropping the paired ones. When that
    happens this helper realigns the affected image's annotations to their
    common minimum length and logs a warning, so training degrades gracefully
    instead of crashing inside the loss.

    The trimming is a best-effort safety net: it keeps the first ``n`` entries
    of each field (annotations are built per-instance in a consistent order, so
    trailing extras are the most likely divergence). It only mutates images
    whose counts actually diverge, leaving the common (consistent) path
    untouched.

    Args:
        entity: The batch to align. Modified in place.

    Returns:
        The same ``entity`` instance (for convenient chaining).
    """
    bboxes = entity.bboxes
    labels = entity.labels
    masks = entity.masks
    keypoints = entity.keypoints

    # Nothing to align if there are no instance-level annotations.
    if bboxes is None and labels is None and masks is None and keypoints is None:
        return entity

    for i in range(entity.batch_size):
        counts: list[int] = [
            int(field[i].shape[0])
            for field in (bboxes, labels, masks, keypoints)
            if field is not None and i < len(field) and field[i] is not None
        ]

        if not counts:
            continue

        n = min(counts)
        if all(c == n for c in counts):
            continue  # already consistent — leave untouched

        logger.warning(
            "Sample %d has mismatched annotation counts "
            "(bboxes=%s, labels=%s, masks=%s, keypoints=%s); aligning to %d.",
            i,
            None if bboxes is None else int(bboxes[i].shape[0]),
            None if labels is None else int(labels[i].shape[0]),
            None if masks is None else int(masks[i].shape[0]),
            None if keypoints is None else int(keypoints[i].shape[0]),
            n,
        )

        if bboxes is not None and bboxes[i] is not None:
            bboxes[i] = bboxes[i][:n]  # pyrefly: ignore[unsupported-operation]
        if labels is not None and labels[i] is not None:
            labels[i] = labels[i][:n]
        if masks is not None and masks[i] is not None:
            masks[i] = masks[i][:n]  # pyrefly: ignore[unsupported-operation]
        if keypoints is not None and keypoints[i] is not None:
            keypoints[i] = keypoints[i][:n]

    return entity
