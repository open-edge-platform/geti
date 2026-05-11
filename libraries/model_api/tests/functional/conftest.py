#
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#

import pytest


def pytest_addoption(parser):
    parser.addoption("--data", action="store", help="data folder with dataset")


@pytest.fixture(scope="session")
def data(pytestconfig):
    return pytestconfig.getoption("data")
