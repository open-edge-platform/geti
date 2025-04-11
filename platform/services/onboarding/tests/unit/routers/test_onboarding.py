# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import os
from datetime import datetime
from http import HTTPStatus
from unittest.mock import MagicMock, patch

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException
from fastapi.testclient import TestClient
from google.protobuf.timestamp_pb2 import Timestamp
from grpc_interfaces.account_service.pb import user_common_pb2
from grpc_interfaces.account_service.pb.organization_pb2 import OrganizationData
from grpc_interfaces.account_service.pb.workspace_pb2 import WorkspaceData

from main import app
from models.account_service_model import ModelUpdateError
from models.organization import Organization, OrganizationRepoInterface
from models.statuses import Status
from models.user import User, UserRepoInterface
from models.workspace import Workspace, WorkspaceRepoInterface
from routers.onboarding import DEFAULT_PRODUCT_NAME, INTERNAL_PRODUCT_NAME

client = TestClient(app)


def _build_internal_jwt_token(is_internal: bool = False) -> str:
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    key = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )
    alg = "RS256"

    future_date = datetime(2050, 1, 1)

    external_token = jwt.encode(
        {
            "exp": future_date,
            "email": "spam@egg.com",
            "given_name": "spam",
            "family_name": "egg",
            "sub": "123456789",
            "isInternal": is_internal,
        },
        key,
        algorithm=alg,
    )

    internal_token = jwt.encode(
        {
            "exp": future_date,
            "external_token": external_token,
        },
        key,
        algorithm=alg,
    )

    return internal_token


@pytest.fixture(autouse=True)
def mock_user_repo() -> UserRepoInterface:
    mock_repo = MagicMock(spec=UserRepoInterface)
    User.repo = mock_repo
    yield mock_repo
    User.repo = None


@pytest.fixture(autouse=True)
def mock_workspace_repo() -> WorkspaceRepoInterface:
    mock_repo = MagicMock(spec=WorkspaceRepoInterface)
    Workspace.repo = mock_repo
    yield mock_repo
    Workspace.repo = None


@pytest.fixture(autouse=True)
def mock_organization_repo() -> OrganizationRepoInterface:
    mock_repo = MagicMock(spec=OrganizationRepoInterface)
    Organization.repo = mock_repo
    yield mock_repo
    Organization.repo = None


@pytest.fixture()
def set_env_var_key(monkeypatch):
    with patch.dict(os.environ, clear=True):
        envvars = {
            "KMS_KEY_ALIAS": "mock-hmac-key-alias",
        }
        for k, v in envvars.items():
            monkeypatch.setenv(k, v)
        yield


def test_user_onboarding(mock_user_repo: UserRepoInterface, mock_organization_repo: OrganizationRepoInterface, mocker):
    first_name = "spam"
    second_name = "egg"
    organization_id = "cheese"

    onboarded_user = User(
        id_="abcd", first_name=first_name, second_name=second_name, email="spam@egg.com", status=Status.REGISTERED
    )
    mock_user_repo.get_user_by_email.return_value = onboarded_user
    onboarded_org = Organization(id_=organization_id, cell_id="spam", status=Status.REGISTERED, name="bla")
    mock_organization_repo.get.return_value = onboarded_org
    cs_feature_flag_mock = mocker.patch("routers.onboarding.is_feature_flag_enabled")
    cs_feature_flag_mock.return_value = True
    create_subscription_mock = mocker.patch("routers.onboarding.create_subscription")

    request_body = {"organization_id": organization_id, "user_consent": "y", "telemetry_consent": "y"}

    response = client.post(
        "/onboarding/user",
        json=request_body,
        headers={
            "x-auth-request-access-token": _build_internal_jwt_token(),
        },
    )

    print(response)
    assert response.status_code == HTTPStatus.OK

    assert onboarded_user.status == Status.ACTIVE
    assert onboarded_user.first_name == first_name
    assert onboarded_user.second_name == second_name

    assert onboarded_org.status == Status.ACTIVE

    assert mock_user_repo.get_user_by_email.call_count == 1
    assert mock_user_repo.update.call_count == 1
    assert mock_organization_repo.get.call_count == 1
    assert mock_organization_repo.update.call_count == 1
    assert cs_feature_flag_mock.call_count == 1 and create_subscription_mock.call_count == 1


