# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import base64
from unittest.mock import Mock

import pytest as pytest
from endpoints.user_management.activate_user import ActivateData, activate
from endpoints.user_management.router import users_router
from fastapi import FastAPI
from fastapi.testclient import TestClient
from grpc_interfaces.account_service.pb.user_common_pb2 import UserData

from users_handler.users_handler import UserHandlerError, UsersHandler, WeakPassword

from common.errors import BadTokenError

app = FastAPI()
app.include_router(users_router)
client = TestClient(app)

X_AUTH_REQUEST_ACCESS_TOKEN = "foo_bar_baz"
OAUTH2_PROXY_COOKIE_VALUE = "oauth cookie value"


@pytest.fixture
def mock_account_service(mocker):
    account_service_class_mock = mocker.patch("endpoints.user_management.activate_user.AccountServiceConnection")
    account_service_mock = mocker.MagicMock()
    account_service_class_mock.return_value = account_service_mock
    account_service_mock.client.user_stub = Mock()
    account_service_mock.client.user_stub.find.return_value.users = [UserData(email="sample@mail.com")]
    account_service_mock.get_organization.return_value.organizations[0].id = "00-22-33"
    return account_service_mock


@pytest.fixture
def mock_users_handler(mocker):
    users_handler_mock = mocker.MagicMock(spec=UsersHandler)
    users_handler_mock.get_password.return_value = base64.b64encode("SampleP@ssw0rd".encode("ascii")).decode("ascii")
    users_handler_mock.change_user_password.return_value = True
    return mocker.patch(
        "endpoints.user_management.activate_user.UsersHandler", return_value=users_handler_mock
    ).return_value


@pytest.mark.asyncio
async def test_get_users_active(mock_account_service, mock_users_handler, mocker):
    mocker.patch("endpoints.user_management.activate_user.verify_payload").return_value = {
        "mail": "sample@mail.com",
        "uid": "00-22-33",
    }
    activate_user_body = ActivateData(
        first_name="Test",
        second_name="Test",
        password=base64.b64encode("SampleP@ssw0rd".encode("ascii")).decode("ascii"),
        token="sample_jwt",
    )

    response = await activate(activate_user_body)
    assert response.status_code == 200

    assert mock_account_service.client.user_stub.find.call_count == 1
    assert mock_account_service.client.user_stub.modify.call_count == 1
    assert mock_users_handler.change_user_password.call_count == 1
    assert mock_users_handler.edit_user.call_count == 1


@pytest.mark.asyncio
async def test_get_users_active_jwt_error(mock_account_service, mock_users_handler, mocker):
    mocker.patch("endpoints.user_management.activate_user.verify_payload").side_effect = BadTokenError()
    activate_user_body = ActivateData(
        first_name="test",
        second_name="test",
        password=base64.b64encode("SampleP@ssw0rd".encode("ascii")).decode("ascii"),
        token="sample_jwt",
    )

    response = await activate(activate_user_body)
    assert response.status_code == 401

    assert mock_account_service.client.user_stub.find.call_count == 0
    assert mock_account_service.client.user_stub.modify.call_count == 0
    assert mock_users_handler.change_user_password.call_count == 0
    assert mock_users_handler.edit_user.call_count == 0


@pytest.mark.asyncio
async def test_get_users_active_error_and_rollback(mock_account_service, mock_users_handler, mocker):
    mocker.patch("endpoints.user_management.activate_user.verify_payload").return_value = {
        "mail": "sample@mail.com",
        "uid": "00-22-33",
    }
    mock_users_handler.change_user_password.side_effect = UserHandlerError
    activate_user_body = ActivateData(
        first_name="test",
        second_name="test",
        password=base64.b64encode("SampleP@ssw0rd".encode("ascii")).decode("ascii"),
        token="sample_jwt",
    )

    with pytest.raises(UserHandlerError):
        await activate(activate_user_body)

    assert mock_account_service.client.user_stub.find.call_count == 1
    assert mock_account_service.client.user_stub.modify.call_count == 2


