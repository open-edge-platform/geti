# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import os

import pytest
from jobs_common.features.feature_flag_provider import FeatureFlag, FeatureFlagProvider


@pytest.mark.DatasetIEMsComponent
class TestFeatureFlagProvider:
    @staticmethod
    def set_flag(flag: FeatureFlag, value: bool = True):
        os.environ[flag.name] = str(value)

    @staticmethod
    def remove_flag(flag: FeatureFlag):
        if flag.name in os.environ:
            del os.environ[flag.name]

    def test_feature_flag_provider(self) -> None:
        """
        Checks that FeatureFlagProvider returns the correct value for each feature flag
        """
        for flag in FeatureFlag:
            self.set_flag(flag, True)
            assert FeatureFlagProvider.is_enabled(flag)
            self.set_flag(flag, False)
            assert not FeatureFlagProvider.is_enabled(flag)

            # Check undefined flag return false
            self.remove_flag(flag)
            assert not FeatureFlagProvider.is_enabled(flag)
