# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import base64
from http import HTTPStatus

import pytest
from endpoints.user_management.router import users_router
from fastapi import FastAPI
from fastapi.testclient import TestClient

from users_handler.exceptions import UserDoesNotExist

from common.errors import GeneralError
from common.interfaces.payload_error import ResponseException
from common.utils import API_BASE_PATTERN

UPDATE_PASSWD_ENDPOINT = f"{API_BASE_PATTERN}/users/{{user_id}}/update_password"

app = FastAPI()
app.include_router(users_router)
client = TestClient(app)


@pytest.fixture
def get_user_from_header_mock(mocker):
    return mocker.patch("endpoints.user_management.update_password.get_user_from_header")


@pytest.fixture
def update_password_mock(mocker):
    return mocker.patch("endpoints.user_management.update_password.update_password")


def test_update_password_same_passwords(get_user_from_header_mock, update_password_mock):
    old_password = base64.b64encode("fakePassword@123".encode("ascii")).decode("ascii")
    new_password = base64.b64encode("fakePassword@123".encode("ascii")).decode("ascii")
    user_id = "user@test.com"
    header_key = "x-auth-request-access-token"
    active_user_data = {
        "uid": user_id,
        "name": "test-user-name",
        "mail": user_id,
        "registered": True,
        "admin": False,
        "change_admin": False,
    }
    get_user_from_header_mock.return_value = active_user_data
    update_password_mock.side_effect = ResponseException(code=GeneralError.SAME_NEW_PASSWORD.name, item=user_id, msg="")
    response = client.post(
        UPDATE_PASSWD_ENDPOINT.format(user_id=user_id),
        json={"old_password": old_password, "new_password": new_password},
        headers={header_key: user_id},
    )
    assert update_password_mock.call_count == 1
    assert get_user_from_header_mock.call_count == 1
    assert response.status_code == HTTPStatus.CONFLICT
    assert response.text == "Password should be different from your old password."


