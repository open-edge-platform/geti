"""Typing hints for getitune."""

# Copyright (C) 2025-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import functools
import operator
from typing import TYPE_CHECKING

from getitune.backend.lightning.models.base import LightningModel
from getitune.backend.openvino.models.base import OVModel
from getitune.data.entity import BaseSample
from getitune.data.module import DataModule
from getitune.types import PathLike

try:
    from getitune.backend.ultralytics.models.base import UltralyticsModel
except ImportError:  # ultralytics not installed
    UltralyticsModel = None  # type: ignore[assignment, misc]

try:
    from getitune.backend.huggingface.models.base import HFModel
except ImportError:  # transformers/accelerate not installed
    HFModel = None  # type: ignore[assignment, misc]

METRICS = dict[str, float]
ANNOTATIONS = list[BaseSample]
DATA = DataModule | PathLike

if TYPE_CHECKING:
    # Static view: assume every optional backend is available so annotations
    # referring to MODEL type-check against all model classes.
    MODEL = LightningModel | OVModel | UltralyticsModel | HFModel | PathLike
else:
    # Runtime view: build the union from whichever backends imported. Adding a
    # further optional backend needs one more entry, not another branch.
    MODEL = functools.reduce(
        operator.or_,
        [m for m in (UltralyticsModel, HFModel) if m is not None],
        LightningModel | OVModel | PathLike,
    )
