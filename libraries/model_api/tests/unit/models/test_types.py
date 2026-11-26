#
# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#

from model_api.models.types import ListValue


def test_string_list_parameter():
    str_list = ListValue(
        value_type=str,
        description="List of strings",
        default_value=["label1", "label2", "label3"],
    )
    assert str_list.value_type is str

    parsed_list = str_list.from_str("1 2 3")

    assert len(parsed_list) == 3
    assert type(parsed_list[0]) is str
