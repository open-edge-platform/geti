# INTEL CONFIDENTIAL
#
# Copyright (C) 2021 Intel Corporation
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
import os
import pathlib
from unittest.mock import patch

import pytest
from geti_types import CTX_SESSION_VAR, make_session
from sc_sdk.repos.base.mongo_connector import MongoConnector
from testcontainers.mongodb import MongoDbContainer

CTX_SESSION_VAR.set(make_session())
os.environ["DEFAULT_TRAINER_VERSION"] = "2.2"


@pytest.fixture(scope="session", autouse=True)
def mongodb_testcontainer() -> None:
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
