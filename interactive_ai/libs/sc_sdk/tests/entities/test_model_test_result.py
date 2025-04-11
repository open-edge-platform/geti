"""This module tests the ModelTestResult class"""

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
from copy import deepcopy

import pytest

from sc_sdk.entities.model_test_result import NullModelTestResult


@pytest.mark.ScSdkComponent
class TestModelTestResult:
    def test_model_test_result_equality(self, fxt_model_test_result, fxt_mongo_id) -> None:
        """
        <b>Description:</b>
        Check that ModelTestResult equality works correctly

        <b>Input data:</b>
        ModelTestResult instances

        <b>Expected results:</b>
        == and != operations work correctly for various inputs

        <b>Steps</b>
        1. Test ModelTestResult equality
        2. Test NullModelTestResult equality
        """
        copied_model_test_result = deepcopy(fxt_model_test_result)

        second_model_test_result = deepcopy(fxt_model_test_result)
        second_model_test_result.job_id = fxt_mongo_id(10)

        assert fxt_model_test_result == copied_model_test_result
        assert fxt_model_test_result != second_model_test_result
        assert NullModelTestResult() != fxt_model_test_result
        assert fxt_model_test_result != NullModelTestResult()
        assert NullModelTestResult() == NullModelTestResult()
