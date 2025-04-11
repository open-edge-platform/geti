"""Tests the mongodb_create_user module."""

# INTEL CONFIDENTIAL
#
# Copyright (C) 2022 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and your use of them is governed by
# the express license under which they were provided to you ("License"). Unless the License provides otherwise,
# you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is, with no express or implied warranties,
# other than those that are expressly stated in the License.

import os
from collections.abc import Sequence
from unittest.mock import Mock, patch

import pymongo
import pytest

from migration_job.mongodb_create_service_user import _parse_roles, create_user, does_user_exist, main


@pytest.fixture(scope="function")
def mongo_client():
    """Returns a mocked MongoClient."""
    client = Mock(pymongo.MongoClient)
    client.admin = Mock()
    client.admin.command = Mock()
    return client


@pytest.mark.component
def test_main(mongo_client: pymongo.MongoClient):
    """Tests the main function."""
    db_username_service = "service user username"
    db_password_service = "service user password"
    service_user_all_db_roles = "roleA,roleB"

    # Mock environment variables.
    os.environ.update(
        {
            "DATABASE_USERNAME_SERVICE": db_username_service,
            "DATABASE_PASSWORD_SERVICE": db_password_service,
            "SERVICE_USER_ALL_DB_ROLES": service_user_all_db_roles,
        }
    )

    roles_expected = ["roleA", "roleB"]

    with (
        patch("migration_job.mongodb_create_service_user.create_mongo_client") as mongo_client_type_mock,
        patch("migration_job.mongodb_create_service_user.does_user_exist") as does_user_exist_mock,
        patch("migration_job.mongodb_create_service_user._parse_roles") as parse_roles_mock,
        patch("migration_job.mongodb_create_service_user.create_user") as create_user_mock,
    ):
        mongo_client_type_mock.side_effect = [mongo_client]
        does_user_exist_mock.side_effect = [False]
        parse_roles_mock.side_effect = [roles_expected]

        main()

    assert (
        does_user_exist_mock.call_args.kwargs == {"client": mongo_client, "username": db_username_service}
        and parse_roles_mock.call_args.args == (service_user_all_db_roles,)
        and create_user_mock.call_args.kwargs
        == {
            "client": mongo_client,
            "username": db_username_service,
            "password": db_password_service,
            "roles": roles_expected,
        }
    )


@pytest.mark.parametrize(
    "db_username_service,db_password_service,service_user_all_db_roles",
    (
        (
            None,
            "db_password_service",
            "service_user_all_db_roles",
        ),
        (
            "db_username_service",
            None,
            "service_user_all_db_roles",
        ),
        (
            "db_username_service",
            "db_password_service",
            None,
        ),
    ),
)
@pytest.mark.component
def test_main_unset_env_var(db_username_service, db_password_service, service_user_all_db_roles):
    """Tests the main function, negative case.

    Covers a scenario in which some required environment variables are not set.
    """
    # Mock environment variables.
    envs = {
        "DATABASE_USERNAME_SERVICE": db_username_service,
        "DATABASE_PASSWORD_SERVICE": db_password_service,
        "SERVICE_USER_ALL_DB_ROLES": service_user_all_db_roles,
    }
    os.environ.update({key: val for key, val in envs.items() if val})
    for name, value in envs.items():
        if value is None and name in os.environ:
            os.environ.pop(name)
    with pytest.raises(EnvironmentError):
        main()


@pytest.mark.component
def test_create_user(mongo_client: pymongo.MongoClient):
    """Tests the create_user function."""
    username: str = "new user username"
    password: str = "new user password"
    roles = ["roleA", "roleB"]

    create_user(mongo_client, username, password, roles)

    assert (
        mongo_client.admin.command.call_count == 1  # type: ignore
        and mongo_client.admin.command.call_args.args == ("createUser", username)  # type: ignore
        and mongo_client.admin.command.call_args.kwargs == {"pwd": password, "roles": roles}  # type: ignore
    )


@pytest.mark.parametrize(
    "command_response, username, does_user_exist_expected",
    (
        ({"users": [{"user": "foo"}, {"user": "bar"}]}, "foo", True),
        ({"users": [{"user": "foo"}, {"user": "bar"}]}, "bar", True),
        ({"users": [{"user": "foo"}, {"user": "bar"}]}, "other", False),
    ),
)
@pytest.mark.component
def test_does_user_exist(
    mongo_client: pymongo.MongoClient,
    command_response,
    username: str,
    does_user_exist_expected: bool,
):
    """Tests the does_user_exist function."""
    mongo_client.admin.command.side_effect = [command_response]  # type: ignore

    does_user_exist_actual: bool = does_user_exist(mongo_client, username)

    assert does_user_exist_actual == does_user_exist_expected and mongo_client.admin.command.call_args.args == (  # type: ignore
        "usersInfo",
    )


@pytest.mark.parametrize(
    "roles_str, roles_expected",
    (
        ("", []),
        ("a", ["a"]),
        ("a,b", ["a", "b"]),
        ("a ,b", ["a", "b"]),
        (" a,b ", ["a", "b"]),
    ),
)
@pytest.mark.component
def test_parse_roles(roles_str: str, roles_expected: Sequence[str]):
    """Tests the _parse_roles function."""
    roles_actual: Sequence[str] = _parse_roles(roles_str)

    assert list(roles_actual) == list(roles_expected)
