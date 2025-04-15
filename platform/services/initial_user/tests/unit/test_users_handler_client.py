# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import pytest
from users_handler_client import UsersHandlerConnection

from users_handler.exceptions import UserDoesNotExist


@pytest.fixture
def mock_users_handler_connection(mocker):
    mocker.patch("users_handler_client.UsersHandler")
    mocker.patch("users_handler_client.INITIAL_USER_PASSWORD", "S@mPL3P@55")
    connection = UsersHandlerConnection()
    yield connection


def test_uh_create_initial_user_that_does_not_exist(mock_users_handler_connection):
    mock_users_handler_connection.users_handler.get_user.side_effect = UserDoesNotExist
    mock_users_handler_connection.users_handler.add_user.return_value = True
    user = mock_users_handler_connection.create_initial_user(
        uid="u123456", organization_id="o123456", workspace_id="w123456"
    )
    assert user is True


def test_uh_create_initial_user_that_does_exist(mock_users_handler_connection):
    mock_users_handler_connection.users_handler.get_user.return_value = True
    user = mock_users_handler_connection.create_initial_user(
        uid="u123456", organization_id="o123456", workspace_id="w123456"
    )
    assert user is False
