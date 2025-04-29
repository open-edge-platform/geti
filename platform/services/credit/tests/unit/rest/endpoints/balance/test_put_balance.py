# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import status

from db.model import CreditAccount, Subscription
from dependencies import get_session
from main import app
from rest.schema.common import MAX_INT_32

ORGANIZATION_ID = "000000000000000000000001"
ACCOUNT_ID = uuid4()
ENDPOINT = f"/api/v1/organizations/{ORGANIZATION_ID}/credit_accounts/{ACCOUNT_ID}/balance"


def patched_session():
    return MagicMock()


@pytest.mark.parametrize(
    "payload",
    [
        {"add": 100},
        {"subtract": 100},
    ],
)
def test_success(client, payload) -> None:
    # Arrange
    app.dependency_overrides[get_session] = patched_session  # type: ignore

    subscription_service = MagicMock()
    transaction_service = MagicMock()
    subscription_service.get_active_subscription.return_value = Subscription(
        id=uuid4(), credit_accounts=[CreditAccount(id=ACCOUNT_ID), CreditAccount(id=uuid4())]
    )

    # Act
    with (
        patch(
            target="rest.endpoints.balance.put.TransactionService", return_value=transaction_service
        ) as mock_transaction_service,
        patch(
            target="rest.endpoints.balance.put.SubscriptionService", return_value=subscription_service
        ) as mock_subscription_service,
    ):
        result = client.put(ENDPOINT, json=payload)

    # Assert
    mock_transaction_service.assert_called_once()
    mock_subscription_service.assert_called_once()
    assert result.status_code == status.HTTP_200_OK


@pytest.mark.parametrize(
    "payload",
    [
        {"add": 100, "subtract": 10},
        {},
    ],
)
def test_incorrect_payload(client, payload) -> None:
    # Arrange
    app.dependency_overrides[get_session] = patched_session  # type: ignore
    subscription_service = MagicMock()
    transaction_service = MagicMock()
    subscription_service.get_active_subscription.return_value = Subscription(
        id=uuid4(), credit_accounts=[CreditAccount(id=ACCOUNT_ID), CreditAccount(id=uuid4())]
    )

    # Act
    with (
        patch(
            target="rest.endpoints.balance.put.TransactionService", return_value=transaction_service
        ) as mock_transaction_service,
        patch(
            target="rest.endpoints.balance.put.SubscriptionService", return_value=subscription_service
        ) as mock_subscription_service,
    ):
        result = client.put(ENDPOINT, json=payload)

    # Assert
    mock_subscription_service.assert_called_once()
    mock_transaction_service.assert_not_called()
    assert result.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.parametrize(
    "payload",
    [
        {"add": -100},
        {"add": 0},
        {"subtract": -100},
        {"subtract": MAX_INT_32 + 1},
        {"add": MAX_INT_32 + 1},
    ],
)
def test_incorrect_payload_values(client, payload) -> None:
    # Arrange
    app.dependency_overrides[get_session] = patched_session  # type: ignore
    transaction_service = MagicMock()

    # Act
    with patch(
        "rest.endpoints.balance.put.TransactionService", return_value=transaction_service
    ) as mock_transaction_service:
        result = client.put(ENDPOINT, json=payload)

    # Assert
    mock_transaction_service.assert_not_called()
    assert result.status_code == status.HTTP_400_BAD_REQUEST


def test_wrong_acc_id(client) -> None:
    # Arrange
    app.dependency_overrides[get_session] = patched_session  # type: ignore

    subscription_service = MagicMock()
    transaction_service = MagicMock()
    subscription_service.get_active_subscription.return_value = Subscription(
        id=uuid4(), credit_accounts=[CreditAccount(id=uuid4()), CreditAccount(id=uuid4())]
    )
    payload = {"add": 500}

    # Act
    with (
        patch(
            target="rest.endpoints.balance.put.TransactionService", return_value=transaction_service
        ) as mock_transaction_service,
        patch(
            target="rest.endpoints.balance.put.SubscriptionService", return_value=subscription_service
        ) as mock_subscription_service,
    ):
        result = client.put(ENDPOINT, json=payload)

    # Assert
    mock_transaction_service.assert_not_called()
    mock_subscription_service.assert_called_once()
    assert result.status_code == status.HTTP_404_NOT_FOUND
