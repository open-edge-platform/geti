# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import pytest

from sc_sdk.utils.type_helpers import str2bool


class TestStr2Bool:
    def test_converts_common_true_strings_to_true(self):
        true_strings = ["y", "yes", "t", "true", "on", "1", "Y", "YES", "T", "TRUE", "ON", "1"]
        for s in true_strings:
            assert str2bool(s) is True

    def test_converts_common_false_strings_to_false(self):
        false_strings = ["n", "no", "f", "false", "off", "0", "N", "NO", "F", "FALSE", "OFF", "0"]
        for s in false_strings:
            assert str2bool(s) is False

    def test_raises_value_error_for_invalid_strings(self):
        invalid_strings = ["maybe", "yesno", "2", "", " ", "tru", "fals", "onoff", "10"]
        for s in invalid_strings:
            with pytest.raises(ValueError):
                str2bool(s)

    def test_handles_mixed_case_input(self):
        mixed_case_strings = {"YeS": True, "FaLsE": False, "TrUe": True, "OfF": False, "yEs": True, "fAlSe": False}
        for s, expected in mixed_case_strings.items():
            assert str2bool(s) is expected
