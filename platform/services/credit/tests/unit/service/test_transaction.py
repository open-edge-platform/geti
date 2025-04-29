# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from db.model.subscription import Subscription
from db.repository.transaction import TransactionRepository
from exceptions.custom_exceptions import InsufficientBalanceException
from rest.schema.balance import BalanceResponse
from rest.schema.transactions import AggregateItem, AggregatesResponse, AggregatesResult, GroupItem, ResourcesAmount
from service.transaction import TransactionDetails, TransactionService
from utils.enums import AggregatesKey, CreditAccountType
from utils.time import datetime_to_unix_milliseconds, get_current_datetime

ORGANIZATION_ID = "000000000000000000000001"


@pytest.fixture
def mock_session():
    return MagicMock()


@pytest.fixture
def mock_transaction_repository():
    return MagicMock(spec=TransactionRepository)


@pytest.fixture
def transaction_service(mock_session, mock_transaction_repository):
    with patch("service.transaction.TransactionRepository", return_value=mock_transaction_repository):
        return TransactionService(session=mock_session)


@pytest.mark.parametrize(
    "credits_amount, account_type, exc_info",
    [
        (100, "LEASE", "Invalid account type"),
        (-100, "ASSET", "Credits amount is expected to be a positive integer number"),
    ],
)
@patch("service.transaction.AccountRepository")
def test_fill_account_invalid_data(mock_account_repo, credits_amount, account_type, exc_info):
    # Arrange
    session = MagicMock()
    service = TransactionService(session)
    mock_account_repo.return_value.get_account.return_value = MagicMock(type=account_type)

    # Act & Assert
    with pytest.raises(ValueError, match=exc_info):
        service.fill_account(
            receiver_acc_id=1, amount=credits_amount, _db_session=session, organization_id=ORGANIZATION_ID
        )


@patch("service.transaction.AccountRepository")
@patch("service.transaction.TransactionService._perform_transaction")
def test_fill_account(mock_perform_transaction, mock_account_repo):
    # Arrange
    session = MagicMock()
    service = TransactionService(session)

    asset_account_mock = MagicMock(type=CreditAccountType.ASSET)
    mock_account_repo.return_value.get_account.return_value = asset_account_mock
    saas_account_mock = MagicMock()
    mock_account_repo.return_value.retrieve_saas_account.return_value = saas_account_mock

    details = TransactionDetails(debit=500, credit=0, created=None)

    # Act
    service.fill_account(receiver_acc_id=1, amount=500, _db_session=session, organization_id=ORGANIZATION_ID)

    # Assert
    mock_perform_transaction.assert_called_once_with(
        from_acc=saas_account_mock, target_acc=asset_account_mock, target_details=details
    )


@pytest.mark.parametrize(
    "credits_amount, account_balance, account_type, exc_info",
    [
        (100, 300, "LEASE", "Invalid account type"),
        (-100, 300, "ASSET", "Credits amount is expected to be a positive integer number"),
        (100, 20, "ASSET", "Cannot withdraw"),
    ],
)
@patch("service.transaction.AccountRepository")
@patch("service.transaction.BalanceService")
def test_withdraw_credits_invalid_data(
    mock_balance_svc, mock_account_repo, credits_amount, account_balance, account_type, exc_info
):
    # Arrange
    subscription = Subscription(organization_id=ORGANIZATION_ID, renewal_day_of_month=15)
    session = MagicMock()
    service = TransactionService(session)
    mock_account_repo.return_value.get_account.return_value = MagicMock(type=account_type)
    account_id = uuid4()
    mock_balance_svc.return_value.get_credit_accounts_balances.return_value = {
        account_id: BalanceResponse(incoming=1000, available=1000, blocked=37)
    }

    # Act & Assert
    with pytest.raises(ValueError, match=exc_info):
        service.withdraw_credits(
            account_id=account_id,
            amount=credits_amount,
            _db_session=session,
            organization_id=ORGANIZATION_ID,
            subscription=subscription,
        )


