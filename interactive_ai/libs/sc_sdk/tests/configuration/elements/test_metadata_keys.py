# INTEL CONFIDENTIAL
#
# Copyright (C) 2021 Intel Corporation
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

from sc_sdk.configuration.elements.metadata_keys import (
    AFFECTS_OUTCOME_OF,
    DEFAULT_VALUE,
    DESCRIPTION,
    EDITABLE,
    ENUM_NAME,
    HEADER,
    MAX_VALUE,
    MIN_VALUE,
    OPTIONS,
    TYPE,
    UI_RULES,
    VISIBLE_IN_UI,
    WARNING,
    allows_dictionary_values,
    allows_model_template_override,
)


@pytest.mark.ScSdkComponent
class TestMetadataKeys:
    def test_allows_model_template_override(self):
        """
        <b>Description:</b>
        Check "allows_model_template_override" function

        <b>Input data:</b>
        "keyword" constant

        <b>Expected results:</b>
        Test passes if value returned by "allows_model_template_override" function is equal to expected

        <b>Steps</b>
        1. Check value returned by "allows_model_template_override" function for "keyword" that can be overridden
        2. Check value returned by "allows_model_template_override" function for "keyword" that can not be overridden
        """
        # Checking value returned by "allows_model_template_override" for "keyword" that can be overridden
        for keyword in [
            DEFAULT_VALUE,
            MIN_VALUE,
            MAX_VALUE,
            DESCRIPTION,
            HEADER,
            EDITABLE,
            WARNING,
            VISIBLE_IN_UI,
            OPTIONS,
            ENUM_NAME,
            UI_RULES,
            AFFECTS_OUTCOME_OF,
        ]:
            assert allows_model_template_override(keyword)
        # Checking value returned by "allows_model_template_override" for "keyword" that can not be overridden
        for keyword in [TYPE, "non-constant keyword"]:
            assert not allows_model_template_override(keyword)

    def test_allows_dictionary_values(self):
        """
        <b>Description:</b>
        Check "allows_dictionary_values" function

        <b>Input data:</b>
        "keyword" constant

        <b>Expected results:</b>
        Test passes if value returned by "allows_dictionary_values" function is equal to expected

        <b>Steps</b>
        1. Check value returned by "allows_dictionary_values" function for "keyword" that allowed to have a dictionary
        as its value
        2. Check value returned by "allows_dictionary_values" function for "keyword" that not allowed to have a
        dictionary as its value
        """
        # Checking value returned by "allows_dictionary_values" for "keyword" that allowed to have a dictionary as its
        # value
        for keyword in [UI_RULES, OPTIONS]:
            assert allows_dictionary_values(keyword)
        # Checking value returned by "allows_dictionary_values" for "keyword" that not allowed to have a dictionary as
        # its value
        for keyword in [
            DEFAULT_VALUE,
            MIN_VALUE,
            MAX_VALUE,
            DESCRIPTION,
            HEADER,
            WARNING,
            EDITABLE,
            VISIBLE_IN_UI,
            AFFECTS_OUTCOME_OF,
            TYPE,
            ENUM_NAME,
            "non-constant keyword",
        ]:
            assert not allows_dictionary_values(keyword)
