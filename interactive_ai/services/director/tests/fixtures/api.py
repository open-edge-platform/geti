#  INTEL CONFIDENTIAL
#
#  Copyright (C) 2023 Intel Corporation
#
#  This software and the related documents are Intel copyrighted materials, and
#  your use of them is governed by the express license under which they were provided to
#  you ("License"). Unless the License provides otherwise, you may not use, modify, copy,
#  publish, distribute, disclose or transmit this software or the related documents
#  without Intel's prior written permission.
#
#  This software and the related documents are provided as is,
#  with no express or implied warranties, other than those that are expressly stated
#  in the License.

import pytest
from starlette.testclient import TestClient

from communication.main import app as director_app

from geti_fastapi_tools.dependencies import get_source_fastapi, get_user_id_fastapi
from geti_types import ID, RequestSource

DUMMY_ORGANIZATION_ID = "000000000000000000000001"


def patched_user() -> ID:
    return ID("dummy_user")


@pytest.fixture
def fxt_director_app():
    """
    Dummy user authorized director MS API
    """
    director_app.dependency_overrides[get_user_id_fastapi] = patched_user  # type: ignore
    director_app.dependency_overrides[get_source_fastapi] = lambda: RequestSource.UNKNOWN  # type: ignore
    yield TestClient(director_app)