@patch("service.transaction.AccountRepository")
@patch("service.transaction.BalanceService")
@patch("service.transaction.TransactionService._perform_transaction")
def test_withdraw_credits(
    mock_perform_transaction,
    mock_balance_svc,
    mock_account_repo,
):
    # Arrange
    session = MagicMock()
    service = TransactionService(session)

    asset_account_mock = MagicMock(type="ASSET", id="acc_id_1")
    mock_account_repo.return_value.get_account.return_value = asset_account_mock
    saas_account_mock = MagicMock()
    mock_account_repo.return_value.retrieve_saas_account.return_value = saas_account_mock
    subscription = Subscription(organization_id=ORGANIZATION_ID, renewal_day_of_month=15)

    mock_balance_svc.return_value.get_credit_accounts_balances.return_value = {
        "acc_id_1": BalanceResponse(incoming=1000, available=1000, blocked=53)
    }

    details = TransactionDetails(debit=500, credit=0)

    # Act
    service.withdraw_credits(
        account_id="acc_id_1",
        amount=500,
        _db_session=session,
        organization_id=ORGANIZATION_ID,
        subscription=subscription,
    )

    # Assert
    mock_perform_transaction.assert_called_once_with(
        from_acc=asset_account_mock, target_acc=saas_account_mock, target_details=details
    )


def test_acquire_lease_missing_requests():
    # Arrange
    session = MagicMock()
    service = TransactionService(session)
    details = MagicMock(requests={})  # Empty requests
    subscription = Subscription(organization_id=ORGANIZATION_ID, status="ACTIVE", renewal_day_of_month=15)

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        service.acquire_lease(
            details=details, organization_id=ORGANIZATION_ID, _db_session=session, subscription=subscription
        )

    assert "Missing lease requests" in str(exc_info.value)


def test_acquire_lease_insufficient_balance():
    # Arrange
    session = MagicMock()
    service = TransactionService(session)
    service.balance_service.get_credit_accounts_balances = MagicMock(
        return_value={"acc_1": BalanceResponse(incoming=500, available=500, blocked=30)}  # Insufficient balance
    )
    service.account_repository.retrieve_lease_account = MagicMock()
    service.account_repository.get_organization_accounts = MagicMock(return_value=(2, [MagicMock()]))

    subscription = Subscription(organization_id=ORGANIZATION_ID, status="ACTIVE", renewal_day_of_month=15)
    lease_requests = {"image": 600, "frame": 100}  # Total required 700, more than available 500
    details = MagicMock(requests=lease_requests)

    # Act & Assert
    with pytest.raises(InsufficientBalanceException):
        service.acquire_lease(details, subscription, ORGANIZATION_ID, session)


def test_acquire_lease_successful():
    # Arrange
    session = MagicMock()
    service = TransactionService(session)
    account_id = uuid4()
    service.balance_service.get_organization_balance = MagicMock(
        return_value=BalanceResponse(incoming=10_000, available=10_000, blocked=0)  # Sufficient balance
    )
    service.balance_service.get_credit_accounts_balances = MagicMock(
        return_value={account_id: BalanceResponse(incoming=10_000, available=10_000, blocked=0)}  # Sufficient balance
    )
    service.subscription_repository.get_subscription_renewal_day = MagicMock(return_value=10)

    asset_account_mock = MagicMock()
    asset_account_mock.id = account_id
    asset_account_mock.expires = None
    asset_account_mock.renewable_amount = 15
    asset_account_mock.type = CreditAccountType.ASSET

    lease_account_mock = MagicMock()
    lease_account_mock.id = uuid4()
    lease_account_mock.type = CreditAccountType.LEASE

    service._perform_transaction = MagicMock()  # Mocking to verify if it gets called correctly

    lease_requests = {"image": 5_000, "frame": 4_000}
    details = MagicMock(
        workspace_id="workspace_id_123", project_id="project_id_123", service_name="training", requests=lease_requests
    )
    subscription = Subscription(
        organization_id=ORGANIZATION_ID,
        status="ACTIVE",
        renewal_day_of_month=15,
        credit_accounts=[asset_account_mock, lease_account_mock],
    )

    # Act
    lease_id = service.acquire_lease(details, subscription, ORGANIZATION_ID, session)

    # Assert
    service._perform_transaction.assert_called()  # Ensure transaction was attempted
    assert isinstance(lease_id, str)  # Confirm that a lease ID is returned


