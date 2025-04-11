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
from starlette.testclient import TestClient

from services.main import app

from geti_fastapi_tools.dependencies import get_source_fastapi, get_user_id_fastapi
from geti_types import ID, RequestSource


def patched_user() -> ID:
    return ID("dummy_user")


@pytest.fixture
def fxt_test_app():
    """Test client for FastAPI app."""
    app.dependency_overrides[get_user_id_fastapi] = patched_user
    app.dependency_overrides[get_source_fastapi] = lambda: RequestSource.UNKNOWN
    yield TestClient(app)