def test_user_onboarding_no_consent(
    mock_user_repo: UserRepoInterface, mock_organization_repo: OrganizationRepoInterface
):
    first_name = "spam"
    second_name = "egg"
    organization_id = "cheese"

    onboarded_user = User(
        id_="abcd", first_name=first_name, second_name=second_name, email="spam@egg.com", status=Status.REGISTERED
    )
    mock_user_repo.get_user_by_email.return_value = onboarded_user
    onboarded_org = Organization(id_=organization_id, cell_id="spam", status=Status.REGISTERED, name="bla")
    mock_organization_repo.get.return_value = onboarded_org

    request_body = {"organization_id": organization_id, "user_consent": "n", "telemetry_consent": "n"}

    response = client.post(
        "/onboarding/user",
        json=request_body,
        headers={
            "x-auth-request-access-token": _build_internal_jwt_token(),
        },
    )
    print(response)

    assert response.status_code == HTTPStatus.BAD_REQUEST

    assert onboarded_user.status == Status.REGISTERED
    assert onboarded_user.first_name == first_name
    assert onboarded_user.second_name == second_name

    assert onboarded_org.status == Status.REGISTERED

    assert mock_user_repo.get_user_by_email.call_count == 0
    assert mock_user_repo.update.call_count == 0
    assert mock_organization_repo.get.call_count == 0
    assert mock_organization_repo.update.call_count == 0


@pytest.mark.parametrize(
    "user_status,organization_status",
    [(Status.ACTIVE, Status.ACTIVE), (Status.ACTIVE, Status.REGISTERED)],
)
def test_user_onboarding_not_registered(
    mock_user_repo: UserRepoInterface,
    mock_organization_repo: OrganizationRepoInterface,
    user_status: Status,
    organization_status: Status,
):
    organization_id = "cheese"

    onboarded_user = User(id_="abcd", first_name="spam", second_name="egg", email="spam@egg.com", status=user_status)
    mock_user_repo.get_user_by_email.return_value = onboarded_user
    onboarded_org = Organization(id_=organization_id, cell_id="spam", status=organization_status, name="bla")
    mock_organization_repo.get.return_value = onboarded_org

    request_body = {"organization_id": organization_id, "user_consent": "y", "telemetry_consent": "y"}

    response = client.post(
        "/onboarding/user",
        json=request_body,
        headers={
            "x-auth-request-access-token": _build_internal_jwt_token(),
        },
    )

    assert response.status_code == HTTPStatus.NOT_FOUND

    assert onboarded_user.status == user_status
    assert onboarded_org.status == organization_status

    assert mock_user_repo.get_user_by_email.call_count == 1
    assert mock_user_repo.update.call_count == 0
    assert mock_organization_repo.get.call_count == 0
    assert mock_organization_repo.update.call_count == 0


@pytest.mark.parametrize(
    "update_user_side_effect,update_org_side_effect",
    [(None, ModelUpdateError), (ModelUpdateError, None), (ModelUpdateError, ModelUpdateError)],
)
def test_user_onboarding_rollback(
    mock_user_repo: UserRepoInterface,
    mock_organization_repo: OrganizationRepoInterface,
    update_user_side_effect,
    update_org_side_effect,
    mocker,
):
    organization_id = "cheese"

    onboarded_user = User(
        id_="abcd", first_name="spam", second_name="egg", email="spam@egg.com", status=Status.REGISTERED
    )
    mock_user_repo.get_user_by_email.return_value = onboarded_user
    onboarded_org = Organization(id_=organization_id, cell_id="spam", status=Status.REGISTERED, name="bla")
    mock_organization_repo.get.return_value = onboarded_org
    cs_feature_flag_mock = mocker.patch("routers.onboarding.is_feature_flag_enabled")
    cs_feature_flag_mock.return_value = True
    create_subscription_mock = mocker.patch("routers.onboarding.create_subscription")
    fail_subscription_mock = mocker.patch("routers.onboarding.fail_subscription")

    mock_organization_repo.update.side_effect = update_org_side_effect
    mock_user_repo.update.side_effect = update_user_side_effect

    request_body = {"organization_id": organization_id, "user_consent": "y", "telemetry_consent": "y"}

    with pytest.raises(ModelUpdateError):
        response = client.post(
            "/onboarding/user",
            json=request_body,
            headers={
                "x-auth-request-access-token": _build_internal_jwt_token(),
            },
        )
        print(response)

    assert onboarded_user.status == Status.REGISTERED
    assert onboarded_org.status == Status.REGISTERED

    assert mock_user_repo.get_user_by_email.call_count == 1
    assert mock_user_repo.update.call_count == (0 if update_org_side_effect is not None else 2)
    assert mock_organization_repo.get.call_count == 1
    assert cs_feature_flag_mock.call_count == (0 if update_org_side_effect is not None else 2)
    assert create_subscription_mock.call_count == (0 if update_org_side_effect is not None else 1)
    assert fail_subscription_mock.call_count == (0 if update_org_side_effect is not None else 1)
    assert mock_organization_repo.update.call_count == 2