def test_cancel_lease_already_closed():
    # Arrange
    session = MagicMock()
    service = TransactionService(session)
    service._is_lease_closed = MagicMock(return_value=True)

    lease_id = "lease123"
    organization_id = "org123"
    subscription = Subscription(organization_id=organization_id, status="ACTIVE", renewal_day_of_month=15)

    with patch("service.transaction.logger.info") as mock_log_info:
        # Act
        service._cancel_lease(lease_id, subscription, organization_id, session)

        # Assert
        service._is_lease_closed.assert_called_once_with(lease_id)
        mock_log_info.assert_called_once_with(
            f"The lease with lease_id='{lease_id}' for the organization {organization_id} had been closed already."
        )


def test_cancel_lease_process():
    # Arrange
    session = MagicMock()
    service = TransactionService(session)
    service._is_lease_closed = MagicMock(return_value=False)
    service.transaction_repository.get_lease_transactions_and_accounts_data = MagicMock()
    service._return_unused_credits = MagicMock()

    lease_id = "lease123"
    organization_id = "org123"
    mock_result = MagicMock()
    service.transaction_repository.get_lease_transactions_and_accounts_data.return_value = [mock_result]

    lease_account_mock = MagicMock()
    lease_account_mock.id = uuid4()
    lease_account_mock.type = CreditAccountType.LEASE
    subscription = Subscription(
        organization_id=organization_id,
        status="ACTIVE",
        renewal_day_of_month=15,
        credit_accounts=[lease_account_mock],
    )

    # Act
    service._cancel_lease(lease_id, subscription, organization_id, session)

    # Assert
    service._is_lease_closed.assert_called_once_with(lease_id)
    service.transaction_repository.get_lease_transactions_and_accounts_data.assert_called_once_with(lease_id)
    service._return_unused_credits.assert_called_once()


def test_get_transactions_no_filters(mock_transaction_repository, transaction_service):
    # Arrange
    organization_id = ORGANIZATION_ID
    skip = 0
    limit = 10
    from_date = int(datetime(2023, 1, 1).timestamp() * 1000)
    to_date = int(datetime(2023, 12, 31).timestamp() * 1000)
    sort = []
    project_id = None
    usage_type = None

    mock_transactions = [
        MagicMock(
            debit=100,
            workspace_id="ws1",
            project_id="pj1",
            service_name="svc1",
            created=from_date + 1000,
        ),
        MagicMock(
            debit=200,
            workspace_id="ws2",
            project_id="pj2",
            service_name="svc2",
            created=from_date + 2000,
        ),
    ]

    mock_transaction_repository.get_transactions.return_value = (2, mock_transactions)

    # Act
    total_matched, transactions = transaction_service.get_transactions(
        organization_id=organization_id,
        skip=skip,
        limit=limit,
        from_date=from_date,
        to_date=to_date,
        sort=sort,
        project_id=project_id,
        usage_type=usage_type,
    )

    # Assert
    assert total_matched == 2
    assert len(transactions) == 2
    assert transactions[0].credits == 100
    assert transactions[1].credits == 200
    mock_transaction_repository.get_transactions.assert_called_once_with(
        organization_id=organization_id,
        skip=skip,
        limit=limit,
        from_date=from_date,
        to_date=to_date,
        sort=sort,
        project_id=project_id,
        usage_type=usage_type,
    )


def test_get_transactions_with_project_id_filter(mock_transaction_repository, transaction_service):
    # Arrange
    organization_id = ORGANIZATION_ID
    skip = 0
    limit = 10
    from_date = int(datetime(2023, 1, 1).timestamp() * 1000)
    to_date = int(datetime(2023, 12, 31).timestamp() * 1000)
    sort = []
    project_id = "proj1"
    usage_type = None

    mock_transactions = [
        MagicMock(
            debit=100,
            workspace_id="ws1",
            project_id="proj1",
            service_name="svc1",
            created=from_date + 1000,
        )
    ]

    mock_transaction_repository.get_transactions.return_value = (1, mock_transactions)

    # Act
    total_matched, transactions = transaction_service.get_transactions(
        organization_id=organization_id,
        skip=skip,
        limit=limit,
        from_date=from_date,
        to_date=to_date,
        sort=sort,
        project_id=project_id,
        usage_type=usage_type,
    )

    # Assert
    assert total_matched == 1
    assert len(transactions) == 1
    assert transactions[0].project_id == "proj1"
    mock_transaction_repository.get_transactions.assert_called_once_with(
        organization_id=organization_id,
        skip=skip,
        limit=limit,
        from_date=from_date,
        to_date=to_date,
        sort=sort,
        project_id=project_id,
        usage_type=usage_type,
    )