@pytest.mark.asyncio
async def test_get_users_active_password_error(mock_account_service, mock_users_handler, mocker):
    mocker.patch("endpoints.user_management.activate_user.verify_payload").return_value = {
        "mail": "sample@mail.com",
        "uid": "00-22-33",
    }
    mock_users_handler.check_password_strength.side_effect = WeakPassword
    activate_user_body = ActivateData(
        first_name="test",
        second_name="test",
        password=base64.b64encode("WeakPassword".encode("ascii")).decode("ascii"),
        token="sample_jwt",
    )

    await activate(activate_user_body)

    assert mock_account_service.client.user_stub.find.call_count == 0
    assert mock_account_service.client.user_stub.modify.call_count == 0
    assert mock_users_handler.change_user_password.call_count == 0
    assert mock_users_handler.edit_user.call_count == 0


@pytest.mark.asyncio
async def test_get_users_active_user_not_found_in_acc(mock_account_service, mock_users_handler, mocker):
    mocker.patch("endpoints.user_management.activate_user.verify_payload").return_value = {
        "mail": "sample@mail.com",
        "uid": "00-22-33",
    }
    mock_account_service.client.user_stub.find.return_value = UserData()
    activate_user_body = ActivateData(
        first_name="test",
        second_name="test",
        password=base64.b64encode("SampleP@ssw0rd".encode("ascii")).decode("ascii"),
        token="sample_jwt",
    )

    response = await activate(activate_user_body)
    assert response.status_code == 500

    assert mock_account_service.client.user_stub.find.call_count == 1
    assert mock_account_service.client.user_stub.modify.call_count == 0
    assert mock_users_handler.change_user_password.call_count == 0
    assert mock_users_handler.edit_user.call_count == 0


@pytest.mark.asyncio
async def test_get_users_active_too_long_input(mock_account_service, mock_users_handler, mocker):
    mocker.patch("endpoints.user_management.activate_user.verify_payload").return_value = {
        "mail": "sample@mail.com",
        "uid": "00-22-33",
    }
    activate_user_body = ActivateData(
        first_name="testwithinputlenghtover200characters_Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.",
        second_name="test",
        password=base64.b64encode("WeakPassword".encode("ascii")).decode("ascii"),
        token="sample_jwt",
    )

    response = await activate(activate_user_body)
    assert response.status_code == 400

    assert mock_account_service.client.user_stub.find.call_count == 0
    assert mock_account_service.client.user_stub.modify.call_count == 0
    assert mock_users_handler.change_user_password.call_count == 0
    assert mock_users_handler.edit_user.call_count == 0


@pytest.mark.asyncio
async def test_get_users_active_user_no_mail_from_jwt(mock_account_service, mock_users_handler, mocker):
    mocker.patch("endpoints.user_management.activate_user.verify_payload").return_value = {
        "mail": "",
        "uid": "00-22-33",
    }
    activate_user_body = ActivateData(
        first_name="test",
        second_name="test",
        password=base64.b64encode("SampleP@ssw0rd".encode("ascii")).decode("ascii"),
        token="sample_jwt",
    )

    response = await activate(activate_user_body)
    assert response.status_code == 404

    assert mock_account_service.client.user_stub.find.call_count == 0
    assert mock_account_service.client.user_stub.modify.call_count == 0
    assert mock_users_handler.change_user_password.call_count == 0
    assert mock_users_handler.edit_user.call_count == 0


@pytest.mark.asyncio
async def test_get_users_active_user_bad_token(mock_account_service, mock_users_handler, mocker):
    mocker.patch("endpoints.user_management.activate_user.verify_payload").side_effect = BadTokenError
    activate_user_body = ActivateData(
        first_name="test",
        second_name="test",
        password=base64.b64encode("SampleP@ssw0rd".encode("ascii")).decode("ascii"),
        token="sample_jwt",
    )

    response = await activate(activate_user_body)
    assert response.status_code == 401

    assert mock_account_service.client.user_stub.find.call_count == 0
    assert mock_account_service.client.user_stub.modify.call_count == 0
    assert mock_users_handler.change_user_password.call_count == 0
    assert mock_users_handler.edit_user.call_count == 0
