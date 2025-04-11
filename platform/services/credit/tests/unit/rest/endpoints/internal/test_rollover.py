# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from datetime import datetime
from unittest.mock import MagicMock, patch

from fastapi import status
from starlette.testclient import TestClient

from dependencies import get_session
from main import app

ORGANIZATION_ID = "000000000000000000000001"


def patched_session():
    return MagicMock()


def test_success_without_renewal_date() -> None:
    # Arrange
    client = TestClient(app)
    endpoint = "/api/v1/internal/tasks/credit_accounts/rollover"
    app.dependency_overrides[get_session] = patched_session  # type: ignore
    credit_account_service = MagicMock()

    # Act
    with patch(
        "rest.endpoints.internal.rollover.CreditAccountService", return_value=credit_account_service
    ) as mock_credit_account_service:
        result = client.post(endpoint)

    # Assert
    mock_credit_account_service.assert_called_once()
    credit_account_service.rollover_credit_accounts.assert_called_once()
    assert result.status_code == status.HTTP_200_OK


def test_success_with_renewal_date() -> None:
    # Arrange
    client = TestClient(app)
    endpoint = "/api/v1/internal/tasks/credit_accounts/rollover"
    app.dependency_overrides[get_session] = patched_session  # type: ignore
    credit_account_service = MagicMock()
    renewal_date = int(datetime(2024, 4, 16, 12, 0, 0).timestamp() * 1000)

    # Act
    with patch(
        "rest.endpoints.internal.rollover.CreditAccountService", return_value=credit_account_service
    ) as mock_credit_account_service:
        result = client.post(endpoint, params={"renewal_date": renewal_date})

    # Assert
    mock_credit_account_service.assert_called_once()
    credit_account_service.rollover_credit_accounts.assert_called_once_with(
        start_date_time=1713312000000,  # Date and time (GMT): April 17, 2024 12:00:00 AM
        end_date_time=1713916800000,  # Date and time (GMT): April 24, 2024 12:00:00 AM
        renewal_date=renewal_date,  # Date and time (GMT): April 16, 2024 12:00:00 AM
    )
    assert result.status_code == status.HTTP_200_OK
