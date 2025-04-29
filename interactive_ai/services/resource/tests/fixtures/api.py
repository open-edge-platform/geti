# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import pytest
from starlette.testclient import TestClient

from communication.main import app as resource_app

from geti_fastapi_tools.dependencies import get_source_fastapi, get_user_id_fastapi
from geti_types import ID, RequestSource

DUMMY_ORGANIZATION_ID = "000000000000000000000001"


def patched_user() -> ID:
    return ID("dummy_user")


@pytest.fixture
def fxt_resource_rest():
    """
    Dummy user authorized resource MS API
    """
    resource_app.dependency_overrides[get_user_id_fastapi] = patched_user  # type: ignore
    resource_app.dependency_overrides[get_source_fastapi] = lambda: RequestSource.UNKNOWN  # type: ignore
    yield TestClient(resource_app)
