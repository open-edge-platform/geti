# INTEL CONFIDENTIAL
#
# Copyright (C) 2023 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and
# your use of them is governed by the express license under which they were provided to
# you ("License"). Unless the License provides otherwise, you may not use, modify, copy,
# publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is,
# with no express or implied warranties, other than those that are expressly stated
# in the License.

"""
This module contains the FeatureFlagProvider class
"""

import logging
import os
from enum import Enum, auto

from sc_sdk.utils.type_helpers import str2bool

logger = logging.getLogger(__name__)


class FeatureFlag(Enum):
    FEATURE_FLAG_ANOMALY_REDUCTION = auto()
    FEATURE_FLAG_KEYPOINT_DETECTION = auto()
    FEATURE_FLAG_RETAIN_TRAINING_ARTIFACTS = auto()
    FEATURE_FLAG_STORAGE_SIZE_COMPUTATION = auto()
    FEATURE_FLAG_CREDIT_SYSTEM = auto()


class FeatureFlagProvider:
    @staticmethod
    def is_enabled(feature_flag: FeatureFlag) -> bool:
        """
        Returns whether the provided feature flag is enabled

        :param feature_flag: the feature flag to check
        :return: True if enabled, false otherwise
        """
        value = os.environ.get(feature_flag.name)
        if not value:
            logger.warning(
                "Attempting to access undefined flag %s. Returning false.",
                feature_flag.name,
            )
            enabled = False
        else:
            enabled = str2bool(value)
        return enabled
