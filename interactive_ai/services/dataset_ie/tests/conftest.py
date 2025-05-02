# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""
This module defines the test configuration
"""

import logging
import os
import pathlib
import shutil
import tempfile
from unittest.mock import patch

import jwt
import pytest
from _pytest.fixtures import FixtureRequest
from starlette.testclient import TestClient
from testcontainers.mongodb import MongoDbContainer

from application.export_management import ExportManager
from application.import_management import ImportManager
from communication.endpoints.main import app

from geti_fastapi_tools.dependencies import get_source_fastapi, get_user_id_fastapi
from geti_types import ID, RequestSource
from iai_core_py.entities.dataset_storage import DatasetStorage
from iai_core_py.entities.project import Project
from iai_core_py.repos import ProjectRepo
from iai_core_py.repos.base.mongo_connector import MongoConnector
from iai_core_py.utils.deletion_helpers import DeletionHelpers

## a valid JWT x-auth-request-access-token
payload = {"preferred_username": "testing"}
ENCODED_TOKEN = jwt.encode(payload=payload, key="secret")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.fixture(scope="session", autouse=True)
def mongodb_testcontainer():
    image_name = "mongo:7.0.7"
    logger.info(f"Pulling MongoDB testcontainer image from: {image_name}")
    with MongoDbContainer(image_name) as mongo:
        db_url = mongo.get_connection_url()
        with patch.object(MongoConnector, "get_connection_string", return_value=db_url):
            yield mongo


def detect_fixtures(module_name: str) -> list:
    """
    Searches for fixtures at given path provided in python module notation,
    starting on current working directory.
    :param module_name: name of module where fixtures folder is located
    :return: list of string representing fixture modules/plugins
    """
    fixtures: set = set()
    fixtures_path = pathlib.Path(os.path.dirname(__file__)) / "fixtures"
    for fixture_path in fixtures_path.iterdir():
        if not fixture_path.stem.endswith("__"):
            fixtures.add(".".join([module_name, "fixtures", fixture_path.stem]))
    return list(fixtures)


pytest_plugins = detect_fixtures("tests")


@pytest.fixture
def fxt_import_manager():
    return ImportManager()


@pytest.fixture
def fxt_export_manager():
    return ExportManager()


@pytest.fixture
def fxt_temp_directory(request: FixtureRequest):
    """
    This fixture creates temporary directory
    """

    dir_path = tempfile.mkdtemp()
    request.addfinalizer(lambda: shutil.rmtree(dir_path))
    yield dir_path


@pytest.fixture
def fxt_dataset_id(fxt_mongo_id):
    return fxt_mongo_id(1000)


@pytest.fixture
def fxt_dataset_storage_id(fxt_mongo_id):
    return fxt_mongo_id(1000)


@pytest.fixture
def fxt_project_id(fxt_mongo_id):
    return fxt_mongo_id(1002)


@pytest.fixture
def fxt_job_id(fxt_mongo_id):
    return fxt_mongo_id(1003)


@pytest.fixture
def fxt_user_id(fxt_mongo_id):
    return fxt_mongo_id(1004)


@pytest.fixture
def fxt_dataset_storage(fxt_dataset_storage_id, fxt_project_id):
    return DatasetStorage(
        name="patched training data",
        _id=fxt_dataset_storage_id,
        project_id=fxt_project_id,
        use_for_training=True,
    )


@pytest.fixture
def fxt_project(fxt_project_id, fxt_dataset_storage, request: FixtureRequest):
    project = Project(
        id=fxt_project_id,
        name="patched_project",
        creator_id="creator",
        description="patched_project",
        dataset_storages=[fxt_dataset_storage],
    )
    repo = ProjectRepo()
    repo.save(project)
    request.addfinalizer(lambda: DeletionHelpers.delete_project_by_id(project_id=fxt_project_id))
    return project


def patched_user() -> ID:
    return ID("dummy_user")


@pytest.fixture(scope="function")
def client(fxt_temp_directory: str) -> TestClient:
    """Test client for FastAPI app.

    It cleans up ImportDataRepo and ExportDataRepo for each test.
    """
    app.dependency_overrides[get_user_id_fastapi] = patched_user
    app.dependency_overrides[get_source_fastapi] = lambda: RequestSource.UNKNOWN
    return TestClient(app)


@pytest.fixture
def fxt_url_prefix(fxt_organization_id, fxt_workspace_id):
    return f"/api/v1/organizations/{str(fxt_organization_id)}/workspaces/{str(fxt_workspace_id)}"


@pytest.fixture
def fxt_headers():
    return {"x-auth-request-access-token": ENCODED_TOKEN}


@pytest.fixture
def fxt_download_path(fxt_organization_id, fxt_workspace_id, fxt_dataset_id):
    return (
        f"/api/v1/fileservice/temporaryfiles/organizations/{fxt_organization_id}"
        f"/workspaces/{fxt_workspace_id}/exports/{fxt_dataset_id}/dataset.zip"
    )