@pytest.mark.parametrize(
    "is_internal_user, require_invitation_link, product_name",
    [
        (True, True, INTERNAL_PRODUCT_NAME),
        (False, True, DEFAULT_PRODUCT_NAME),
        (True, False, INTERNAL_PRODUCT_NAME),
        (False, False, DEFAULT_PRODUCT_NAME),
    ],
)
def test_user_onboarding_create_user_and_org(
    mock_user_repo: UserRepoInterface,
    mock_organization_repo: OrganizationRepoInterface,
    mock_workspace_repo: WorkspaceRepoInterface,
    set_env_var_key,
    mocker,
    is_internal_user,
    require_invitation_link,
    product_name,
):
    def feature_flag_mock_function(flag_name) -> bool:
        if flag_name == "FEATURE_FLAG_FREE_TIER":
            return True
        if flag_name == "FEATURE_FLAG_CREDIT_SYSTEM":
            return True
        if flag_name == "FEATURE_FLAG_SAAS_REQUIRE_INVITATION_LINK":
            return require_invitation_link
        if flag_name == "FEATURE_FLAG_REQ_ACCESS":
            return False
        raise ValueError(f"Unexpected flag name: {flag_name}")

    mock_user_repo.get_user_profile.return_value = None
    ft_feature_flag_mock = mocker.patch("routers.onboarding.is_feature_flag_enabled")
    ft_feature_flag_mock.side_effect = feature_flag_mock_function
    create_subscription_mock = mocker.patch("routers.onboarding.create_subscription")
    user = user_common_pb2.UserData(id="542fa-daw24")
    current_timestamp = Timestamp()
    current_timestamp.GetCurrentTime()
    onboarded_org = OrganizationData(
        id="30ffc4ef-5d73",
        name="custom",
        status="ACT",
        country="PL",
        location="PL",
        cell_id="000",
        created_at=current_timestamp,
        modified_at=current_timestamp,
    )
    workspace = WorkspaceData(id=onboarded_org.id, name="random")
    mock_organization_repo.create.return_value = onboarded_org
    mock_workspace_repo.create.return_value = workspace
    mock_user_repo.create.return_value = user
    onboard_token_validation_mock = mocker.patch("routers.onboarding.OnboardingTokenService.validate_onboarding_token")

    onboarding_token = "token_mock_value"
    request_body = {
        "organization_id": "",
        "organization_name": "custom",
        "user_consent": "y",
        "telemetry_consent": "y",
        "onboarding_token": onboarding_token,
    }

    response = client.post(
        "/onboarding/user",
        json=request_body,
        headers={
            "x-auth-request-access-token": _build_internal_jwt_token(is_internal=is_internal_user),
        },
    )

    assert response.status_code == HTTPStatus.OK

    assert onboarded_org.status == Status.ACTIVE

    assert mock_user_repo.get_user_profile.call_count == 1
    assert mock_user_repo.create.call_count == 1
    assert mock_organization_repo.create.call_count == 1
    assert mock_workspace_repo.create.call_count == 1
    create_subscription_mock.assert_called_once_with(
        organization_id=onboarded_org.id, workspace_id=workspace.id, product_name=product_name
    )
    if require_invitation_link and not is_internal_user:
        onboard_token_validation_mock.assert_called_once_with(token=onboarding_token)
    else:
        onboard_token_validation_mock.assert_not_called()


