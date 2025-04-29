# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE


import pytest

from jwt_utils import lookup_jwt_fields


@pytest.mark.parametrize(
    "decoded_token,fields,expected_result",
    [
        ({"firstName": "foo", "lastName": "bar"}, ["firstName", "given_name"], "foo"),
        ({"given_name": "foo", "family_name": "bar"}, ["firstName", "given_name"], "foo"),
    ],
)
def test_lookup_jwt_fields(decoded_token, fields, expected_result):
    assert lookup_jwt_fields(decoded_token, fields) == expected_result


@pytest.mark.parametrize(
    "decoded_token,fields,expected_result",
    [
        ({"name": "foo", "family_name": "bar"}, ["firstName", "given_name"], ValueError),
        ({}, ["firstName", "given_name"], ValueError),
    ],
)
def test_lookup_jwt_fields_failure(decoded_token, fields, expected_result):
    with pytest.raises(expected_result):
        lookup_jwt_fields(decoded_token, fields)
