"""This module tests the ModelTestResult class"""

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from copy import deepcopy

from sc_sdk.entities.model_test_result import NullModelTestResult


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
