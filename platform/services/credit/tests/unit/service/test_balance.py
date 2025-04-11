# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from freezegun import freeze_time

from db.model.subscription import Subscription
from rest.schema.balance import BalanceResponse
from service.balance import BalanceService
from utils.time import datetime_to_unix_milliseconds

SUBSCRIPTION_ID = uuid4()


@pytest.mark.parametrize(
    "request_date, current_date, cycle_start_date",
    [
        (
            None,
            datetime(year=2024, month=1, day=1, hour=12, tzinfo=timezone.utc),
            datetime(year=2023, month=12, day=10, hour=0, tzinfo=timezone.utc),
        ),
        (
            datetime(year=2023, month=12, day=8, hour=0, tzinfo=timezone.utc),
            datetime(year=2023, month=12, day=8, hour=0, tzinfo=timezone.utc),
            datetime(year=2023, month=11, day=10, hour=0, tzinfo=timezone.utc),
        ),
    ],
)
@patch("service.balance.BalanceRepository")
@freeze_time("2024-01-01 12:00:00")
def test_get_credit_accounts_balances(mock_balance_repo, request_date, current_date, cycle_start_date) -> None:
    # Arrange
    subscription = Subscription(id=SUBSCRIPTION_ID, organization_id="org-1", renewal_day_of_month=10)
    balance_repo = MagicMock()
    mock_balance_repo.return_value = balance_repo
    balance_repo.get_balance.return_value = [("acc_1", 100, 100, 0), ("acc_2", 200, 200, 25)]

    session = MagicMock()
    balance_service = BalanceService(session=session)

    # Act
    if request_date is not None:
        request_date_millis = datetime_to_unix_milliseconds(request_date)
    else:
        request_date_millis = None

    accounts_balances = balance_service.get_credit_accounts_balances(
        subscription=subscription, organization_id="org-1", _db_session=session, date=request_date_millis
    )
    # Assert
    balance_repo.get_balance.assert_called_once_with(
        subscription_id=subscription.id,
        current_date=datetime_to_unix_milliseconds(current_date),
        cycle_start_date=datetime_to_unix_milliseconds(cycle_start_date),
    )
    assert accounts_balances == {
        "acc_1": BalanceResponse(incoming=100, available=100, blocked=0),
        "acc_2": BalanceResponse(incoming=200, available=200, blocked=25),
    }


@patch("service.balance.BalanceRepository")
@freeze_time("2024-01-01 12:00:00")
def test_get_credit_accounts_balances_for_transactionless_accounts(mock_balance_repo) -> None:
    # Arrange
    balance_repo = MagicMock()
    mock_balance_repo.return_value = balance_repo
    balance_repo.get_balance.return_value = []
    subscription = Subscription(id=SUBSCRIPTION_ID, organization_id="org-1", renewal_day_of_month=10)
    session = MagicMock()
    balance_service = BalanceService(session=session)

    # Act
    balance_request_date = datetime_to_unix_milliseconds(datetime(year=2023, month=12, day=8, hour=0))
    accounts_balances = balance_service.get_credit_accounts_balances(
        subscription=subscription, organization_id="org-1", _db_session=session, date=balance_request_date
    )

    # Assert
    balance_repo.get_balance.assert_called_once_with(
        subscription_id=subscription.id,
        current_date=balance_request_date,
        cycle_start_date=datetime_to_unix_milliseconds(datetime(year=2023, month=11, day=10, hour=0)),
    )
    assert accounts_balances == {}


@pytest.mark.parametrize(
    "request_date, current_date, cycle_start_date",
    [
        (
            None,
            datetime(year=2024, month=1, day=1, hour=12, tzinfo=timezone.utc),
            datetime(year=2023, month=12, day=10, hour=0, tzinfo=timezone.utc),
        ),
        (
            datetime(year=2023, month=12, day=8, hour=0, tzinfo=timezone.utc),
            datetime(year=2023, month=12, day=8, hour=0, tzinfo=timezone.utc),
            datetime(year=2023, month=11, day=10, hour=0, tzinfo=timezone.utc),
        ),
    ],
)
@patch("service.balance.BalanceRepository")
@freeze_time("2024-01-01 12:00:00")
def test_get_organization_balance(mock_balance_repo, request_date, current_date, cycle_start_date) -> None:
    # Arrange
    subscription = Subscription(id=SUBSCRIPTION_ID, organization_id="org-1", renewal_day_of_month=10)

    balance_repo = MagicMock()
    mock_balance_repo.return_value = balance_repo
    balance_repo.get_balance.return_value = [("acc_1", 100, 100, 0), ("acc_2", 200, 200, 30)]

    session = MagicMock()
    balance_service = BalanceService(session=session)

    if request_date is not None:
        request_date_millis = datetime_to_unix_milliseconds(request_date)
    else:
        request_date_millis = None

    balance = balance_service.get_organization_balance(active_subscription=subscription, date=request_date_millis)

    # Assert
    balance_repo.get_balance.assert_called_once_with(
        subscription_id=subscription.id,
        current_date=datetime_to_unix_milliseconds(current_date),
        cycle_start_date=datetime_to_unix_milliseconds(cycle_start_date),
    )
    assert balance == BalanceResponse(incoming=300, available=300, blocked=30)


@patch("service.balance.BalanceRepository")
@freeze_time("2024-01-01 12:00:00")
def test_get_organization_balance_for_transactionless_accounts(mock_balance_repo) -> None:
    # Arrange
    subscription = Subscription(id=SUBSCRIPTION_ID, organization_id="org-1", renewal_day_of_month=10)

    balance_repo = MagicMock()
    mock_balance_repo.return_value = balance_repo
    balance_repo.get_balance.return_value = []

    session = MagicMock()
    balance_service = BalanceService(session=session)

    # Act
    balance_request_date = datetime_to_unix_milliseconds(datetime(year=2023, month=12, day=8, hour=0))
    balance = balance_service.get_organization_balance(active_subscription=subscription, date=balance_request_date)

    # Assert
    balance_repo.get_balance.assert_called_once_with(
        subscription_id=subscription.id,
        current_date=balance_request_date,
        cycle_start_date=datetime_to_unix_milliseconds(datetime(year=2023, month=11, day=10, hour=0)),
    )

    assert balance == BalanceResponse(incoming=0, available=0, blocked=0)
