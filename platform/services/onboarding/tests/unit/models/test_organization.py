# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from unittest.mock import MagicMock

import pytest

from models.organization import Organization, OrganizationRepoInterface
from models.statuses import Status


@pytest.fixture(autouse=True)
def mock_repo() -> OrganizationRepoInterface:
    repo_mock = MagicMock(spec=OrganizationRepoInterface)
    Organization.repo = repo_mock
    yield repo_mock
    Organization.repo = None


def test_is_registered():
    registered_org = Organization(id_="spam", status=Status.REGISTERED, cell_id="egg", name="bla")
    assert registered_org.is_registered() is True

    active_org = Organization(id_="spam", status=Status.ACTIVE, cell_id="egg", name="bla")
    assert active_org.is_registered() is False


@pytest.mark.asyncio
async def test_set_as_active(mock_repo: OrganizationRepoInterface):
    registered_org = Organization(id_="spam", status=Status.REGISTERED, cell_id="egg", name="bla")
    await registered_org.set_as_active(modified_by="abcd")
    assert mock_repo.update.call_count == 1
    assert registered_org.status == Status.ACTIVE

    # Test idempotency
    await registered_org.set_as_active(modified_by="abcd")
    await registered_org.set_as_active(modified_by="abcd")
    assert mock_repo.update.call_count == 1


@pytest.mark.asyncio
async def test_set_as_registered(mock_repo: OrganizationRepoInterface):
    active_org = Organization(id_="spam", status=Status.ACTIVE, cell_id="egg", name="bla")
    await active_org.set_as_registered(modified_by="abcd")
    assert mock_repo.update.call_count == 1
    assert active_org.status == Status.REGISTERED

    # Test idempotency
    await active_org.set_as_registered(modified_by="abcd")
    await active_org.set_as_registered(modified_by="abcd")
    assert mock_repo.update.call_count == 1


@pytest.mark.asyncio
async def test_get(mock_repo: OrganizationRepoInterface):
    await Organization.get(id_="spam")
    assert mock_repo.get.call_count == 1


@pytest.mark.asyncio
async def test_update(mock_repo: OrganizationRepoInterface):
    org = Organization(id_="spam", status=Status.REGISTERED, cell_id="egg", name="bla")
    org.id_ = "egg"
    await org.update(modified_by="abcd")
    assert mock_repo.update.call_count == 1
    assert org.id_ == "egg"


@pytest.mark.asyncio
async def test_create(mock_repo: OrganizationRepoInterface):
    await Organization.create(organization_name="test", status="REQ", request_access_reason="test reason")
    assert mock_repo.create.call_count == 1
