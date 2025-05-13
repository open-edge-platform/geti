# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import os
import pathlib
from unittest.mock import patch

import pytest
from geti_types import CTX_SESSION_VAR, make_session
from iai_core.repos.base.mongo_connector import MongoConnector
from testcontainers.mongodb import MongoDbContainer

CTX_SESSION_VAR.set(make_session())
os.environ["DEFAULT_TRAINER_VERSION"] = "2.2"


@pytest.fixture(scope="session", autouse=True)
def mongodb_testcontainer():
    with MongoDbContainer("mongo:7.0.7") as mongo:
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
