# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging
from enum import Enum, auto

logger = logging.getLogger(__name__)


class FeatureFlag(Enum):
    FEATURE_FLAG_ANOMALY_REDUCTION = auto()
    FEATURE_FLAG_KEYPOINT_DETECTION = auto()
    FEATURE_FLAG_RETAIN_TRAINING_ARTIFACTS = auto()
    FEATURE_FLAG_STORAGE_SIZE_COMPUTATION = auto()
    FEATURE_FLAG_CREDIT_SYSTEM = auto()
    FEATURE_FLAG_NEW_CONFIGURABLE_PARAMETERS = auto()
