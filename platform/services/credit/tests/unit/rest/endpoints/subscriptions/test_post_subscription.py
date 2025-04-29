# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import status

from db.model import Subscription
from dependencies import get_session
from exceptions.custom_exception_handler import custom_exception_handler
from main import app

ORGANIZATION_ID = "000000000000000000000001"
WORKSPACE_ID = "000000000000000000000111"


def patched_session():
    return MagicMock()


def test_success(client) -> None:
    # Arrange
    endpoint = f"/api/v1/organizations/{ORGANIZATION_ID}/workspaces/{WORKSPACE_ID}/subscriptions"
    app.dependency_overrides[get_session] = patched_session  # type: ignore
    payload = {"product_id": str(uuid4())}
    subscription_id = uuid4()
    subscription_service = MagicMock()
    subscription_service.transition.return_value = Subscription(id=subscription_id)
    subscription_service.get_active_subscription.return_value = None

    # Act
    with patch(
        "rest.endpoints.subscriptions.create.SubscriptionService", return_value=subscription_service
    ) as mock_subscription_service:
        result = client.post(endpoint, json=payload)

    # Assert
    assert (
        result.status_code == status.HTTP_201_CREATED
        and "location" in result.headers
        and result.headers["location"]
        == f"/api/v1/organizations/{ORGANIZATION_ID}/workspaces/{WORKSPACE_ID}/subscriptions/{subscription_id}"
    )
    assert mock_subscription_service.call_count == 1


def test_subscription_exists(client) -> None:
    # Arrange
    endpoint = f"/api/v1/organizations/{ORGANIZATION_ID}/workspaces/{WORKSPACE_ID}/subscriptions"
    app.dependency_overrides[get_session] = patched_session  # type: ignore
    product_id = str(uuid4())
    payload = {"product_id": product_id}
    subscription_service = MagicMock()
    subscription_service.get_active_subscription.return_value = Subscription(product_id=product_id)

    # Act
    with (
        patch("rest.endpoints.subscriptions.create.SubscriptionService", return_value=subscription_service),
    ):
        result = client.post(endpoint, json=payload)
        # Assert
        assert result.status_code == status.HTTP_409_CONFLICT
    subscription_service.get_active_subscription.assert_called_once()
    subscription_service.transition.assert_not_called()


def test_internal_failure(client) -> None:
    # Arrange
    endpoint = f"/api/v1/organizations/{ORGANIZATION_ID}/workspaces/{WORKSPACE_ID}/subscriptions"
    app.dependency_overrides[get_session] = patched_session  # type: ignore
    app.add_exception_handler(Exception, custom_exception_handler)
    payload = {"product_id": str(uuid4())}
    subscription_service = MagicMock()
    subscription_service.get_active_subscription.return_value = None
    subscription_service.transition.side_effect = RuntimeError
    # Act
    with (
        patch(
            "rest.endpoints.subscriptions.create.SubscriptionService", return_value=subscription_service
        ) as mock_subscription_service,
        pytest.raises(RuntimeError),
    ):
        result = client.post(endpoint, json=payload)
        assert result.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    # Assert
    assert mock_subscription_service.call_count == 1
