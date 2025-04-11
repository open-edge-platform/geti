# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from freezegun import freeze_time

from db.model import CreditAccount
from db.model.subscription import Subscription
from rest.schema.balance import BalanceResponse
from rest.schema.credit_accounts import CreditAccount as CreditAccountResponse
from service.credit_account import CreditAccountDetails, CreditAccountService
from utils.enums import CreditAccountType

ORGANIZATION_ID = "000000000000000000000001"


@patch("service.credit_account.CreditAccountService._create_account")
def test_create_credit_account_invalid_expiration_date(mock_create_account, request) -> None:
    # Arrange
    session = MagicMock()
    account_service = CreditAccountService(session=session)
    details = CreditAccountDetails(
        name="credit_account",
        account_type=CreditAccountType.ASSET,
        init_amount=1000,
        renewable_amount=100,
        expires=int((datetime.utcnow() - timedelta(days=1)).timestamp() * 1000),
    )
    subscription = Subscription(organization_id=ORGANIZATION_ID)

    # Act
    with pytest.raises(ValueError):
        account_service.create_credit_account(details=details, subscription=subscription)

    # Assert
    mock_create_account.assert_not_called()


@patch("service.credit_account.CreditAccountService._create_account")
def test_create_credit_account(mock_create_account, request) -> None:
    # Arrange
    session = MagicMock()
    account_service = CreditAccountService(session=session)
    details = CreditAccountDetails(
        name="credit_account",
        account_type=CreditAccountType.ASSET,
        init_amount=1000,
        renewable_amount=100,
        expires=int((datetime.utcnow() + timedelta(days=1)).timestamp() * 1000),
    )
    subscription = Subscription(organization_id=ORGANIZATION_ID)

    # Act
    account_service.create_credit_account(details=details, subscription=subscription)

    # Assert
    mock_create_account.assert_called_once_with(details=details, subscription=subscription, _db_session=session)


@pytest.mark.parametrize("account_type", [CreditAccountType.LEASE, CreditAccountType.SAAS])
@patch("service.credit_account.TransactionService")
@patch("service.credit_account.AccountRepository")
def test_create_account(mock_account_repo, mock_transaction_service, request, account_type) -> None:
    # Arrange
    account_id = uuid4()

    session = MagicMock()

    account_repo = MagicMock()

    def _account_repo_create(credit_account):
        credit_account.id = account_id

    account_repo.create.side_effect = _account_repo_create
    mock_account_repo.return_value = account_repo

    transaction_service = MagicMock()
    mock_transaction_service.return_value = transaction_service

    account_service = CreditAccountService(session=session)
    expires = int((datetime.utcnow() + timedelta(days=1)).timestamp() * 1000)
    details = CreditAccountDetails(
        name="credit_account",
        account_type=account_type,
        init_amount=1000,
        renewable_amount=100,
        expires=expires,
    )
    subscription = Subscription(organization_id=ORGANIZATION_ID)

    # Act
    result = account_service._create_account(details=details, subscription=subscription, _db_session=session)

    # Assert
    assert result == account_id
    account_repo.create.assert_called_once()
    assert len(account_repo.create.call_args[1]) == 1 and "credit_account" in account_repo.create.call_args[1]
    credit_account: CreditAccount = account_repo.create.call_args[1].get("credit_account")
    assert (
        credit_account.id == account_id
        and credit_account.subscription_id == subscription.id
        and credit_account.name == "credit_account"
        and credit_account.type == account_type
        and credit_account.renewable_amount == 100
        and credit_account.expires == expires
    )
    transaction_service.fill_account.assert_not_called()


@patch("service.credit_account.TransactionService")
@patch("service.credit_account.AccountRepository")
def test_create_empty_asset_account(mock_account_repo, mock_transaction_service, request) -> None:
    # Arrange
    account_id = uuid4()

    session = MagicMock()

    account_repo = MagicMock()

    def _account_repo_create(credit_account):
        credit_account.id = account_id

    account_repo.create.side_effect = _account_repo_create
    mock_account_repo.return_value = account_repo

    transaction_service = MagicMock()
    mock_transaction_service.return_value = transaction_service

    account_service = CreditAccountService(session=session)
    expires = int((datetime.utcnow() + timedelta(days=1)).timestamp() * 1000)
    details = CreditAccountDetails(
        name="credit_account",
        account_type=CreditAccountType.ASSET,
        renewable_amount=100,
        expires=expires,
    )
    subscription = Subscription(organization_id=ORGANIZATION_ID)

    # Act
    result = account_service._create_account(details=details, subscription=subscription, _db_session=session)

    # Assert
    assert result == account_id
    account_repo.create.assert_called_once()
    assert len(account_repo.create.call_args[1]) == 1 and "credit_account" in account_repo.create.call_args[1]
    credit_account: CreditAccount = account_repo.create.call_args[1].get("credit_account")
    assert (
        credit_account.id == account_id
        and credit_account.subscription_id == subscription.id
        and credit_account.name == "credit_account"
        and credit_account.type == CreditAccountType.ASSET
        and credit_account.renewable_amount == 100
        and credit_account.expires == expires
    )

    transaction_service.fill_account.assert_not_called()