def test_update_password_wrong_password_format():
    old_password = "fakePassword@123"
    new_password = base64.b64encode("new_fakePassword@123".encode("ascii")).decode("ascii")
    user_id = "user@test.com"
    response = client.post(
        UPDATE_PASSWD_ENDPOINT.format(user_id=user_id),
        json={"old_password": old_password, "new_password": new_password},
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.text == "Wrong password format"


def test_update_password_weak_new_password(get_user_from_header_mock, update_password_mock):
    old_password = base64.b64encode("fakePassword@123".encode("ascii")).decode("ascii")
    new_password = base64.b64encode("new_password".encode("ascii")).decode("ascii")
    user_id = "user@test.com"
    header_key = "x-auth-request-access-token"
    active_user_data = {
        "uid": user_id,
        "name": "test-user-name",
        "mail": user_id,
        "registered": True,
        "admin": False,
        "change_admin": False,
    }
    get_user_from_header_mock.return_value = active_user_data
    update_password_mock.side_effect = ResponseException(code=GeneralError.WEAK_PASSWORD.name, item=user_id, msg="")
    response = client.post(
        UPDATE_PASSWD_ENDPOINT.format(user_id=user_id),
        json={"old_password": old_password, "new_password": new_password},
        headers={header_key: user_id},
    )
    assert update_password_mock.call_count == 1
    assert get_user_from_header_mock.call_count == 1
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.text == "Specified password does not meet minimal requirements."


def test_update_password_invalid_input(get_user_from_header_mock, update_password_mock):
    old_password = base64.b64encode("fakePassword@123".encode("ascii")).decode("ascii")
    new_password = base64.b64encode("delete users".encode("ascii")).decode("ascii")
    user_id = "drop users"
    header_key = "x-auth-request-access-token"
    response = client.post(
        UPDATE_PASSWD_ENDPOINT.format(user_id=user_id),
        json={"old_password": old_password, "new_password": new_password},
        headers={header_key: user_id},
    )
    assert update_password_mock.call_count == 0
    assert get_user_from_header_mock.call_count == 0
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.text == "Not allowed string"


def test_update_password_wrong_old_password(get_user_from_header_mock, update_password_mock):
    old_password = base64.b64encode("wrongFakePassword@123".encode("ascii")).decode("ascii")
    new_password = base64.b64encode("new_fakePassword@123".encode("ascii")).decode("ascii")
    user_id = "user@test.com"
    header_key = "x-auth-request-access-token"
    active_user_data = {
        "uid": user_id,
        "name": "test-user-name",
        "mail": user_id,
        "registered": True,
        "admin": False,
        "change_admin": False,
    }
    get_user_from_header_mock.return_value = active_user_data
    update_password_mock.side_effect = ResponseException(
        code=GeneralError.WRONG_OLD_PASSWORD.name, item=user_id, msg=""
    )
    response = client.post(
        UPDATE_PASSWD_ENDPOINT.format(user_id=user_id),
        json={"old_password": old_password, "new_password": new_password},
        headers={header_key: user_id},
    )
    assert update_password_mock.call_count == 1
    assert get_user_from_header_mock.call_count == 1
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.text == "That’s an incorrect password. Try again."


def test_update_password_non_existing_user_id(get_user_from_header_mock, update_password_mock):
    old_password = base64.b64encode("fakePassword@123".encode("ascii")).decode("ascii")
    new_password = base64.b64encode("new_fakePassword@123".encode("ascii")).decode("ascii")
    user_id = "user@test.com"
    header_key = "x-auth-request-access-token"
    get_user_from_header_mock.side_effect = UserDoesNotExist
    response = client.post(
        UPDATE_PASSWD_ENDPOINT.format(user_id=user_id),
        json={"old_password": old_password, "new_password": new_password},
        headers={header_key: user_id},
    )
    assert get_user_from_header_mock.call_count == 1
    assert update_password_mock.call_count == 0
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.text == "User doesn't exist."


def test_update_password_no_auth_header(get_user_from_header_mock, update_password_mock):
    old_password = base64.b64encode("fakePassword@123".encode("ascii")).decode("ascii")
    new_password = base64.b64encode("new_fakePassword@123".encode("ascii")).decode("ascii")
    user_id = "user@test.com"
    response = client.post(
        UPDATE_PASSWD_ENDPOINT.format(user_id=user_id),
        json={"old_password": old_password, "new_password": new_password},
    )
    assert update_password_mock.call_count == 0
    assert get_user_from_header_mock.call_count == 1
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.text == "Unauthorized"


def test_update_password_wrong_user_logged_in(get_user_from_header_mock, update_password_mock):
    old_password = base64.b64encode("fakePassword@123".encode("ascii")).decode("ascii")
    new_password = base64.b64encode("new_fakePassword@123".encode("ascii")).decode("ascii")
    user_id = "user@test.com"
    header_key = "x-auth-request-access-token"
    get_user_from_header_mock.side_effect = UserDoesNotExist
    response = client.post(
        UPDATE_PASSWD_ENDPOINT.format(user_id=user_id),
        json={"old_password": old_password, "new_password": new_password},
        headers={header_key: "different_user@test.com"},
    )
    assert update_password_mock.call_count == 0
    assert get_user_from_header_mock.call_count == 1
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.text == "User doesn't exist."


def test_update_password_correctly(get_user_from_header_mock, update_password_mock):
    old_password = base64.b64encode("fakePassword@123".encode("ascii")).decode("ascii")
    new_password = base64.b64encode("new_fakePassword@123".encode("ascii")).decode("ascii")
    user_id = "user@test.com"
    header_key = "x-auth-request-access-token"
    active_user_data = {
        "uid": user_id,
        "name": "test-user-name",
        "mail": user_id,
        "registered": True,
        "admin": False,
        "change_admin": False,
    }
    get_user_from_header_mock.return_value = active_user_data
    response = client.post(
        UPDATE_PASSWD_ENDPOINT.format(user_id=user_id),
        json={"old_password": old_password, "new_password": new_password},
        headers={header_key: user_id},
    )
    assert update_password_mock.call_count == 1
    assert get_user_from_header_mock.call_count == 1
    assert response.status_code == HTTPStatus.OK
    assert response.text == "Password has been updated"