def test_get_transactions_with_sorting(mock_transaction_repository, transaction_service):
    # Arrange
    organization_id = ORGANIZATION_ID
    skip = 0
    limit = 10
    from_date = int(datetime(2023, 1, 1).timestamp() * 1000)
    to_date = int(datetime(2023, 12, 31).timestamp() * 1000)
    sort = [("created", "asc")]
    project_id = None
    usage_type = None

    mock_transactions = [
        MagicMock(
            debit=100,
            workspace_id="ws1",
            project_id="proj1",
            service_name="svc1",
            created=from_date + 1000,
        ),
        MagicMock(
            debit=200,
            workspace_id="ws2",
            project_id="proj2",
            service_name="svc2",
            created=from_date + 2000,
        ),
    ]

    mock_transaction_repository.get_transactions.return_value = (2, mock_transactions)

    # Act
    total_matched, transactions = transaction_service.get_transactions(
        organization_id=organization_id,
        skip=skip,
        limit=limit,
        from_date=from_date,
        to_date=to_date,
        sort=sort,
        project_id=project_id,
        usage_type=usage_type,
    )

    # Assert
    assert total_matched == 2
    assert len(transactions) == 2
    assert transactions[0].milliseconds_timestamp <= transactions[1].milliseconds_timestamp
    mock_transaction_repository.get_transactions.assert_called_once_with(
        organization_id=organization_id,
        skip=skip,
        limit=limit,
        from_date=from_date,
        to_date=to_date,
        sort=sort,
        project_id=project_id,
        usage_type=usage_type,
    )


def test_get_transactions_with_limit(mock_transaction_repository, transaction_service):
    # Arrange
    organization_id = ORGANIZATION_ID
    skip = 0
    limit = 1
    from_date = int(datetime(2023, 1, 1).timestamp() * 1000)
    to_date = int(datetime(2023, 12, 31).timestamp() * 1000)
    sort = []
    project_id = None
    usage_type = None

    mock_transactions = [
        MagicMock(
            debit=100,
            workspace_id="ws1",
            project_id="proj1",
            service_name="svc1",
            created=from_date + 1000,
        ),
        MagicMock(
            debit=200,
            workspace_id="ws2",
            project_id="proj2",
            service_name="svc2",
            created=from_date + 2000,
        ),
    ]

    mock_transaction_repository.get_transactions.return_value = (2, mock_transactions[:1])

    # Act
    total_matched, transactions = transaction_service.get_transactions(
        organization_id=organization_id,
        skip=skip,
        limit=limit,
        from_date=from_date,
        to_date=to_date,
        sort=sort,
        project_id=project_id,
        usage_type=usage_type,
    )

    # Ensure we're checking the correct transaction type (debit transaction)
    transactions = [t for t in transactions if t.credits > 0]

    # Assert
    assert total_matched == 2
    assert len(transactions) == 1
    assert transactions[0].credits == 100
    mock_transaction_repository.get_transactions.assert_called_once_with(
        organization_id=organization_id,
        skip=skip,
        limit=limit,
        from_date=from_date,
        to_date=to_date,
        sort=sort,
        project_id=project_id,
        usage_type=usage_type,
    )


