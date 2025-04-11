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
import os
import pathlib

import pytest
from _pytest.fixtures import FixtureRequest
from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_for_logs

os.environ["MONGODB_DATABASE_NAME"] = "geti"
os.environ["TEST_METRICS"] = "true"
os.environ["ENABLE_METRICS"] = "true"
os.environ["S3_CREDENTIALS_PROVIDER"] = "local"


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


@pytest.fixture(scope="session", autouse=True)
def fxt_spicedb_server(request: FixtureRequest):
    container = DockerContainer("092711417317.dkr.ecr.us-west-2.amazonaws.com/third-party/spicedb:v1.34.0.1")
    container.with_bind_ports(50051, 50051)
    test_dir = pathlib.Path(__file__).parent
    container.with_volume_mapping((test_dir / "configs/spicedb.zaml").resolve(), "/schema/spicedb.zaml", "ro")
    container.with_env("SPICEDB_GRPC_PRESHARED_KEY", "test")
    container.with_command(["serve-testing", "--skip-release-check", "--load-configs", "/schema/spicedb.zaml"])
    container.start()

    wait_for_logs(container, "grpc server started serving", timeout=30)

    yield container

    container.stop()


pytest_plugins = detect_fixtures("tests")
