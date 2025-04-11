# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import os
from enum import Enum


class FeatureFlag(str, Enum):
    """Represents feature flags"""

    CREDIT_SYSTEM = "FEATURE_FLAG_CREDIT_SYSTEM"
    FREE_TIER = "FEATURE_FLAG_FREE_TIER"
    REQUIRE_INVITATION_LINK = "FEATURE_FLAG_SAAS_REQUIRE_INVITATION_LINK"
    REQ_ACCESS = "FEATURE_FLAG_REQ_ACCESS"


def is_feature_flag_enabled(feature: FeatureFlag) -> bool:
    """Checks if a given feature flag is enabled."""
    flag_value = os.environ.get(feature.value, "false").lower()
    return flag_value == "true"