def test_get_transactions_with_usage_type_filter(mock_transaction_repository, transaction_service):
    # Arrange
    organization_id = ORGANIZATION_ID
    skip = 0
    limit = 10
    from_date = int(datetime(2023, 1, 1).timestamp() * 1000)
    to_date = int(datetime(2023, 12, 31).timestamp() * 1000)
    sort = []
    project_id = None
    usage_type = "compute"

    mock_transactions = [
        MagicMock(
            debit=100,
            workspace_id="ws1",
            project_id="proj1",
            service_name="svc1",
            created=from_date + 1000,
            usage_type="compute",
        ),
        MagicMock(
            debit=200,
            workspace_id="ws2",
            project_id="proj2",
            service_name="svc2",
            created=from_date + 2000,
            usage_type="storage",
        ),
    ]

    mock_transaction_repository.get_transactions.return_value = (1, [mock_transactions[0]])

    # Act
    total_matched, transactions = transaction_service.get_transactions(
        organization_id=organization_id,
        skip=skip,
        limit=limit,
        from_date=from_date,
        to_date=to_date,
        sort=sort,
        project_id=project_id,
        usage_type=usage_type,
    )

    # Assert
    assert total_matched == 1
    assert len(transactions) == 1
    assert transactions[0].credits == 100
    mock_transaction_repository.get_transactions.assert_called_once_with(
        organization_id=organization_id,
        skip=skip,
        limit=limit,
        from_date=from_date,
        to_date=to_date,
        sort=sort,
        project_id=project_id,
        usage_type=usage_type,
    )


def test_get_transactions_with_date_range(mock_transaction_repository, transaction_service):
    # Arrange
    organization_id = ORGANIZATION_ID
    skip = 0
    limit = 10
    from_date = int(datetime(2023, 6, 1).timestamp() * 1000)
    to_date = int(datetime(2023, 6, 30).timestamp() * 1000)
    sort = []
    project_id = None
    usage_type = None

    mock_transactions = [
        MagicMock(
            debit=100,
            workspace_id="ws1",
            project_id="proj1",
            service_name="svc1",
            created=from_date + 1000,
        ),
        MagicMock(
            debit=200,
            workspace_id="ws2",
            project_id="proj2",
            service_name="svc2",
            created=from_date - 2000,
        ),
    ]

    mock_transaction_repository.get_transactions.return_value = (1, [mock_transactions[0]])

    # Act
    total_matched, transactions = transaction_service.get_transactions(
        organization_id=organization_id,
        skip=skip,
        limit=limit,
        from_date=from_date,
        to_date=to_date,
        sort=sort,
        project_id=project_id,
        usage_type=usage_type,
    )

    # Assert
    assert total_matched == 1
    assert len(transactions) == 1
    assert transactions[0].credits == 100
    mock_transaction_repository.get_transactions.assert_called_once_with(
        organization_id=organization_id,
        skip=skip,
        limit=limit,
        from_date=from_date,
        to_date=to_date,
        sort=sort,
        project_id=project_id,
        usage_type=usage_type,
    )


@pytest.mark.parametrize(
    "keys, projects, raw_data",
    [
        (
            [AggregatesKey.PROJECT],
            None,
            {
                "optional_keys": [AggregatesKey.PROJECT.value],
                "row_data_list": [
                    ("pj0", {"frame": 1, "image": 5}, Decimal("6")),
                    ("pj1", {"frame": 2, "image": 10}, Decimal("12")),
                ],
            },
        ),
        (
            [AggregatesKey.SERVICE_NAME],
            None,
            {
                "optional_keys": [AggregatesKey.SERVICE_NAME.value],
                "row_data_list": [
                    ("service1", {"frame": 10, "image": 10}, Decimal("20")),
                ],
            },
        ),
        (
            [AggregatesKey.DATE],
            None,
            {
                "optional_keys": [AggregatesKey.DATE.value],
                "row_data_list": [
                    (1716300748800, {"frame": 0, "image": 10}, Decimal("10")),
                ],
            },
        ),
        (
            [AggregatesKey.DATE, AggregatesKey.PROJECT],
            ["some"],
            {
                "optional_keys": [AggregatesKey.DATE.value, AggregatesKey.PROJECT.value],
                "row_data_list": [
                    (1716300748800, "pj0", {"frame": 0, "image": 10}, Decimal("10")),
                    (1716300748800, "pj1", {"frame": 0, "image": 10}, Decimal("10")),
                ],
            },
        ),
        (
            [AggregatesKey.PROJECT, AggregatesKey.SERVICE_NAME, AggregatesKey.DATE],
            None,
            {
                "optional_keys": [
                    AggregatesKey.PROJECT.value,
                    AggregatesKey.SERVICE_NAME.value,
                    AggregatesKey.DATE.value,
                ],
                "row_data_list": [
                    ("pj0", "svc0", 1716300748800, {"frame": 1, "image": 5}, Decimal("6")),
                    ("pj1", "svc1", 1716387148800, {"frame": 2, "image": 10}, Decimal("12")),
                ],
            },
        ),
    ],
)
@patch("service.transaction.TransactionRepository")
def test_aggregate_transactions(mock_transaction_repository, aggregate_result_fixture, keys, projects, raw_data):
    # Arrange
    session = MagicMock()
    current_datetime = get_current_datetime()
    from_date = datetime_to_unix_milliseconds(
        current_datetime.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    )
    to_date = datetime_to_unix_milliseconds(current_datetime)

    mocked_aggregation_result = aggregate_result_fixture(raw_data["optional_keys"], raw_data["row_data_list"])
    mock_transaction_repository_instance = mock_transaction_repository.return_value
    mock_transaction_repository_instance.aggregate_transactions.return_value = mocked_aggregation_result

    # Act
    transaction_service = TransactionService(session=session)
    actual_result = transaction_service.aggregate_transactions(
        organization_id=ORGANIZATION_ID, aggregate_keys=keys, from_date=from_date, to_date=to_date, projects=projects
    )

    expected_result = transaction_service._parse_row_to_aggregate_response(
        aggregate_keys=keys, aggregation_result=mocked_aggregation_result
    )

    # Assert
    mock_transaction_repository_instance.aggregate_transactions.assert_called_once_with(
        organization_id=ORGANIZATION_ID, aggregates_keys=keys, from_date=from_date, to_date=to_date, projects=projects
    )
    assert actual_result == expected_result


