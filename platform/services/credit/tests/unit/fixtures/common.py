# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import random
import string

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(scope="function")
def organization_id():
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=10))


@pytest.fixture(scope="function")
def workspace_id():
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=10))


@pytest.fixture
def endpoint_url():
    def _endpoint_url(organization_id, sub_path):
        return f"/api/v1/organizations/{organization_id}/{sub_path}"

    return _endpoint_url
