# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from unittest.mock import MagicMock, patch

import pytest
from fastapi import status

from db.model.subscription import Subscription
from dependencies import get_session
from exceptions.custom_exception_handler import custom_exception_handler
from main import app
from rest.schema.common import NextPage


def patched_session():
    return MagicMock()


@pytest.fixture
def mock_credit_account_get():
    with patch("rest.endpoints.credit_accounts.get.CreditAccountService") as mock_account_service:
        yield mock_account_service


@pytest.fixture
def mock_subscription_svc():
    with patch("rest.endpoints.credit_accounts.get.SubscriptionService") as mock_subscription_svc:
        yield mock_subscription_svc


@pytest.mark.parametrize("has_accounts", [True, False])
def test_success(mock_credit_account_get, mock_subscription_svc, client, organization_id, credit_account, has_accounts):
    skip = 0
    limit = 10
    accounts = []
    if has_accounts:
        accounts.append(credit_account)
    endpoint = f"/api/v1/organizations/{organization_id}/credit_accounts"
    app.dependency_overrides[get_session] = patched_session  # type: ignore

    subscription_service_mock = MagicMock()
    subscription = Subscription(organization_id=organization_id)
    subscription_service_mock.get_active_subscription.return_value = subscription
    mock_subscription_svc.return_value = subscription_service_mock

    credit_account_service = MagicMock()
    credit_account_service.get_organization_accounts.return_value = (len(accounts), accounts)
    mock_credit_account_get.return_value = credit_account_service

    response = client.get(endpoint, params={"skip": skip, "limit": limit})

    credit_account_service.get_organization_accounts.assert_called_once_with(
        subscription=subscription,
        skip=skip,
        limit=limit,
    )
    mock_subscription_svc.assert_called_once()
    mock_credit_account_get.assert_called_once()
    assert response.status_code == status.HTTP_200_OK


def test_no_subscription(mock_credit_account_get, mock_subscription_svc, client, organization_id):
    skip = 0
    limit = 10
    endpoint = f"/api/v1/organizations/{organization_id}/credit_accounts"
    app.dependency_overrides[get_session] = patched_session  # type: ignore

    subscription_service_mock = MagicMock()
    subscription_service_mock.get_active_subscription.return_value = None
    mock_subscription_svc.return_value = subscription_service_mock

    credit_account_service = MagicMock()
    mock_credit_account_get.return_value = credit_account_service

    response = client.get(endpoint, params={"skip": skip, "limit": limit})

    mock_subscription_svc.assert_called_once()
    mock_credit_account_get.assert_not_called()
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_failure(mock_credit_account_get, mock_subscription_svc, client, organization_id):
    endpoint = f"/api/v1/organizations/{organization_id}/credit_accounts"
    app.dependency_overrides[get_session] = patched_session  # type: ignore
    app.add_exception_handler(Exception, custom_exception_handler)

    subscription_service_mock = MagicMock()
    subscription = Subscription(organization_id=organization_id)
    subscription_service_mock.get_active_subscription.return_value = subscription
    mock_subscription_svc.return_value = subscription_service_mock

    credit_account_service = MagicMock()
    credit_account_service.update_credit_account.side_effect = ValueError
    mock_credit_account_get.return_value = credit_account_service

    with pytest.raises(ValueError):
        result = client.get(endpoint)
        assert result.status_code == status.HTTP_400_BAD_REQUEST

    mock_credit_account_get.assert_called_once()
    credit_account_service.get_organization_accounts.assert_called_once_with(
        subscription=subscription,
        skip=0,
        limit=50,
    )


@pytest.mark.parametrize(
    "skip, limit, total_matched, next_page",
    [
        (0, 10, 15, NextPage(limit=10, skip=10)),
        (0, 10, 9, None),
        (2, 15, 32, NextPage(limit=15, skip=17)),
        (40, 5, 41, None),
        (10, 5, 41, NextPage(limit=5, skip=15)),
    ],
)
def test_get_credit_accounts_next_page_calculation(
    mock_credit_account_get,
    mock_subscription_svc,
    client,
    organization_id,
    credit_account,
    skip,
    limit,
    total_matched,
    next_page,
):
    accounts = [credit_account] * total_matched
    endpoint = f"/api/v1/organizations/{organization_id}/credit_accounts"
    app.dependency_overrides[get_session] = patched_session  # type: ignore
    subscription_service_mock = MagicMock()
    subscription = Subscription(organization_id=organization_id)
    subscription_service_mock.get_active_subscription.return_value = subscription
    mock_subscription_svc.return_value = subscription_service_mock

    credit_account_service = MagicMock()
    credit_account_service.get_organization_accounts.return_value = (len(accounts), accounts)
    mock_credit_account_get.return_value = credit_account_service

    response = client.get(endpoint, params={"skip": skip, "limit": limit})
    data = response.json()
    assert data["total_matched"] == total_matched
    assert len(data["credit_accounts"]) == len(accounts)
    if next_page is not None:
        assert data["next_page"]["limit"] == next_page.limit
        assert data["next_page"]["skip"] == next_page.skip
    else:
        assert data["next_page"] is None
    credit_account_service.get_organization_accounts.assert_called_once_with(
        subscription=subscription,
        skip=skip,
        limit=limit,
    )
    mock_credit_account_get.assert_called_once()
    assert response.status_code == status.HTTP_200_OK
