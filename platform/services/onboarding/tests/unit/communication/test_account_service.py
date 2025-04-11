# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from unittest.mock import MagicMock, Mock

import pytest
from google.protobuf.timestamp_pb2 import Timestamp
from grpc import StatusCode
from grpc._channel import _InactiveRpcError, _RPCState
from grpc_interfaces.account_service.pb.organization_pb2 import OrganizationData

from models.organization import Organization
from models.statuses import Status
from models.user import User

from communication.account_service.account_service import OrganizationRepo, UserRepo


@pytest.fixture
def organization_repo():
    connection = MagicMock()
    mock_repo = OrganizationRepo(connection)
    Organization.repo = mock_repo
    yield mock_repo
    Organization.repo = None


@pytest.fixture
def user_repo():
    connection = MagicMock()
    mock_repo = UserRepo(connection)
    User.repo = mock_repo
    yield mock_repo
    User.repo = None


@pytest.mark.asyncio
async def test_get_organization(organization_repo: OrganizationRepo):
    get_by_id_mock = MagicMock(id="123", status=Status.REGISTERED, cell_id="abc")
    get_by_id_mock.name = "bla"
    organization_repo.acc_svc_client.organization_stub.get_by_id = Mock(return_value=get_by_id_mock)
    org = await organization_repo.get("123")

    assert org.id_ == "123"
    assert org.status == Status.REGISTERED
    assert org.cell_id == "abc"
    assert org.name == "bla"


@pytest.mark.asyncio
async def test_create_organization(organization_repo: OrganizationRepo):
    create_mock = OrganizationData(name="example", status=Status.REQUESTED, request_access_reason="test reason")
    organization_repo.acc_svc_client.organization_stub.create = Mock(return_value=create_mock)
    org = await organization_repo.create(
        organization_name="example", status=Status.REQUESTED, request_access_reason="test reason"
    )

    assert org.status == Status.REQUESTED
    assert org.name == "example"
    assert org.request_access_reason == "test reason"


@pytest.mark.asyncio
async def test_get_organization_failure(organization_repo: OrganizationRepo):
    organization_repo.acc_svc_client.organization_stub.get_by_id = Mock(
        return_value=MagicMock(id="123", status=Status.REGISTERED, cell_id="abc", name="bla")
    )
    organization_repo.acc_svc_client.organization_stub.get_by_id.side_effect = _InactiveRpcError(
        state=_RPCState(
            code=StatusCode.NOT_FOUND,
            details="error details",
            trailing_metadata=None,
            initial_metadata=None,
            due=[],
        )
    )
    org = await organization_repo.get("123")

    assert org is None


@pytest.mark.asyncio
async def test_update_organization(organization_repo: OrganizationRepo):
    current_timestamp = Timestamp()
    current_timestamp.GetCurrentTime()
    organization_repo.acc_svc_client.organization_stub.get_by_id = Mock(
        return_value=OrganizationData(
            id="123",
            status=Status.REGISTERED,
            cell_id="abc",
            name="bla",
            created_at=current_timestamp,
            modified_at=current_timestamp,
            country="PL",
            location="PL",
        )
    )
    organization_repo.acc_svc_client.organization_stub.modify = Mock()

    org = Organization(id_="123", status=Status.REGISTERED, cell_id="abc", name="bla")
    await organization_repo.update(org, modified_by="123")

    organization_repo.acc_svc_client.organization_stub.get_by_id.assert_called_once()
    organization_repo.acc_svc_client.organization_stub.modify.assert_called_once()


@pytest.mark.asyncio
async def test_get_user_by_email(user_repo: UserRepo):
    user_repo.acc_svc_client.user_stub.find = Mock(
        return_value=MagicMock(
            users=[
                MagicMock(id="0", first_name="Egg", second_name="Cheese", status="ACT", email="cheeseegg@spam.com"),
                MagicMock(id="1", first_name="Egg", second_name="Spam", status="ACT", email="egg@spam.com"),
                MagicMock(id="2", first_name="RawEgg", second_name="Spam", status="ACT", email="rawegg@spam.com"),
            ]
        )
    )
    user = await user_repo.get_user_by_email(email="egg@spam.com", organization_id="cheese")

    assert user.id_ == "1"
    assert user.first_name == "Egg"
    assert user.second_name == "Spam"
    assert user.status == "ACT"
    assert user.email == "egg@spam.com"


@pytest.mark.asyncio
async def test_get_user_by_email_strict_match(user_repo: UserRepo):
    user_repo.acc_svc_client.user_stub.find = Mock(
        return_value=MagicMock(
            users=[
                MagicMock(id="0", first_name="Egg", second_name="Cheese", status="ACT", email="egg@spam.com12"),
                MagicMock(id="2", first_name="RawEgg", second_name="Spam", status="ACT", email="rawegg@spam.com"),
            ]
        )
    )
    user = await user_repo.get_user_by_email(email="egg@spam.com", organization_id="cheese")

    assert user is None


@pytest.mark.asyncio
async def test_get_user_by_email_failure(user_repo: UserRepo):
    user_repo.acc_svc_client.user_stub.find = Mock(return_value=MagicMock(users=[]))
    user = await user_repo.get_user_by_email(email="egg@spam.com", organization_id="cheese")

    assert user is None


@pytest.mark.asyncio
async def test_update_user(user_repo: UserRepo):
    user_repo.acc_svc_client.user_stub.find = Mock(
        return_value=MagicMock(
            users=[
                MagicMock(
                    id="1",
                    first_name="Egg",
                    second_name="Spam",
                    status="ACT",
                    email="egg@spam.com",
                    organization_id="cheese",
                )
            ]
        )
    )
    user_repo.acc_svc_client.user_stub.modify = Mock()

    user = User(
        id_="1",
        first_name="Egg",
        second_name="Spam",
        status="ACT",
        email="egg@spam.com",
        organization_id="cheese",
    )
    await user_repo.update(user, modified_by="123")

    user_repo.acc_svc_client.user_stub.modify.assert_called_once()


@pytest.mark.asyncio
async def test_update_user_strict_match(user_repo: UserRepo):
    users = [
        User(
            id_="2",
            first_name="Egg2",
            second_name="Spam",
            status="ACT",
            email="egg@spam.com2",
            organization_id="cheese",
        ),
        User(
            id_="1",
            first_name="Egg",
            second_name="Spam",
            status="ACT",
            email="egg@spam.com",
            organization_id="cheese",
        ),
    ]
    user_repo.acc_svc_client.user_stub.find = Mock(return_value=MagicMock(users=users))
    user_repo.acc_svc_client.user_stub.modify = Mock()

    user = User(
        id_="1",
        first_name="Egg",
        second_name="Spam",
        status="REG",
        email="egg@spam.com",
        organization_id="cheese",
    )
    await user_repo.update(user, modified_by="123")

    user_repo.acc_svc_client.user_stub.modify.assert_called_once()
    assert users[0].status == "ACT"
    assert users[1].status == "REG"
