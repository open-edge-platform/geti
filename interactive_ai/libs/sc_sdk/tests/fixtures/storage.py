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
import http

import pytest
from minio.datatypes import Object


@pytest.fixture
def fxt_http_response():
    """
    Create a realistic HTTP response for testing purposes. Used to mock S3 responses.
    """

    class MockResponse:
        def __init__(self, data: bytes, status_code: int = http.HTTPStatus.OK) -> None:
            self.data = data
            self.status_code = status_code

    def _generate_response(data: bytes, status_code: int = http.HTTPStatus.OK) -> MockResponse:
        return MockResponse(data=data, status_code=status_code)

    yield _generate_response


@pytest.fixture
def fxt_s3_object():
    """
    Create a realistic S3 object retrieved from a Minio get command
    """

    def _generate_response(bucket_name: str = "", object_name: str = "") -> Object:
        return Object(bucket_name=bucket_name, object_name=object_name)

    yield _generate_response
