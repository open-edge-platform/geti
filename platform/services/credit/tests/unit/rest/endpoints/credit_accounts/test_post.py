# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import status

from db.model.subscription import Subscription
from dependencies import get_session
from exceptions.custom_exception_handler import custom_exception_handler
from main import app
from rest.schema.common import MAX_INT_32
from service.credit_account import CreditAccountDetails
from utils.enums import CreditAccountType

ORGANIZATION_ID = "000000000000000000000001"


def patched_session():
    return MagicMock()


@pytest.mark.parametrize("renewable_amount", [100, None])
@pytest.mark.parametrize("expires", [1712845839000, None])
def test_success(client, renewable_amount, expires) -> None:
    # Arrange
    account_id = uuid4()

    endpoint = f"/api/v1/organizations/{ORGANIZATION_ID}/credit_accounts"
    app.dependency_overrides[get_session] = patched_session  # type: ignore

    payload = {"name": "credit_account", "init_amount": 1000}
    if renewable_amount is not None:
        payload["renewable_amount"] = renewable_amount
    if expires is not None:
        payload["expires"] = expires

    credit_account_service = MagicMock()
    credit_account_service.create_credit_account.return_value = account_id
    subscription_service = MagicMock()
    subscription = Subscription(organization_id=ORGANIZATION_ID)
    subscription_service.get_active_subscription.return_value = subscription

    # Act
    with (
        patch(
            "rest.endpoints.credit_accounts.post.CreditAccountService", return_value=credit_account_service
        ) as mock_credit_account_service,
        patch(
            target="rest.endpoints.credit_accounts.post.SubscriptionService", return_value=subscription_service
        ) as mock_subscription_service,
    ):
        result = client.post(endpoint, json=payload)

    # Assert
    mock_credit_account_service.assert_called_once()
    credit_account_service.create_credit_account.assert_called_once_with(
        details=CreditAccountDetails(
            name="credit_account",
            account_type=CreditAccountType.ASSET,
            init_amount=1000,
            renewable_amount=renewable_amount,
            expires=expires,
        ),
        subscription=subscription,
    )
    assert (
        result.status_code == status.HTTP_201_CREATED
        and "location" in result.headers
        and result.headers["location"] == f"/api/v1/organizations/{ORGANIZATION_ID}/credit_accounts/{account_id}"
    )
    mock_subscription_service.assert_called_once()


@pytest.mark.parametrize("renewable_amount", [100, None])
@pytest.mark.parametrize("expires", [1712845839000, None])
def test_forbidden(client, renewable_amount, expires) -> None:
    # Arrange
    account_id = uuid4()

    endpoint = f"/api/v1/organizations/{ORGANIZATION_ID}/credit_accounts"
    app.dependency_overrides[get_session] = patched_session  # type: ignore

    payload = {"name": "credit_account", "init_amount": 1000}
    if renewable_amount is not None:
        payload["renewable_amount"] = renewable_amount
    if expires is not None:
        payload["expires"] = expires

    credit_account_service = MagicMock()
    credit_account_service.create_credit_account.return_value = account_id
    subscription_service = MagicMock()
    subscription_service.get_active_subscription.return_value = None

    # Act
    with (
        patch(
            "rest.endpoints.credit_accounts.post.CreditAccountService", return_value=credit_account_service
        ) as mock_credit_account_service,
        patch(
            target="rest.endpoints.credit_accounts.post.SubscriptionService", return_value=subscription_service
        ) as mock_subscription_service,
    ):
        result = client.post(endpoint, json=payload)

    # Assert
    assert result.status_code == status.HTTP_403_FORBIDDEN
    mock_subscription_service.assert_called_once()
    mock_credit_account_service.assert_not_called()


@pytest.mark.parametrize(
    "error, response_code",
    [(ValueError, status.HTTP_400_BAD_REQUEST), (RuntimeError, status.HTTP_500_INTERNAL_SERVER_ERROR)],
)
@patch("rest.endpoints.credit_accounts.post.CreditAccountService")
def test_failure(mock_credit_account_service, client, error, response_code) -> None:
    # Arrange
    endpoint = f"/api/v1/organizations/{ORGANIZATION_ID}/credit_accounts"
    app.dependency_overrides[get_session] = patched_session  # type: ignore
    app.add_exception_handler(Exception, custom_exception_handler)

    payload = {"name": "credit_account", "init_amount": 1000}

    credit_account_service = MagicMock()
    credit_account_service.create_credit_account.side_effect = error
    mock_credit_account_service.return_value = credit_account_service
    subscription_service = MagicMock()
    subscription = Subscription(organization_id=ORGANIZATION_ID)
    subscription_service.get_active_subscription.return_value = subscription

    # Act
    with (
        patch(
            target="rest.endpoints.credit_accounts.post.SubscriptionService", return_value=subscription_service
        ) as mock_subscription_service,
        pytest.raises(error),
    ):
        result = client.post(endpoint, json=payload)
        assert result.status_code == response_code

    # Assert
    mock_credit_account_service.assert_called_once()
    mock_subscription_service.assert_called_once()
    credit_account_service.create_credit_account.assert_called_once_with(
        details=CreditAccountDetails(
            name="credit_account",
            account_type=CreditAccountType.ASSET,
            init_amount=1000,
        ),
        subscription=subscription,
    )


@pytest.mark.parametrize(
    "init_amount, renewable_amount",
    [
        (0, MAX_INT_32 + 1),
        (100, -1),
        (-1, MAX_INT_32),
        (MAX_INT_32 + 1, MAX_INT_32),
        (MAX_INT_32 + 1, MAX_INT_32 + 1),
    ],
)
@patch("rest.endpoints.credit_accounts.post.CreditAccountService")
def test_create_credit_account_validation_error(
    mock_credit_account_service, client, organization_id, init_amount, renewable_amount
) -> None:
    # Arrange
    endpoint = f"/api/v1/organizations/{organization_id}/credit_accounts"
    app.dependency_overrides[get_session] = patched_session  # type: ignore
    credit_account_service = MagicMock()
    mock_credit_account_service.return_value = credit_account_service
    payload = {
        "name": "credit_account",
        "init_amount": init_amount,
        "renewable_amount": renewable_amount,
        "expires": None,
    }

    # Act
    result = client.post(endpoint, json=payload)
    result_data = result.json()

    # Assert
    mock_credit_account_service.assert_not_called()
    assert result.status_code == status.HTTP_400_BAD_REQUEST
    assert result_data["message"] is not None
