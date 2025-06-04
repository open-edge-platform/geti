# INTEL CONFIDENTIAL
#
# Copyright (C) 2022 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and your use of them is governed by
# the express license under which they were provided to you ("License"). Unless the License provides otherwise,
# you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is, with no express or implied warranties,
# other than those that are expressly stated in the License.

"""Module used to retrieve information about platform feature configuration."""

import os
from enum import Enum

from constants.feature_flags import FEATURE_FLAGS


class FeatureFlag(str, Enum):
    """Represents feature flags' names"""

    AMBIENT_MESH = "FEATURE_FLAG_AMBIENT_MESH"
    CREDIT_SYSTEM = "FEATURE_FLAG_CREDIT_SYSTEM"
    OFFLINE_INSTALLATION = "FEATURE_FLAG_OFFLINE_INSTALLATION"
    OIDC_CIDAAS = "FEATURE_FLAG_OIDC_CIDAAS"
    SUPPORT_CORS = "FEATURE_FLAG_SUPPORT_CORS"
    USER_ONBOARDING = "FEATURE_FLAG_USER_ONBOARDING"
    MANAGE_USERS = "FEATURE_FLAG_MANAGE_USERS"


def get_updated_feature_flags() -> dict[str, str]:
    """
    Get dictionary with updated values of the FEATURE_FLAGS dictionary if the appropriate environment variable
    has been set
    """
    env_variables = dict(os.environ)
    offline_tools_dir = "tools"
    env_variables[FeatureFlag.OFFLINE_INSTALLATION] = (
        "true" if (os.path.isdir(offline_tools_dir) and os.listdir(offline_tools_dir) != []) else "false"
    )
    return {key: str(env_variables.get(key, default_value)).lower() for key, default_value in FEATURE_FLAGS.items()}


def is_feature_flag_enabled(feature_flag: FeatureFlag) -> bool:
    """
    Returns whether the provided feature flag is enabled

    :param feature_flag: the feature flag to check
    :return: True if enabled, false otherwise
    """
    flag = get_updated_feature_flags().get(feature_flag)

    if flag is None:
        return False

    return flag.lower() in ("true", "1", "t")