@pytest.mark.parametrize("renewal", [True, False])
@patch("service.credit_account.AccountRepository")
@patch("service.credit_account.BalanceService.get_credit_accounts_balances")
@freeze_time("2024-02-29 12:00:00")
def test_update_account_success(mock_balance_svc, mock_account_repo, renewal):
    session = MagicMock()
    account_new_name = "update_account_name"
    renewable_amount = None

    subscription = MagicMock()
    subscription.organization_id = ORGANIZATION_ID
    subscription.next_renewal_date = 1721174400000
    account_id = str(uuid4())
    credit_account = CreditAccount(
        id=account_id, name="old name", type="ASSET", subscription=subscription, created=12345, updated=12345
    )
    if renewal:
        renewable_amount = 100
        credit_account.renewable_amount = renewable_amount

    mock_repository_instance = mock_account_repo.return_value
    mock_repository_instance.get_account.return_value = credit_account

    mock_balance_svc.return_value = {account_id: BalanceResponse(incoming=300, available=200, blocked=0)}

    account_service = CreditAccountService(session=session)
    update_account = account_service.update_credit_account(
        _db_session=session,
        account_id=credit_account.id,
        organization_id=ORGANIZATION_ID,
        name=account_new_name,
        renewable_amount=renewable_amount,
        expires=1743271787793,
    )

    assert update_account.name == account_new_name
    mock_repository_instance.get_account.assert_called_once_with(
        account_id=credit_account.id,
    )


@patch("service.credit_account.TransactionService")
@patch("service.credit_account.AccountRepository")
def test_create_non_empty_asset_account(mock_account_repo, mock_transaction_service, request) -> None:
    # Arrange
    account_id = uuid4()
    session = MagicMock()
    account_repo = MagicMock()

    def _account_repo_create(credit_account):
        credit_account.id = account_id

    account_repo.create.side_effect = _account_repo_create
    mock_account_repo.return_value = account_repo

    transaction_service = MagicMock()
    mock_transaction_service.return_value = transaction_service

    account_service = CreditAccountService(session=session)
    expires = int((datetime.utcnow() + timedelta(days=1)).timestamp() * 1000)
    details = CreditAccountDetails(
        name="credit_account",
        account_type=CreditAccountType.ASSET,
        init_amount=1000,
        renewable_amount=100,
        expires=expires,
    )
    subscription = Subscription(organization_id=ORGANIZATION_ID)

    # Act
    result = account_service._create_account(details=details, subscription=subscription, _db_session=session)

    # Assert
    assert result == account_id
    account_repo.create.assert_called_once()
    assert len(account_repo.create.call_args[1]) == 1 and "credit_account" in account_repo.create.call_args[1]
    credit_account: CreditAccount = account_repo.create.call_args[1].get("credit_account")
    assert (
        credit_account.id == account_id
        and credit_account.subscription_id == subscription.id
        and credit_account.name == "credit_account"
        and credit_account.type == CreditAccountType.ASSET
        and credit_account.renewable_amount == 100
        and credit_account.expires == expires
    )
    transaction_service.fill_account.assert_called_once_with(
        receiver_acc_id=account_id,
        amount=1000,
        _db_session=session,
        organization_id=ORGANIZATION_ID,
    )


@pytest.mark.parametrize(
    "name, expires, renewable_amount",
    [
        ("   ", 8023398573999, None),
        ("new_account_name", 8023398573999, 200),
        ("new_account_name", 1703271787793, None),
    ],
)
@patch("service.credit_account.AccountRepository")
def test_update_account_failure(mock_account_repo, credit_account, name, renewable_amount, expires) -> None:
    session = MagicMock()
    mock_repository_instance = mock_account_repo.return_value
    mock_repository_instance.get_account.return_value = credit_account

    account_service = CreditAccountService(session=session)
    with pytest.raises(ValueError):
        account_service.update_credit_account(
            _db_session=session,
            account_id=credit_account.id,
            organization_id=credit_account.organization_id,
            name=name,
            renewable_amount=renewable_amount,
            expires=expires,
        )


