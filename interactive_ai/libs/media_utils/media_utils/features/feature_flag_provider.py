# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
This module contains the FeatureFlagProvider class
"""

import logging
from enum import Enum, auto

logger = logging.getLogger(__name__)


class FeatureFlag(Enum):
    FEATURE_FLAG_DECORD_VIDEO_DECODER = auto()
