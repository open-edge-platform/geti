# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
