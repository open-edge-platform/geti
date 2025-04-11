# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from unittest.mock import MagicMock

import pytest

from models.statuses import Status
from models.user import User, UserRepoInterface


@pytest.fixture(autouse=True)
def mock_repo() -> UserRepoInterface:
    repo_mock = MagicMock(spec=UserRepoInterface)
    User.repo = repo_mock
    yield repo_mock
    User.repo = None


def test_is_registered():
    registered_user = User(
        id_="abcd", first_name="spam", second_name="egg", email="spam@egg.com", status=Status.REGISTERED
    )
    assert registered_user.is_registered() is True

    active_user = User(id_="abcd", first_name="spam", second_name="egg", email="spam@egg.com", status=Status.ACTIVE)
    assert active_user.is_registered() is False


@pytest.mark.asyncio
async def test_set_as_active(mock_repo: UserRepoInterface):
    registered_user = User(
        id_="abcd", first_name="spam", second_name="egg", email="spam@egg.com", status=Status.REGISTERED
    )
    await registered_user.set_as_active(modified_by="abcd")
    assert mock_repo.update.call_count == 1
    assert registered_user.status == Status.ACTIVE

    # Test idempotency
    await registered_user.set_as_active(modified_by="abcd")
    await registered_user.set_as_active(modified_by="abcd")
    assert mock_repo.update.call_count == 1


@pytest.mark.asyncio
async def test_set_as_registered(mock_repo: UserRepoInterface):
    active_user = User(id_="abcd", first_name="spam", second_name="egg", email="spam@egg.com", status=Status.ACTIVE)
    await active_user.set_as_registered(modified_by="abcd")
    assert mock_repo.update.call_count == 1
    assert active_user.status == Status.REGISTERED

    # Test idempotency
    await active_user.set_as_registered(modified_by="abcd")
    await active_user.set_as_registered(modified_by="abcd")
    assert mock_repo.update.call_count == 1


@pytest.mark.asyncio
async def test_get(mock_repo: UserRepoInterface):
    await User.get(id_="spam")
    assert mock_repo.get.call_count == 1


@pytest.mark.asyncio
async def test_update(mock_repo: UserRepoInterface):
    user = User(
        id_="abcd",
        first_name="spam",
        second_name="egg",
        email="spam@egg.com",
        status=Status.REGISTERED,
        organization_id="cheese",
    )
    user.first_name = "egg"
    await user.update(modified_by="abcd")
    assert mock_repo.update.call_count == 1
    assert user.first_name == "egg"
