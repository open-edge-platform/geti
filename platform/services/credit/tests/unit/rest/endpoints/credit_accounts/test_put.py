# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import status

from db.model import CreditAccount, Subscription
from dependencies import get_session
from exceptions.custom_exception_handler import custom_exception_handler
from main import app
from rest.schema.common import MAX_INT_32


def patched_session():
    return MagicMock()


@pytest.fixture
def mock_credit_account_put():
    with patch("rest.endpoints.credit_accounts.put.CreditAccountService") as mock_account_service:
        yield mock_account_service


@pytest.fixture
def mock_subscription_svc():
    with patch("rest.endpoints.credit_accounts.put.SubscriptionService") as mock_subscription_svc:
        yield mock_subscription_svc


@pytest.mark.parametrize("account", ["credit_account", "renewal_credit_account"])
def test_success(
    mock_credit_account_put, mock_subscription_svc, client, organization_id, account_id, account, request, put_payload
):
    endpoint = f"/api/v1/organizations/{organization_id}/credit_accounts/{account_id}"
    app.dependency_overrides[get_session] = patched_session  # type: ignore

    subscription_service_mock = MagicMock()
    subscription = Subscription(
        id=uuid4(),
        organization_id=organization_id,
        credit_accounts=[CreditAccount(id=account_id), CreditAccount(id=uuid4())],
    )
    subscription_service_mock.get_active_subscription.return_value = subscription
    mock_subscription_svc.return_value = subscription_service_mock

    credit_account = request.getfixturevalue(account)
    credit_account.id = str(account_id)
    if credit_account.renewable_amount is not None:
        put_payload["renewable_amount"] = 100

    credit_account_service = MagicMock()
    credit_account_service.update_credit_account.return_value = credit_account
    mock_credit_account_put.return_value = credit_account_service

    response = client.put(endpoint, json=put_payload)
    data = response.json()

    mock_credit_account_put.assert_called_once()
    mock_subscription_svc.assert_called_once()
    credit_account_service.update_credit_account.assert_called_once()
    assert response.status_code == status.HTTP_200_OK and data["id"] == str(account_id)


@pytest.mark.parametrize(
    "error, response_code",
    [(ValueError, status.HTTP_400_BAD_REQUEST), (RuntimeError, status.HTTP_500_INTERNAL_SERVER_ERROR)],
)
def test_update_failure(
    mock_credit_account_put,
    mock_subscription_svc,
    account_id,
    organization_id,
    client,
    error,
    response_code,
    put_payload,
):
    endpoint = f"/api/v1/organizations/{organization_id}/credit_accounts/{account_id}"
    app.dependency_overrides[get_session] = patched_session  # type: ignore
    app.add_exception_handler(Exception, custom_exception_handler)

    subscription_service_mock = MagicMock()
    subscription = Subscription(
        id=uuid4(),
        organization_id=organization_id,
        credit_accounts=[CreditAccount(id=account_id), CreditAccount(id=uuid4())],
    )
    subscription_service_mock.get_active_subscription.return_value = subscription
    mock_subscription_svc.return_value = subscription_service_mock

    credit_account_service = MagicMock()
    credit_account_service.update_credit_account.side_effect = error
    mock_credit_account_put.return_value = credit_account_service

    with pytest.raises(error):
        result = client.put(endpoint, json=put_payload)
        assert result.status_code == response_code

    mock_credit_account_put.assert_called_once()
    credit_account_service.update_credit_account.assert_called_once()


@pytest.mark.parametrize("renewable_amount", [MAX_INT_32 + 1, -1])
@patch("rest.endpoints.credit_accounts.put.CreditAccountService")
def test_update_credit_account_validation_error(
    mock_credit_account_service, mock_subscription_svc, client, organization_id, account_id, renewable_amount
) -> None:
    # Arrange
    endpoint = f"/api/v1/organizations/{organization_id}/credit_accounts/{account_id}"
    app.dependency_overrides[get_session] = patched_session  # type: ignore
    credit_account_service = MagicMock()
    mock_credit_account_service.return_value = credit_account_service
    payload = {"name": "credit_account", "renewable_amount": renewable_amount}

    # Act
    result = client.put(endpoint, json=payload)
    result_data = result.json()

    # Assert
    mock_credit_account_service.assert_not_called()
    assert result.status_code == status.HTTP_400_BAD_REQUEST
    assert result_data["message"] is not None


def test_update_account_wrong_id(
    mock_credit_account_put,
    mock_subscription_svc,
    account_id,
    organization_id,
    client,
    put_payload,
):
    endpoint = f"/api/v1/organizations/{organization_id}/credit_accounts/{account_id}"
    app.dependency_overrides[get_session] = patched_session  # type: ignore
    app.add_exception_handler(Exception, custom_exception_handler)

    subscription_service_mock = MagicMock()
    subscription = Subscription(
        id=uuid4(),
        organization_id=organization_id,
        credit_accounts=[CreditAccount(id=uuid4()), CreditAccount(id=uuid4())],
    )
    subscription_service_mock.get_active_subscription.return_value = subscription
    mock_subscription_svc.return_value = subscription_service_mock

    result = client.put(endpoint, json=put_payload)

    assert result.status_code == status.HTTP_404_NOT_FOUND
    mock_subscription_svc.assert_called_once()
    mock_credit_account_put.assert_not_called()
