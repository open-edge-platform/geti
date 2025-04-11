# INTEL CONFIDENTIAL
#
# Copyright (C) 2022 Intel Corporation
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
import os

from features.feature_flags import FeatureFlag

from geti_feature_tools import FeatureFlagProvider


class TestUtilsFeatureFlagProvider:
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
