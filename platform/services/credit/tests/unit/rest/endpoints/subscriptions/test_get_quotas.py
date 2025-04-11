# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from unittest.mock import MagicMock, patch

from fastapi import status

from dependencies import get_session
from main import app
from rest.schema.subscription import SubscriptionQuota

ORGANIZATION_ID = "000000000000000000000001"


def patched_session():
    return MagicMock()


def test_success(client) -> None:
    # Arrange
    endpoint = f"/api/v1/organizations/{ORGANIZATION_ID}/subscriptions/active/quotas"
    app.dependency_overrides[get_session] = patched_session  # type: ignore
    subscription_service = MagicMock()
    subscription_service.get_current_quotas.return_value = (
        1,
        [
            SubscriptionQuota(
                id=None,
                organization_id=ORGANIZATION_ID,
                service_name="trainings",
                quota_name="Max number of concurrent training jobs",
                quota_type="MAX_TRAINING_JOBS",
                limit=10,
                created=None,
                updated=None,
            )
        ],
    )

    # Act
    with patch(
        "rest.endpoints.subscriptions.get_quotas.SubscriptionService", return_value=subscription_service
    ) as mock_subscription_service:
        result = client.get(endpoint)
    result_data = result.json()

    # Assert
    mock_subscription_service.assert_called_once()
    assert result.status_code == status.HTTP_200_OK
    assert result_data["quotas"] != []
    assert result_data["quotas"][0]["organization_id"] == ORGANIZATION_ID