def test_user_onboarding_fail_create_user(
    mock_user_repo: UserRepoInterface,
    mock_organization_repo: OrganizationRepoInterface,
    mock_workspace_repo: WorkspaceRepoInterface,
    set_env_var_key,
    mocker,
):
    mock_user_repo.get_user_profile.return_value = None
    ft_feature_flag_mock = mocker.patch("routers.onboarding.is_feature_flag_enabled")
    ft_feature_flag_mock.return_value = True
    onboard_token_validation_mock = mocker.patch("routers.onboarding.OnboardingTokenService.validate_onboarding_token")
    onboarding_token = "token_mock_value"
    create_subscription_mock = mocker.patch("routers.onboarding.create_subscription")

    request_body = {
        "organization_id": "",
        "organization_name": "custom",
        "user_consent": "y",
        "telemetry_consent": "y",
        "onboarding_token": onboarding_token,
    }
    response = client.post(
        "/onboarding/user",
        json=request_body,
        headers={
            "x-auth-request-access-token": _build_internal_jwt_token(),
        },
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST

    assert mock_user_repo.get_user_profile.call_count == 1
    assert mock_user_repo.create.call_count == 0
    assert mock_organization_repo.create.call_count == 1
    assert mock_workspace_repo.create.call_count == 1
    onboard_token_validation_mock.assert_called_once_with(token=onboarding_token)
    create_subscription_mock.assert_not_called()


def test_invalid_onboarding_token(
    mock_user_repo: UserRepoInterface,
    mock_organization_repo: OrganizationRepoInterface,
    mock_workspace_repo: WorkspaceRepoInterface,
    set_env_var_key,
    mocker,
):
    mock_user_repo.get_user_profile.return_value = None
    ft_feature_flag_mock = mocker.patch("routers.onboarding.is_feature_flag_enabled")
    ft_feature_flag_mock.return_value = True
    onboard_token_validation_mock = mocker.patch("routers.onboarding.OnboardingTokenService.validate_onboarding_token")
    onboard_token_validation_mock.side_effect = HTTPException(status_code=HTTPStatus.UNAUTHORIZED)
    onboarding_token = "token_mock_value"
    create_subscription_mock = mocker.patch("routers.onboarding.create_subscription")

    request_body = {
        "organization_id": "",
        "organization_name": "custom",
        "user_consent": "y",
        "telemetry_consent": "y",
        "onboarding_token": onboarding_token,
    }
    response = client.post(
        "/onboarding/user",
        json=request_body,
        headers={
            "x-auth-request-access-token": _build_internal_jwt_token(),
        },
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert mock_user_repo.get_user_profile.call_count == 1
    assert mock_user_repo.create.call_count == 0
    assert mock_organization_repo.create.call_count == 0
    assert mock_workspace_repo.create.call_count == 0
    onboard_token_validation_mock.assert_called_once_with(token=onboarding_token)
    create_subscription_mock.assert_not_called()


def test_user_onboarding_without_free_tier(
    mock_user_repo: UserRepoInterface,
    mock_organization_repo: OrganizationRepoInterface,
    mock_workspace_repo: WorkspaceRepoInterface,
    mocker,
):
    mock_user_repo.get_user_profile.return_value = None
    ft_feature_flag_mock = mocker.patch("routers.onboarding.is_feature_flag_enabled")
    ft_feature_flag_mock.return_value = False
    register_user_in_marketing_platform_mock = mocker.patch("routers.onboarding.register_user_in_marketing_platform")

    request_body = {"organization_id": "", "organization_name": "custom", "user_consent": "y", "telemetry_consent": "y"}
    response = client.post(
        "/onboarding/user",
        json=request_body,
        headers={
            "x-auth-request-access-token": _build_internal_jwt_token(),
        },
    )

    assert response.status_code == HTTPStatus.OK

    assert mock_user_repo.get_user_profile.call_count == 1
    assert mock_organization_repo.get.call_count == 1
    assert mock_user_repo.create.call_count == 0
    assert mock_user_repo.update.call_count == 0
    assert mock_organization_repo.update.call_count == 0
    assert register_user_in_marketing_platform_mock.call_count == 1


def test_user_onboarding_requested(
    mock_user_repo: UserRepoInterface,
    mock_organization_repo: OrganizationRepoInterface,
    mock_workspace_repo: WorkspaceRepoInterface,
    mocker,
):
    feature_flag_mock = mocker.patch("routers.onboarding.is_feature_flag_enabled")
    feature_flag_mock.return_value = True

    mock_user_repo.get_user_profile.return_value = None
    mock_workspace = MagicMock()
    mock_workspace.id = "mock_workspace_id"

    mock_user_repo.create.return_value = user_common_pb2.UserData(id="new_user_id")
    mock_organization_repo.create.return_value = OrganizationData(id="new_org_id", name="new_org")
    mock_workspace_repo.create.return_value = mock_workspace

    mock_subscription = mocker.patch("routers.onboarding.create_subscription")

    request_body = {
        "organization_id": "",
        "organization_name": "new_org",
        "user_consent": "y",
        "telemetry_consent": "y",
    }
    response = client.post(
        "/onboarding/user",
        json=request_body,
        headers={
            "x-auth-request-access-token": _build_internal_jwt_token(),
        },
    )

    assert response.status_code == HTTPStatus.OK
    assert mock_user_repo.create.call_count == 1
    assert mock_organization_repo.create.call_count == 1
    assert feature_flag_mock.call_count == 2
    assert mock_subscription.call_count == 1
