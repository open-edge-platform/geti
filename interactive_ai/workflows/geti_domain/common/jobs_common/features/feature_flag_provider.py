# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
This module contains the FeatureFlagProvider class
"""

import logging
import os
from enum import Enum, auto

from iai_core.utils.type_helpers import str2bool

logger = logging.getLogger(__name__)


class FeatureFlag(Enum):
    """
    Enum containing all available feature flags
    """

    FEATURE_FLAG_ALLOW_EXTERNAL_KEY_PROJECT_IMPORT = auto()
    FEATURE_FLAG_OTX_VERSION_SELECTION = auto()
    FEATURE_FLAG_KEYPOINT_DETECTION = auto()
    FEATURE_FLAG_FP16_INFERENCE = auto()


class FeatureFlagProvider:
    """
    FeatureFlagProvider
    """

    @staticmethod
    def is_enabled(feature_flag: FeatureFlag):  # noqa: ANN205
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
