# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
