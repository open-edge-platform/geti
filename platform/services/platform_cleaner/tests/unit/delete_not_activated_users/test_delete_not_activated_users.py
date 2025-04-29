# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
This is migration script
"""

import os
from datetime import datetime
from unittest.mock import patch

import pytest
from grpc_interfaces.account_service.enums import UserStatus

from delete_not_activated_users.delete_not_activated_users import (
    ActivatedUsers,
    _days_difference_from_current_utc,
    delete_not_activated_users,
    main,
)


@pytest.fixture
def mock_account_service_client():
    with patch("delete_not_activated_users.delete_not_activated_users.AccountServiceClient") as mock:
        yield mock


@pytest.fixture
def mock_days_difference_from_current_utc():
    with patch("delete_not_activated_users.delete_not_activated_users._days_difference_from_current_utc") as mock:
        yield mock


def test_get_all_organizations(mock_account_service_client):
    mock_instance = mock_account_service_client.return_value
    mock_instance.get_all_organizations.return_value = ["org1", "org2"]

    activated_users = ActivatedUsers()
    organizations = activated_users._get_all_organizations()

    assert organizations == ["org1", "org2"]
    mock_account_service_client.assert_called_once()
    mock_instance.get_all_organizations.assert_called_once()


def test_get_all_users(mock_account_service_client):
    expected_users = ["user1", "user2"]
    organization_id = "some-organization"
    mock_instance = mock_account_service_client.return_value
    mock_instance.get_organizations_users.return_value = expected_users

    activated_users = ActivatedUsers()
    actual_users = activated_users._get_registered_users(organization_id=organization_id)

    assert actual_users == expected_users
    mock_account_service_client.assert_called_once()
    mock_instance.get_organizations_users.assert_called_once()


def test_get_user_by_id(mock_account_service_client):
    expected_user = {"id": "some-id", "organizationID": "some-org-id", "createdAt": "2020-01-21T00:00:00Z"}
    mock_instance = mock_account_service_client.return_value
    mock_instance.get_user_by_id.return_value = expected_user

    activated_users = ActivatedUsers()
    actual_users = activated_users._get_user_by_id(
        user_id=expected_user["id"], organization_id=expected_user["organizationID"]
    )

    assert actual_users == expected_user
    mock_account_service_client.assert_called_once()
    mock_instance.get_user_by_id.assert_called_once()


def test_change_user_status(mock_account_service_client):
    organization_id = "some-organization"
    user_id = "some-organization"
    status = "DEL"
    mock_instance = mock_account_service_client.return_value
    mock_instance.change_user_status.return_value = status

    activated_users = ActivatedUsers()
    actual_result = activated_users._change_user_status(organization_id=organization_id, user_id=user_id, status=status)

    assert actual_result == status
    mock_account_service_client.assert_called_once()
    mock_instance.change_user_status.assert_called_once()


@pytest.mark.parametrize(
    "user_status, created_date, days_difference_from_current_utc, change_user_status_called",
    [
        (UserStatus.ACTIVATED, "2023-11-30T12:30:45Z", 0, 0),
        (UserStatus.ACTIVATED, "2023-11-30T12:30:45Z", 31, 0),
        (UserStatus.REGISTERED, "2023-10-30T12:30:45Z", 29, 1),
        (UserStatus.REGISTERED, "2023-10-30T12:30:45Z", 30, 1),
    ],
)
def test_account_service_client_delete_not_activated_users(
    mock_account_service_client,
    mock_days_difference_from_current_utc,
    user_status,
    created_date,
    days_difference_from_current_utc,
    change_user_status_called,
):
    days_until_deletion = 30
    mock_instance = mock_account_service_client.return_value
    mock_instance.get_all_organizations.return_value = [{"id": "some-org-id"}]
    mock_instance.get_organizations_users.return_value = [
        {"id": "some-user-id", "organizationId": "some-org-id", "status": user_status, "createdAt": created_date}
    ]
    mock_account_service_client.get_user_by_id.return_value = [
        {"id": "some-user-id", "status": user_status, "createdAt": created_date}
    ]
    mock_instance.change_user_status.return_value = "not-relevant-status"
    mock_days_difference_from_current_utc.return_value = days_difference_from_current_utc

    activated_users = ActivatedUsers()
    activated_users.delete_not_activated_users(days_until_deletion=days_until_deletion)

    mock_account_service_client.assert_called_once()
    mock_instance.get_all_organizations.assert_called_once()
    assert mock_instance.get_organizations_users.call_count == 2  # 1 call for registered users, 1 for active users
    mock_instance.change_user_status.call_count = change_user_status_called


@patch("delete_not_activated_users.delete_not_activated_users.ActivatedUsers")
def test_delete_not_activated_users(mock_active_user):
    mock_instance = mock_active_user.return_value
    mock_instance.delete_not_activated_users.return_value = None
    days_until_deletion = 30

    delete_not_activated_users(days_until_deletion=days_until_deletion)

    mock_active_user.assert_called_once()
    mock_instance.delete_not_activated_users.assert_called_once_with(days_until_deletion=days_until_deletion)


def test_main(mocker):
    """Tests the main function."""
    mock_delete_not_activated_users = mocker.patch(
        "delete_not_activated_users.delete_not_activated_users.delete_not_activated_users"
    )
    not_activated_user_expiration_in_days = "1234"

    # Mock environment variables.
    os.environ.update(
        {
            "NOT_ACTIVATED_USER_EXPIRATION_IN_DAYS": not_activated_user_expiration_in_days,
        }
    )

    main()

    mock_delete_not_activated_users.assert_called_once_with(
        days_until_deletion=int(not_activated_user_expiration_in_days)
    )


@pytest.mark.parametrize(
    "timestamp_str, expected_days",
    [
        ("2024-03-15T00:00:00Z", 5),
        ("2024-03-19T12:00:00Z", 1),
        ("2024-03-20T12:00:00Z", 0),
        ("2024-03-21T12:00:00Z", -1),
    ],
)
def test_days_difference_from_current_utc(timestamp_str, expected_days):
    with patch("delete_not_activated_users.delete_not_activated_users.datetime") as mock:
        mock.utcnow.return_value = datetime(2024, 3, 20, 12, 0, 0)
        mock.strptime.return_value = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%SZ")

        assert _days_difference_from_current_utc(timestamp_str) == expected_days
