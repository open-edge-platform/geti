# INTEL CONFIDENTIAL
#
# Copyright (C) 2024 Intel Corporation
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

import pytest

from sc_sdk.utils.type_helpers import str2bool


@pytest.mark.ScSdkComponent
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
