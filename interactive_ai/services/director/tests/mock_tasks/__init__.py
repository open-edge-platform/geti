# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from .detection import register_detection_task
from .multi_classification import register_classification_task

__all__ = [
    "register_classification_task",
    "register_detection_task",
]