@pytest.mark.parametrize("has_accounts", [True, False])
@patch("service.credit_account.BalanceService")
@patch("service.credit_account.AccountRepository")
def test_get_organization_accounts_success(mock_account_repo, mock_balance_svc, has_accounts):
    accounts = []
    session = MagicMock()

    subscription = Subscription(organization_id=ORGANIZATION_ID, status="ACTIVE", renewal_day_of_month=12)
    credit_account = CreditAccountResponse(
        id=uuid4(),
        name="asset acc",
        organization_id=ORGANIZATION_ID,
        created=12345,
        updated=12345,
        balance=BalanceResponse(incoming=100, available=100, blocked=0),
    )
    if has_accounts:
        accounts.append(credit_account)

    mock_acc_repository_instance = mock_account_repo.return_value
    mock_acc_repository_instance.get_organization_accounts.return_value = (len(accounts), accounts)
    mock_balance_service_instance = mock_balance_svc.return_value
    mock_balance_service_instance.get_credit_accounts_balances.return_value = {
        credit_account.id: BalanceResponse(incoming=100, available=100, blocked=0)
    }

    account_service = CreditAccountService(session=session)
    organization_accounts = account_service.get_organization_accounts(subscription)

    mock_acc_repository_instance.get_organization_accounts.assert_called_once()
    assert organization_accounts == (len(accounts), accounts)


@pytest.mark.parametrize(
    "skip, limit",
    [
        (-1, 10),
        (0, -10),
        (-2, -1),
    ],
)
def test_get_organization_accounts_failure(skip, limit):
    session = MagicMock()
    account_service = CreditAccountService(session=session)
    subscription = Subscription(organization_id=ORGANIZATION_ID, status="ACTIVE", renewal_day_of_month=12)

    with pytest.raises(ValueError):
        account_service.get_organization_accounts(subscription=subscription, skip=skip, limit=limit)


@patch("service.credit_account.get_renewal_days")
@patch("service.credit_account.CreditAccountService._rollover_subscription")
@patch("service.credit_account.SubscriptionRepository.get_subscriptions_by_renewal_dates_range")
@freeze_time("2024-02-29 12:00:00")
def test_rollover_credit_accounts_renewal_datetime_out_of_range(
    mock_get_subscriptions_by_renewal_dates_range, mock_rollover_subscription, mock_get_renewal_days, request
) -> None:
    # Arrange
    session = MagicMock()

    renewal_days = [1, 29, 30, 31]
    mock_get_renewal_days.return_value = renewal_days
    mock_get_subscriptions_by_renewal_dates_range.return_value = []

    account_service = CreditAccountService(session=session)
    renewal_time = int((datetime.utcnow()).timestamp() * 1000)
    start_date_time = int((datetime.utcnow() + timedelta(days=1)).timestamp() * 1000)
    end_date_time = int((datetime.utcnow() + timedelta(days=5)).timestamp() * 1000)

    # Act
    account_service.rollover_credit_accounts(
        start_date_time=start_date_time, end_date_time=end_date_time, renewal_date=renewal_time
    )

    # Assert
    mock_get_renewal_days.assert_called_once_with(start_date_time, end_date_time)
    mock_get_subscriptions_by_renewal_dates_range.assert_called_once_with(renewal_days)
    mock_rollover_subscription.assert_not_called()


@patch("service.credit_account.get_renewal_days")
@patch("service.credit_account.AccountRepository")
@patch("service.credit_account.SubscriptionRepository.get_subscriptions_by_renewal_dates_range")
@patch("service.credit_account.BalanceService.get_credit_accounts_balances")
@patch("service.credit_account.TransactionService")
@freeze_time("2024-02-29 12:00:00")
def test_rollover_credit_accounts_renewal_datetime_in_range(
    mock_transaction_svc,
    mock_get_credit_accounts_balances,
    mock_get_subscriptions_by_renewal_dates_range,
    mock_account_repo,
    mock_get_renewal_days,
    request,
) -> None:
    # Arrange
    session = MagicMock()
    mock_get_renewal_days.side_effect = [1, 2, 3, 30, 31]

    subscription1 = MagicMock()
    subscription1.id = uuid4()
    subscription1.organization_id = "org-1"
    subscription1.renewal_day_of_month = 1

    subscription2 = MagicMock()
    subscription2.id = uuid4()
    subscription2.organization_id = "org-2"
    subscription2.renewal_day_of_month = 31

    mock_get_subscriptions_by_renewal_dates_range.return_value = [subscription1, subscription2]

    credit_account1 = MagicMock()
    credit_account2 = MagicMock()
    account_repo = MagicMock()
    mock_account_repo.return_value = account_repo
    account_repo.get_renewable_asset_accounts.return_value = [credit_account1, credit_account2]

    mock_get_credit_accounts_balances.return_value = {}

    transaction_service = MagicMock()
    mock_transaction_svc.return_value = transaction_service

    account_service = CreditAccountService(session=session)
    renewal_time = int((datetime.utcnow()).timestamp() * 1000)
    start_date_time = int((datetime.utcnow() + timedelta(days=1)).timestamp() * 1000)
    end_date_time = int((datetime.utcnow() + timedelta(days=5)).timestamp() * 1000)

    # Act
    account_service.rollover_credit_accounts(
        start_date_time=start_date_time, end_date_time=end_date_time, renewal_date=renewal_time
    )

    # Assert
    assert transaction_service.fill_account.call_count == 4  # 2 subscriptions, each has 2 renewable accounts


