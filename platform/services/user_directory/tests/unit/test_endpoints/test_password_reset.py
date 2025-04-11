# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import asyncio
import base64
import json
from http import HTTPStatus
from unittest.mock import MagicMock

import pytest
from endpoints.user_management.password_reset import UsersHandler
from endpoints.user_management.router import users_router
from fastapi import FastAPI
from fastapi.testclient import TestClient

from users_handler.users_handler import UserType

from common.errors import BadTokenError, GeneralError
from common.interfaces.payload_error import ResponseException
from common.utils import API_BASE_PATTERN

app = FastAPI()
app.include_router(users_router)
client = TestClient(app)

REQUEST_PASSWORD_RESET_ENDPOINT = f"{API_BASE_PATTERN}/users/request_password_reset"
PASSWORD_RESET_ENDPOINT = f"{API_BASE_PATTERN}/users/reset_password"


@pytest.fixture
def get_user_mock(mocker):
    return mocker.patch("endpoints.user_management.password_reset.get_user_by_email")


@pytest.fixture
def send_password_reset_mock(mocker):
    return mocker.patch("endpoints.user_management.password_reset._send_password_reset_email")


@pytest.fixture
def update_password_mock(mocker):
    return mocker.patch("endpoints.user_management.password_reset.update_password")


@pytest.fixture
def users_handler_instance_mock(mocker):
    users_handler_class_mock = mocker.patch("endpoints.user_management.password_reset.UsersHandler", spec=UsersHandler)
    return users_handler_class_mock.return_value


@pytest.fixture
def mock_get_config_map(mocker):
    get_config_map_mock = mocker.patch("endpoints.user_management.password_reset.get_config_map")
    return get_config_map_mock


@pytest.fixture
def mock_get_secret(mocker):
    get_secrets_mock = mocker.patch("common.jwt_token_validation.get_secrets")
    return get_secrets_mock


@pytest.fixture
def loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_user() -> UserType:
    mocked_user = MagicMock(spec=UserType)
    d = {"mail": "example@test.com", "uid": "6544809e-a9bc-477a-a756-fd04a4029a15"}
    mocked_user.__getitem__.side_effect = d.__getitem__
    return mocked_user


def test_request_password_reset(send_password_reset_mock, get_user_mock, mock_get_config_map):
    """Proper use of the endpoint with valid data"""
    email = "test@user.com"

    response = client.post(REQUEST_PASSWORD_RESET_ENDPOINT, data=json.dumps({"email": email}))
    assert response.status_code == HTTPStatus.ACCEPTED
    assert response.text == "Password reset request sent"


def test_request_password_reset_long_email(send_password_reset_mock, get_user_mock, mock_get_config_map):
    email = "testtesttesttesttesttesttesttesttesttesttesttesttest@user.com"

    response = client.post(REQUEST_PASSWORD_RESET_ENDPOINT, data=json.dumps({"email": email}))
    assert response.status_code == HTTPStatus.ACCEPTED
    assert response.text == "Password reset request sent"


def test_request_password_reset_invalid_email_as_input(send_password_reset_mock, get_user_mock):
    """Valid request with invalid email provided"""
    invalid_email = "@invalid?mail.cc"
    response = client.post(REQUEST_PASSWORD_RESET_ENDPOINT, data=json.dumps({"email": invalid_email}))
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert response.text == "Invalid email."


def test_request_password_reset_invalid_data_key(send_password_reset_mock, get_user_mock):
    """Valid request with malformed request body key"""
    email = "test@user.com"
    response = client.post(REQUEST_PASSWORD_RESET_ENDPOINT, data=json.dumps({"wrong_key_email": email}))
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_request_password_reset_requested_user_not_found(send_password_reset_mock, get_user_mock, mock_get_config_map):
    """Password request sent for non-existing user"""
    email = "test@user.com"
    get_user_mock.return_value = None
    response = client.post(REQUEST_PASSWORD_RESET_ENDPOINT, data=json.dumps({"email": email}))
    assert response.status_code == HTTPStatus.ACCEPTED
    assert response.text == "Password reset request sent"


def test_request_password_reset_smtp_server_not_configured(
    get_user_mock, send_password_reset_mock, mock_get_config_map
):
    email = "test@user.com"
    mock_get_config_map.side_effect = KeyError
    response = client.post(REQUEST_PASSWORD_RESET_ENDPOINT, data=json.dumps({"email": email}))
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_reset_password_bad_token(users_handler_instance_mock, update_password_mock, mock_get_secret):
    new_password = base64.b64encode("fakePassword".encode("ascii")).decode("ascii")
    token = "wrong_fake_token"
    user_id = "user@test.com"
    user_data = {
        "uid": user_id,
        "name": "test-user-name",
        "mail": user_id,
        "registered": True,
        "admin": False,
        "change_admin": False,
    }
    users_handler_instance_mock.verify_jwt_token.side_effect = BadTokenError
    update_password_mock.side_effect = ResponseException(
        code=GeneralError.WEAK_PASSWORD.name, item=user_data["uid"], msg=""
    )
    response = client.post(PASSWORD_RESET_ENDPOINT, data=json.dumps({"new_password": new_password, "token": token}))
    assert users_handler_instance_mock.verify_jwt_token.call_count == 1
    assert update_password_mock.call_count == 0
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.text == "Unauthorized"


def test_reset_password_invalid_input(users_handler_instance_mock, update_password_mock):
    new_password = base64.b64encode("insert evil".encode("ascii")).decode("ascii")
    token = "drop users"
    response = client.post(PASSWORD_RESET_ENDPOINT, data=json.dumps({"new_password": new_password, "token": token}))
    assert users_handler_instance_mock.verify_jwt_token.call_count == 0
    assert update_password_mock.call_count == 0
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.text == "Bad Request"


def test_reset_password_weak_new_password(users_handler_instance_mock, update_password_mock, mock_get_secret):
    new_password = base64.b64encode("fakePassword".encode("ascii")).decode("ascii")
    token = "fake_token"
    user_id = "user@test.com"
    user_data = {
        "uid": user_id,
        "name": "test-user-name",
        "mail": user_id,
        "registered": True,
        "admin": False,
        "change_admin": False,
    }
    users_handler_instance_mock.verify_jwt_token.return_value = user_data
    update_password_mock.side_effect = ResponseException(
        code=GeneralError.WEAK_PASSWORD.name, item=user_data["uid"], msg=""
    )
    response = client.post(PASSWORD_RESET_ENDPOINT, data=json.dumps({"new_password": new_password, "token": token}))
    assert users_handler_instance_mock.verify_jwt_token.call_count == 1
    assert update_password_mock.call_count == 1
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.text == "Specified password does not meet minimal requirements."


def test_reset_password_wrong_password_format():
    new_password = "fakePassword@123"
    token = "fake_token"
    response = client.post(PASSWORD_RESET_ENDPOINT, data=json.dumps({"new_password": new_password, "token": token}))
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.text == "Wrong password format"


def test_reset_password_correct_values(users_handler_instance_mock, update_password_mock, mock_get_secret):
    new_password = base64.b64encode("fakePassword@123".encode("ascii")).decode("ascii")
    token = "fake_token"
    response = client.post(PASSWORD_RESET_ENDPOINT, data=json.dumps({"new_password": new_password, "token": token}))
    assert users_handler_instance_mock.verify_jwt_token.call_count == 1
    assert update_password_mock.call_count == 1
    assert response.status_code == HTTPStatus.OK
    assert response.text == "Password was reset"
