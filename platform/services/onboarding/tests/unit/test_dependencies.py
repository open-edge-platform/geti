# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import os
from unittest.mock import patch

import pytest

from dependencies import FeatureFlag, is_feature_flag_enabled


@pytest.mark.parametrize(
    "feature_flag, env_value, expected_result",
    [
        (FeatureFlag.CREDIT_SYSTEM, "true", True),
        (FeatureFlag.CREDIT_SYSTEM, "false", False),
        (FeatureFlag.FREE_TIER, "False", False),
        (FeatureFlag.FREE_TIER, "True", True),
    ],
)
def test_feature_flags(feature_flag, env_value, expected_result) -> None:
    with patch.dict(os.environ, {feature_flag: env_value}):
        result = is_feature_flag_enabled(feature_flag)
        assert result == expected_result
