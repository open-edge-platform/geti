import os
from enum import Enum, auto

from geti_feature_tools import FeatureFlagProvider


class TestFeatureFlagProvider:
    def test_is_enabled(self) -> None:
        class FeatureFlag(Enum):
            FEATURE_FLAG_FOO = auto()
            FEATURE_FLAG_BAR = auto()
            FEATURE_FLAG_BAZ = auto()

        # enable 'foo' explicitly, disable 'bar' explicitly, and leave 'baz' undefined
        os.environ["FEATURE_FLAG_FOO"] = "true"
        os.environ["FEATURE_FLAG_BAR"] = "false"

        assert FeatureFlagProvider.is_enabled("FEATURE_FLAG_FOO")
        assert not FeatureFlagProvider.is_enabled("FEATURE_FLAG_BAR")
        assert not FeatureFlagProvider.is_enabled("FEATURE_FLAG_BAZ")

        assert FeatureFlagProvider.is_enabled(FeatureFlag.FEATURE_FLAG_FOO)
        assert not FeatureFlagProvider.is_enabled(FeatureFlag.FEATURE_FLAG_BAR)
        assert not FeatureFlagProvider.is_enabled(FeatureFlag.FEATURE_FLAG_BAZ)
