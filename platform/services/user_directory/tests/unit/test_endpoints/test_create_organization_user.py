"""Tests the endpoints.user_management.create_user module."""

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import base64
from unittest.mock import MagicMock, Mock

import grpc
import pytest
import requests
from endpoints.user_management.create_user import (
    AccountServiceConnection,
    AccountServiceError,
    OpenLDAPConnection,
    get_sub_from_jwt_token,
)
from grpc_interfaces.account_service.pb.user_common_pb2 import UserData

from users_handler.exceptions import UserDoesNotExist
from users_handler.subject_pb2 import IDTokenSubject

from common.ldap import UsersHandlerUser


@pytest.fixture
def mock_account_service_connection():
    connection = AccountServiceConnection()
    connection.client = MagicMock()
    yield connection


@pytest.fixture
def mock_users_handler_connection(mocker):
    mocker.patch("common.ldap.UsersHandler")
    connection = OpenLDAPConnection()
    yield connection


@pytest.fixture
def jwt_mock(mocker):
    request_post_mock = mocker.patch("endpoints.user_management.create_user.requests.post")
    response = requests.Response()
    response._content = b'{"access_token":"default"}'
    request_post_mock.return_value = response
    jwt_decode_mock = mocker.patch("endpoints.user_management.create_user.jwt.decode")
    jwt_decode_mock.return_value = {
        "sub": "sub_123",
    }


def test_create_initial_user_that_exist(mock_account_service_connection):
    already_exists_rpc_error = grpc.RpcError()
    already_exists_rpc_error.details = lambda *x, **y: "user already exists"
    already_exists_rpc_error.code = lambda *x, **y: grpc.StatusCode.ALREADY_EXISTS
    mock_account_service_connection.client.user_stub.create.side_effect = already_exists_rpc_error

    find_user = {
        "first_name": "fist_name",
        "second_name": "second_name",
        "email": "example@example.com",
        "status": "ACT",
    }
    create_user = dict(**find_user, external_id="default")

    with pytest.raises(AccountServiceError):
        mock_account_service_connection.create_user(organization_id="o123456", create_user=create_user)


def test_create_initial_user_that_does_not_exist(mock_account_service_connection):
    mock_account_service_connection.client.user_stub.find.return_value = Mock(total_matched_count=0, users=[])
    mock_account_service_connection.client.user_stub.create.return_value = UserData(id="u123456")
    find_user = {
        "first_name": "fist_name",
        "second_name": "second_name",
        "email": "example@example.com",
        "status": "ACT",
    }
    create_user = dict(**find_user, external_id="default")

    created_user = mock_account_service_connection.create_user(organization_id="o123456", create_user=create_user)

    assert created_user.id == "u123456"
    assert mock_account_service_connection.client.user_stub.create.call_count == 1


def test_uh_create_initial_user_that_does_exist(mock_users_handler_connection):
    mock_users_handler_connection.users_handler.get_user.return_value = True
    payload = {
        "email": "example@example.com",
        "first_name": "first_name",
        "password": base64.b64encode("Example".encode("ascii")).decode("ascii"),
        "roles": [],
    }
    data = UsersHandlerUser(**payload)
    user = mock_users_handler_connection.create_initial_user(uid="u123456", data=data)
    assert user is False


def test_uh_create_initial_user_that_does_not_exist(mock_users_handler_connection):
    mock_users_handler_connection.users_handler.get_user.side_effect = UserDoesNotExist
    mock_users_handler_connection.users_handler.add_user.return_value = True
    payload = {
        "email": "example@example.com",
        "first_name": "first_name",
        "password": base64.b64encode("Example".encode("ascii")).decode("ascii"),
        "roles": [],
    }
    data = UsersHandlerUser(**payload)
    user = mock_users_handler_connection.create_initial_user(uid="u123456", data=data)
    assert user is True


def test_modify_initial_user_external_id(mock_account_service_connection):
    mock_account_service_connection.client.user_stub.modify.return_value = Mock(external_id="e_id")
    find_user = {
        "first_name": "fist_name",
        "second_name": "second_name",
        "email": "example@example.com",
        "status": "ACT",
    }
    external_id = mock_account_service_connection.update_user_external_id(
        uid="u123456", organization_id="o123456", external_id="e_id", find_user=find_user
    )

    assert external_id == "e_id"


def test_get_sub_from_jwt_token():
    uid = "abc123"
    expected_user_id = f"cn={uid},dc=example,dc=org"

    retrieved_sub = get_sub_from_jwt_token(uid)

    # Pad the string if necessary
    padding_needed = len(retrieved_sub) % 4
    retrieved_sub += "=" * padding_needed

    # Decode the serialized IDTokenSubject object
    decoded_bytes = base64.b64decode(retrieved_sub)
    decoded_token_subject = IDTokenSubject()
    decoded_token_subject.ParseFromString(decoded_bytes)

    assert decoded_token_subject.user_id == expected_user_id, (
        f"Expected '{expected_user_id}' but got '{decoded_token_subject.user_id}'"
    )
    assert decoded_token_subject.conn_id == "regular_users", (
        f"Expected 'regular_users' but got '{decoded_token_subject.conn_id}'"
    )