@patch("service.credit_account.get_renewal_days")
@patch("service.credit_account.AccountRepository")
@patch("service.credit_account.SubscriptionRepository.get_subscriptions_by_renewal_dates_range")
@patch("service.credit_account.BalanceService.get_credit_accounts_balances")
@patch("service.credit_account.TransactionService")
@freeze_time("2024-01-01 12:00:00")
def test_rollover_credit_account_already_has_transaction(
    mock_transaction_svc,
    mock_get_credit_accounts_balances,
    mock_get_subscriptions_by_renewal_dates_range,
    mock_account_repo,
    mock_get_renewal_days,
    request,
) -> None:
    # Arrange
    session = MagicMock()
    mock_get_renewal_days.side_effect = [2, 3, 4, 5, 6, 7]

    subscription = MagicMock()
    subscription.id = uuid4()
    subscription.organization_id = "org-1"
    subscription.renewal_day_of_month = 2

    mock_get_subscriptions_by_renewal_dates_range.return_value = [subscription]

    credit_account = MagicMock()
    credit_account.id = uuid4()

    account_repo = MagicMock()
    mock_account_repo.return_value = account_repo
    account_repo.get_renewable_asset_accounts.return_value = [credit_account]

    mock_get_credit_accounts_balances.return_value = {
        credit_account.id: BalanceResponse(incoming=100, available=100, blocked=0)
    }

    transaction_service = MagicMock()
    mock_transaction_svc.return_value = transaction_service

    account_service = CreditAccountService(session=session)
    renewal_time = int((datetime.utcnow() - timedelta(days=8)).timestamp() * 1000)
    start_date_time = int((datetime.utcnow() - timedelta(days=7)).timestamp() * 1000)
    end_date_time = int((datetime.utcnow() + timedelta(days=2)).timestamp() * 1000)

    # Act
    account_service.rollover_credit_accounts(
        start_date_time=start_date_time, end_date_time=end_date_time, renewal_date=renewal_time
    )

    # Assert
    transaction_service.fill_account.assert_not_called()


@pytest.mark.parametrize(
    "expires, expected_expires",
    [
        (None, None),
        (1000_000, 1005_000),
        (800_000, 800_000),
    ],
    ids=[
        "no_expiration_date",
        "expiration_date_after_cancellation",
        "expiration_date_before_cancellation",
    ],
)
@patch("service.credit_account.TransactionService")
@patch("service.credit_account.AccountRepository")
def test_resume_credit_account(mock_account_repository, mock_transaction_service, expires, expected_expires):
    account_id = uuid4()
    cancellation_time = 900_000
    current_time = cancellation_time + 5000
    credits_amount = 500

    credit_account = MagicMock()
    credit_account.id = account_id
    credit_account.expires = expires
    credit_account.updated = 700_000
    credit_account.subscription.organization_id = uuid4()

    def _update_account_updated(*args, **kwargs):
        credit_account.updated = current_time
        return credit_account

    mock_account_repository.return_value.get_account.side_effect = _update_account_updated

    session = MagicMock()
    credit_account_service = CreditAccountService(session)

    credit_account_service.resume_credit_account(
        account_id=account_id,
        cancellation_time=cancellation_time,
        current_time=current_time,
        credits_amount=credits_amount,
    )

    assert credit_account.expires == expected_expires
    assert credit_account.updated == current_time
    mock_transaction_service.return_value.fill_account.assert_called_once_with(
        receiver_acc_id=account_id,
        amount=credits_amount,
        _db_session=session,
        organization_id=credit_account.subscription.organization_id,
    )
