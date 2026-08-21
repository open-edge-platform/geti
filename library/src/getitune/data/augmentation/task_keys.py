# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Which annotation types the GPU augmentation pipeline transforms, per task.

Pulled out on its own because it's a fact about the task, not about which
backend is running it: `GPUAugmentationCallback` (Lightning) and
`GetiTuneHFTrainer` (Hugging Face) both need exactly the same answer to
"what should Kornia's ``AugmentationSequential`` also transform besides the
image, for this task?" Masks for instance segmentation get an extra channel
dimension added and removed around the Kornia call; that stays in
``GPUAugmentationPipeline.forward`` since it's a Kornia-shape detail, not a
task fact.

``backend/lightning/callbacks/gpu_augmentation.py`` still keeps its own copy
of this table rather than importing it. It has no test coverage today, so
the plan is to switch it over once one exists, rather than edit tested and
untested code in the same change.
"""

from __future__ import annotations

from getitune.types.task import TaskType

DATA_KEYS_BY_TASK: dict[TaskType, tuple[str, ...]] = {
    TaskType.MULTI_CLASS_CLS: ("label",),
    TaskType.MULTI_LABEL_CLS: ("label",),
    TaskType.DETECTION: ("bbox_xyxy", "label"),
    TaskType.INSTANCE_SEGMENTATION: ("bbox_xyxy", "mask", "label"),
    TaskType.KEYPOINT_DETECTION: ("keypoints", "label"),
    TaskType.SEMANTIC_SEGMENTATION: ("mask",),
}
