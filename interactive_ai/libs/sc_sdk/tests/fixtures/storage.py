# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
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
