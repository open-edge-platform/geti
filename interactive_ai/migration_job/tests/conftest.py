# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import os

import pytest

BASE_PATH = os.path.dirname(os.path.realpath(__file__))

os.environ["POSTGRES_HOST"] = "127.0.0.42"
os.environ["POSTGRES_PORT"] = "55432"
os.environ["POSTGRES_USER"] = "POSTGRES_USER_FOR_TESTS"
os.environ["POSTGRES_PASSWORD"] = "POSTGRES_USER_PASSWORD_FOR_TESTS"
os.environ["POSTGRES_DB"] = "POSTGRES_DATABASE_FOR_TESTS"
os.environ["SPICEDB_POSTGRES_USER"] = "SPICEDB_USER_FOR_TESTS"
os.environ["SPICEDB_POSTGRES_PASSWORD"] = "SPICEDB_PASSWORD_FOR_TESTS"

migration_py = os.path.join(BASE_PATH, "../app/run_migration.py")


@pytest.fixture(scope="function", autouse=True)
def revert_environ():
    """Reverts os.environ changes after the test."""
    environ_orig = dict(os.environ)

    yield

    keys_to_delete = set(os.environ).difference(environ_orig)
    for key in keys_to_delete:
        os.environ.pop(key)
    os.environ.update(environ_orig)
