# INTEL CONFIDENTIAL
#
# Copyright (C) 2024 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and your use of them is governed by
# the express license under which they were provided to you ("License"). Unless the License provides otherwise,
# you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is, with no express or implied warranties,
# other than those that are expressly stated in the License.

import base64

import pytest
import requests

from users_handler.subject_pb2 import IDTokenSubject

from .custom_usertype import custom_mock_usertype
from common import ab64_decode, base64_encode, get_sub_from_jwt_token


@pytest.fixture
def jwt_mock(mocker):
    request_post_mock = mocker.patch("common.requests.post")
    response = requests.Response()
    response._content = b'{"access_token":"default"}'
    request_post_mock.return_value = response
    jwt_decode_mock = mocker.patch("common.jwt.decode")
    jwt_decode_mock.return_value = {
        "sub": "sub_123",
    }


def test_get_sub_from_jwt_token():
    uid = "abc123"
    expected_user_id = f"cn={uid},dc=example,dc=org"

    retrieved_sub = get_sub_from_jwt_token(uid)

    # Pad the string if necessary
    padding_needed = len(retrieved_sub) % 4
    retrieved_sub += "=" * padding_needed

    # Decode the serialized IDTokenSubject object
    decoded_bytes = base64.b64decode(retrieved_sub)
    decoded_token_subject = IDTokenSubject()
    decoded_token_subject.ParseFromString(decoded_bytes)

    assert decoded_token_subject.user_id == expected_user_id, (
        f"Expected '{expected_user_id}' but got '{decoded_token_subject.user_id}'"
    )
    assert decoded_token_subject.conn_id == "regular_users", (
        f"Expected 'regular_users' but got '{decoded_token_subject.conn_id}'"
    )


def test_base64_encode():
    mock_user = custom_mock_usertype(uid="u123456", mail=None)
    encoded_uid = base64_encode(data=mock_user["uid"])
    assert encoded_uid == "dTEyMzQ1Ng"


def test_ab64_decode():
    custom_mock_usertype(uid="u123456", mail=None)
    decoded_uid = ab64_decode(data="dTEyMzQ1Ng")
    assert decoded_uid == "u123456"
