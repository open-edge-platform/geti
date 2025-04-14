# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import pytest

from sc_sdk.configuration.enums.config_element_type import ConfigElementType
from sc_sdk.configuration.enums.utils import get_enum_names


@pytest.mark.ScSdkComponent
class TestMetadataKeys:
    def test_get_enum_names(self):
        """
        <b>Description:</b>
        Check "get_enum_names" function

        <b>Input data:</b>
        Enum object

        <b>Expected results:</b>
        Test passes if list returned by "get_enum_names" function is equal to expected
        """
        assert get_enum_names(ConfigElementType) == [
            "INTEGER",
            "FLOAT",
            "BOOLEAN",
            "FLOAT_SELECTABLE",
            "SELECTABLE",
            "PARAMETER_GROUP",
            "CONFIGURABLE_PARAMETERS",
            "RULE",
            "UI_RULES",
        ]
