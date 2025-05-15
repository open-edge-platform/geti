# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging
import os
import pathlib
from collections.abc import Generator
from unittest.mock import patch

import pytest
from _pytest.fixtures import FixtureRequest
from iai_core.repos.base.mongo_connector import MongoConnector
from migration.utils.connection import MongoDBConnection
from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_for_logs
from testcontainers.mongodb import MongoDbContainer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

os.environ["TEST_METRICS"] = "true"
os.environ["ENABLE_METRICS"] = "true"
os.environ["S3_CREDENTIALS_PROVIDER"] = "local"


@pytest.fixture(scope="session", autouse=True)
def mongodb_testcontainer() -> Generator[MongoDbContainer, None, None]:
    image_name = "mongo:7.0.7"
    logger.info(f"Pulling MongoDB testcontainer image from: {image_name}")
    with MongoDbContainer(image_name) as mongo:
        db_url = mongo.get_connection_url()
        with (
            patch.object(MongoConnector, "get_connection_string", return_value=db_url),
            patch.object(MongoDBConnection, "_get_connection_string", return_value=db_url),
        ):
            yield mongo


@pytest.fixture(scope="session", autouse=True)
def fxt_spicedb_server(request: FixtureRequest):
    container = DockerContainer("ghcr.io/authzed/spicedb:v1.34.0")
    container.with_bind_ports(50051, 50051)
    test_dir = pathlib.Path(__file__).parent
    container.with_volume_mapping((test_dir / "configs/spicedb.zaml").resolve(), "/schema/spicedb.zaml", "ro")
    container.with_env("SPICEDB_GRPC_PRESHARED_KEY", "test")
    container.with_command(
        [
            "serve-testing",
            "--skip-release-check",
            "--load-configs",
            "/schema/spicedb.zaml",
        ]
    )
    container.start()

    wait_for_logs(container, "grpc server started serving", timeout=30)

    yield container

    container.stop()


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