@pytest.mark.parametrize(
    "resource_dict, expected_result",
    [
        ({}, ResourcesAmount()),
        ({"images": 50}, ResourcesAmount(images=50)),
        ({"frames": 21}, ResourcesAmount(frames=21)),
        ({"images": 20, "frames": 10}, ResourcesAmount(images=20, frames=10)),
        ({"images": 20, "not-existing-key": 10}, ResourcesAmount(images=20)),
        ({"some-key": 20, "frames": 10}, ResourcesAmount(frames=10)),
    ],
)
def test_process_resources_amount(resource_dict, expected_result) -> None:
    session = MagicMock()
    transaction_service = TransactionService(session=session)

    actual_result = transaction_service._process_resources_amount(resources_dict=resource_dict)

    assert actual_result == expected_result


@pytest.mark.parametrize(
    "aggregate_keys, data, expected_result",
    [
        (
            [AggregatesKey.PROJECT],
            [("pj0", {"frames": 1, "images": 5}, Decimal("6"))],
            AggregatesResponse(
                aggregates=[
                    AggregateItem(
                        group=[GroupItem(key="project", value="pj0")],
                        result=AggregatesResult(credits=6, resources=ResourcesAmount(images=5, frames=1)),
                    )
                ]
            ),
        ),
        (
            [AggregatesKey.DATE, AggregatesKey.PROJECT],
            [
                (1716300748800, "pj0", {"frames": 0, "images": 10}, Decimal("10")),
                (1716300748800, "pj1", {"frames": 2, "images": 12}, Decimal("14")),
            ],
            AggregatesResponse(
                aggregates=[
                    AggregateItem(
                        group=[GroupItem(key="date", value=1716300748800), GroupItem(key="project", value="pj0")],
                        result=AggregatesResult(credits=10, resources=ResourcesAmount(images=10, frames=0)),
                    ),
                    AggregateItem(
                        group=[GroupItem(key="date", value=1716300748800), GroupItem(key="project", value="pj1")],
                        result=AggregatesResult(credits=14, resources=ResourcesAmount(images=12, frames=2)),
                    ),
                ]
            ),
        ),
    ],
)
def test_parse_row_to_aggregate_response(aggregate_keys, data, aggregate_result_fixture, expected_result) -> None:
    session = MagicMock()
    optional_keys = [item.value for item in aggregate_keys]
    test_data = aggregate_result_fixture(optional_keys, data)

    transaction_service = TransactionService(session=session)
    actual_result = transaction_service._parse_row_to_aggregate_response(
        aggregate_keys=aggregate_keys, aggregation_result=test_data
    )

    assert actual_result == expected_result
