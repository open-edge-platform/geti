# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from unittest.mock import MagicMock, patch
from uuid import uuid4

from fastapi import status

from db.model.subscription import Subscription
from dependencies import get_session
from exceptions.custom_exception_handler import custom_exception_handler
from main import app

ORGANIZATION_ID = "000000000000000000000001"
WORKSPACE_ID = "000000000000000000000111"


def patched_session():
    return MagicMock()


def test_success(client) -> None:
    # Arrange
    endpoint = f"/api/v1/organizations/{ORGANIZATION_ID}/subscriptions/active"
    app.dependency_overrides[get_session] = patched_session  # type: ignore
    subscription_service = MagicMock()
    subscription_id = uuid4()
    subscription_service.get_active_subscription.return_value = Subscription(
        id=subscription_id,
        organization_id=ORGANIZATION_ID,
        workspace_id=WORKSPACE_ID,
        product_id=uuid4(),
        renewal_day_of_month=13,
        status="ACTIVE",
        created=1234567,
        updated=1234567,
    )

    # Act
    with patch(
        "rest.endpoints.subscriptions.get_active.SubscriptionService", return_value=subscription_service
    ) as mock_subscription_service:
        result = client.get(endpoint)
    result_data = result.json()

    # Assert
    mock_subscription_service.assert_called_once()
    assert result.status_code == status.HTTP_200_OK
    assert result_data["organization_id"] == ORGANIZATION_ID and result_data["id"] == str(subscription_id)


def test_failure(client) -> None:
    # Arrange
    endpoint = f"/api/v1/organizations/{ORGANIZATION_ID}/subscriptions/active"
    app.dependency_overrides[get_session] = patched_session  # type: ignore
    app.add_exception_handler(Exception, custom_exception_handler)
    subscription_service = MagicMock()
    subscription_service.get_active_subscription.return_value = None

    # Act
    with patch(
        "rest.endpoints.subscriptions.get_active.SubscriptionService", return_value=subscription_service
    ) as mock_subscription_service:
        result = client.get(endpoint)

    # Assert
    mock_subscription_service.assert_called_once()
    assert result.status_code == status.HTTP_404_NOT_FOUND
