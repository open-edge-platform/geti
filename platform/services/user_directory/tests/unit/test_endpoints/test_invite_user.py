# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from http import HTTPStatus

import grpc
import pytest
from endpoints.user_management.invite_user import InviteUserData, UserInvitationRequestREST, invite_user_endpoint
from grpc_interfaces.account_service.pb.user_common_pb2 import UserData

from common.account_service import AccountServiceError


@pytest.fixture
def mock_account_service(mocker):
    account_service_class_mock = mocker.patch("endpoints.user_management.invite_user.AccountServiceConnection")
    account_service_mock = mocker.MagicMock()
    account_service_class_mock.return_value = account_service_mock
    account_service_mock.create_user.return_value = UserData(id="7b197b69-d720-4457-afe5-6ef4a3cbb31d")
    return account_service_mock


@pytest.fixture
def mock_openldap(mocker):
    openldap_class_mock = mocker.patch("endpoints.user_management.invite_user.OpenLDAPConnection")
    openldap_mock = mocker.MagicMock()
    mocker.patch.object(openldap_mock.users_handler, "generate_jwt_token")
    openldap_class_mock.return_value = openldap_mock
    return openldap_mock


@pytest.fixture
def mock_invitation_message(mocker):
    mocker.patch("endpoints.user_management.invite_user.get_secrets")
    mocker.patch("endpoints.user_management.invite_user.get_config_map")
    mocker.patch(
        "endpoints.user_management.invite_user.SMTPClient._render_template", return_value=("fake-topic", "fake-message")
    )
    send_message_mock = mocker.patch("endpoints.user_management.invite_user.send_message")
    return send_message_mock


def test_invite_user_accsvc(mock_account_service, mock_openldap, mock_invitation_message):
    invite_user_body = UserInvitationRequestREST(
        user=InviteUserData(
            email="fake@email.com",
            firstName="first_name",
            secondName="second_name",
            organizationId="035964f9-e385-468a-b6a5-a6777c9baba0",
        ),
        roles=[],
    )
    invite_user_endpoint(invite_user_body, organization_id="035964f9-e385-468a-b6a5-a6777c9baba0")

    assert mock_account_service.create_user.call_count == 1
    assert mock_openldap.create_initial_user.call_count == 1
    assert mock_account_service.update_user_external_id.call_count == 1
    assert mock_invitation_message.call_count == 1


def test_invite_user_accsvc_accsvc_error(mock_account_service, mock_openldap, mock_invitation_message):
    mock_account_service.create_user.side_effect = AccountServiceError(
        message="fake error", grpc_status_code=grpc.StatusCode.INVALID_ARGUMENT
    )
    invite_user_body = UserInvitationRequestREST(
        user=InviteUserData(
            email="fake@email.com",
            firstName="first_name",
            secondName="second_name",
            organizationId="035964f9-e385-468a-b6a5-a6777c9baba0",
        ),
        roles=[],
    )
    response = invite_user_endpoint(invite_user_body, organization_id="035964f9-e385-468a-b6a5-a6777c9baba0")
    assert response.status_code == HTTPStatus.BAD_REQUEST

    assert mock_openldap.create_initial_user.call_count == 0
    assert mock_account_service.update_user_external_id.call_count == 0


def test_invite_user_accsvc_ldap_error(mock_account_service, mock_openldap, mock_invitation_message):
    fake_openldap_exception = RuntimeError("fake error")
    mock_openldap.create_initial_user.side_effect = fake_openldap_exception
    invite_user_body = UserInvitationRequestREST(
        user=InviteUserData(
            email="fake@email.com",
            firstName="first_name",
            secondName="second_name",
            organizationId="035964f9-e385-468a-b6a5-a6777c9baba0",
        ),
        roles=[],
    )
    with pytest.raises(type(fake_openldap_exception)):
        invite_user_endpoint(invite_user_body, organization_id="035964f9-e385-468a-b6a5-a6777c9baba0")

    assert mock_openldap.create_initial_user.call_count == 1
    assert mock_account_service.update_user_external_id.call_count == 0
    assert mock_account_service.delete_user.call_count == 1


def test_invite_user_accsvc_ldap_returned_false(mock_account_service, mock_openldap, mock_invitation_message):
    mock_openldap.create_initial_user.return_value = False
    invite_user_body = UserInvitationRequestREST(
        user=InviteUserData(
            email="fake@email.com",
            firstName="first_name",
            secondName="second_name",
            organizationId="035964f9-e385-468a-b6a5-a6777c9baba0",
        ),
        roles=[],
    )
    with pytest.raises(Exception):
        invite_user_endpoint(invite_user_body, organization_id="035964f9-e385-468a-b6a5-a6777c9baba0")

    assert mock_openldap.create_initial_user.call_count == 1
    assert mock_account_service.update_user_external_id.call_count == 0
    assert mock_account_service.delete_user.call_count == 1


def test_invite_user_accsvc_accsvc_update_external_id_error(
    mock_account_service, mock_openldap, mock_invitation_message
):
    mock_account_service.update_user_external_id.side_effect = AccountServiceError(
        message="fake error", grpc_status_code=grpc.StatusCode.INVALID_ARGUMENT
    )
    invite_user_body = UserInvitationRequestREST(
        user=InviteUserData(
            email="fake@email.com",
            firstName="first_name",
            secondName="second_name",
            organizationId="035964f9-e385-468a-b6a5-a6777c9baba0",
        ),
        roles=[],
    )
    with pytest.raises(AccountServiceError):
        invite_user_endpoint(invite_user_body, organization_id="035964f9-e385-468a-b6a5-a6777c9baba0")

    assert mock_account_service.create_user.call_count == 1
    assert mock_openldap.create_initial_user.call_count == 1

    assert mock_account_service.delete_user.call_count == 1
    assert mock_openldap.delete_user.call_count == 1
