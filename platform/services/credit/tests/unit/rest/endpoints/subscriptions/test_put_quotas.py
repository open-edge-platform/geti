# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import status

from db.model.subscription import Subscription, SubscriptionQuota
from dependencies import get_session
from main import app
from utils.enums import QuotaType, SubscriptionStatus


def patched_session():
    return MagicMock()


def test_create_success(client, organization_id, workspace_id) -> None:
    # Arrange
    endpoint = f"/api/v1/organizations/{organization_id}/subscriptions/active/quotas"
    app.dependency_overrides[get_session] = patched_session  # type: ignore
    subscription_service = MagicMock()
    subscription_id = uuid4()
    payload = {
        "service_name": "service_name",
        "quota_name": "quota_name",
        "quota_type": QuotaType.MAX_TRAINING_JOBS,
        "limit": 5,
    }
    subscription_service.get_active_subscription.return_value = Subscription(
        id=subscription_id,
        organization_id=organization_id,
        workspace_id=workspace_id,
        product_id=uuid4(),
        renewal_day_of_month=13,
        status=SubscriptionStatus.ACTIVE,
        created=1234567,
        updated=1234567,
    )
    subscription_service.provisioning_organization_subscription_quota.return_value = SubscriptionQuota(
        id=uuid4(),
        subscription_id=subscription_id,
        service_name="service_name",
        quota_name="quota_name",
        quota_type=QuotaType.MAX_TRAINING_JOBS,
        limit=5,
        created=1234567,
        updated=1234567,
    )

    # Act
    with patch(
        "rest.endpoints.subscriptions.put_quotas.SubscriptionService", return_value=subscription_service
    ) as mock_subscription_service:
        result = client.put(endpoint, json=payload)

    # Assert
    mock_subscription_service.assert_called_once()
    assert result.status_code == status.HTTP_200_OK


def test_create_no_active_subscription(client, organization_id) -> None:
    # Arrange
    endpoint = f"/api/v1/organizations/{organization_id}/subscriptions/active/quotas"
    app.dependency_overrides[get_session] = patched_session  # type: ignore
    subscription_service = MagicMock()
    subscription_service.get_active_subscription.return_value = None
    payload = {
        "service_name": "service_name",
        "quota_name": "quota_name",
        "quota_type": QuotaType.MAX_TRAINING_JOBS,
        "limit": 5,
    }

    # Act
    with patch(
        "rest.endpoints.subscriptions.put_quotas.SubscriptionService", return_value=subscription_service
    ) as mock_subscription_service:
        result = client.put(endpoint, json=payload)

    # Assert
    mock_subscription_service.assert_called_once()
    assert result.status_code == status.HTTP_404_NOT_FOUND


def test_update_success(client, organization_id, workspace_id) -> None:
    # Arrange
    endpoint = f"/api/v1/organizations/{organization_id}/subscriptions/active/quotas"
    app.dependency_overrides[get_session] = patched_session  # type: ignore
    subscription_service = MagicMock()
    subscription_id = uuid4()
    payload = {
        "service_name": "service_name",
        "quota_name": "quota_name",
        "quota_type": QuotaType.MAX_TRAINING_JOBS,
        "limit": 5,
    }
    subscription_service.get_active_subscription.return_value = Subscription(
        id=subscription_id,
        organization_id=organization_id,
        workspace_id=workspace_id,
        product_id=uuid4(),
        renewal_day_of_month=13,
        status=SubscriptionStatus.ACTIVE,
        created=1234567,
        updated=1234567,
    )
    subscription_service.provisioning_organization_subscription_quota.return_value = SubscriptionQuota(
        id=uuid4(),
        subscription_id=subscription_id,
        service_name="service_name",
        quota_name="quota_name",
        quota_type=QuotaType.MAX_TRAINING_JOBS,
        limit=5,
        created=1234567,
        updated=1234567,
    )

    # Act
    with patch(
        "rest.endpoints.subscriptions.put_quotas.SubscriptionService", return_value=subscription_service
    ) as mock_subscription_service:
        result = client.put(endpoint, json=payload)

    # Assert
    mock_subscription_service.assert_called_once()
    assert result.status_code == status.HTTP_200_OK


@pytest.mark.parametrize(
    "limit, quote_type",
    [
        (-1, QuotaType.MAX_TRAINING_JOBS),
        (0, QuotaType.MAX_USERS_COUNT),
        (1, "wrong_quota_type"),
    ],
)
def test_wrong_payload(client, organization_id, limit, quote_type) -> None:
    # Arrange
    endpoint = f"/api/v1/organizations/{organization_id}/subscriptions/active/quotas"
    app.dependency_overrides[get_session] = patched_session  # type: ignore
    payload = {
        "service_name": "service_name",
        "quota_name": "quota_name",
        "quota_type": quote_type,
        "limit": limit,
    }

    # Act
    result = client.put(endpoint, json=payload)

    # Assert
    assert result.status_code == status.HTTP_400_BAD_REQUEST
