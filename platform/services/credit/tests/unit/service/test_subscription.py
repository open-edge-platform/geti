# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from unittest.mock import MagicMock, call, patch
from uuid import UUID, uuid4

import pytest

from db.model.product import ProductQuota
from db.model.subscription import SubscriptionQuota as SubscriptionQuotaModel
from db.repository.subscription import Subscription
from exceptions.custom_exceptions import InvalidStateTransitionException
from rest.schema.product import Product, ProductPolicy
from rest.schema.subscription import SubscriptionQuota as SubscriptionQuotaResponse
from service.subscription import SubscriptionRepository, SubscriptionService
from utils.enums import QuotaType, SubscriptionStatus

ORGANIZATION_ID = "000000000000000000000001"


@pytest.mark.parametrize(
    "expected_result, subscriptions",
    [
        (None, []),
        (
            Subscription(
                id=UUID("96ace5cf-c999-4f31-ab91-9edb8d9d560a"),
                organization_id=ORGANIZATION_ID,
                product_id=UUID("920c0c85-70d2-4d53-a25f-80db9ec4c2fc"),
                renewal_day_of_month=22,
                status=SubscriptionStatus.ACTIVE,
                created=12345,
                updated=12345,
            ),
            [
                Subscription(
                    id=UUID("96ace5cf-c999-4f31-ab91-9edb8d9d560a"),
                    organization_id=ORGANIZATION_ID,
                    product_id=UUID("920c0c85-70d2-4d53-a25f-80db9ec4c2fc"),
                    renewal_day_of_month=22,
                    status=SubscriptionStatus.ACTIVE,
                    created=12345,
                    updated=12345,
                ),
                Subscription(
                    id=UUID("a061d423-ee7a-455a-8768-922e03a80b9a"),
                    organization_id=ORGANIZATION_ID,
                    product_id=UUID("999c0c85-70d2-4d53-a25f-80db9ec4c222"),
                    renewal_day_of_month=15,
                    status=SubscriptionStatus.CANCELLED,
                    created=12345,
                    updated=12345,
                ),
            ],
        ),
    ],
    ids=["No active subscriptions", "One active subscription"],
)
@patch("service.subscription.SubscriptionRepository")
def test_get_active_product_subscription(mock_subscription_repo, expected_result, subscriptions) -> None:
    # Arrange
    session = MagicMock()
    subscription_repo = MagicMock()

    subscription_repo.get_by_organization.return_value = subscriptions
    mock_subscription_repo.return_value = subscription_repo
    subscription_service = SubscriptionService(session)

    # Act
    result = subscription_service.get_active_product_subscription(
        organization_id=ORGANIZATION_ID, product_id=UUID("920c0c85-70d2-4d53-a25f-80db9ec4c2fc")
    )

    # Assert
    if result:
        assert result.id == expected_result.id
        assert result.organization_id == expected_result.organization_id
        assert result.product_id == expected_result.product_id
        assert result.status == expected_result.status
    else:
        assert result == expected_result


@patch("service.subscription.SubscriptionRepository")
@patch("service.subscription.ProductService")
@patch("service.subscription.CreditAccountService")
def test_create_handler(mock_credit_account_svc, mock_product_svc, mock_subscription_repo) -> None:
    # Arrange
    session = MagicMock()

    def _get_product_by_id(prod_id):
        return Product(
            id=prod_id,
            name="Default product",
            product_policies=[
                ProductPolicy(account_name="Welcoming", init_amount=1000, renewable_amount=0, expires_in=12345),
                ProductPolicy(account_name="Freemium", init_amount=0, renewable_amount=100),
            ],
            created=12345,
            updated=12345,
        )

    product_svc = MagicMock()
    product_svc.get_product_by_id.side_effect = _get_product_by_id
    mock_product_svc.return_value = product_svc

    def _create(new_subscription: Subscription):
        new_subscription.id = uuid4()
        return new_subscription

    subscription_repo = MagicMock()
    subscription_repo.create.side_effect = _create
    mock_subscription_repo.return_value = subscription_repo

    credit_account_svc = MagicMock()
    credit_account_svc.create_credit_account.return_value = "new_acc_id"
    mock_credit_account_svc.return_value = credit_account_svc

    subscription_service = SubscriptionService(session)

    # Act
    subscription = Subscription(
        organization_id=ORGANIZATION_ID,
        renewal_day_of_month=12,
        product_id=uuid4(),
        status=SubscriptionStatus.NEW,
    )
    result_subscription = subscription_service._create_handler(subscription)

    # Assert
    subscription_repo.create.assert_called_once()
    assert result_subscription.status == SubscriptionStatus.ACTIVE
    assert credit_account_svc.create_credit_account.call_count == 3


@patch("service.subscription.BalanceService")
@patch("service.subscription.CreditAccountService")
def test_resume_handler(mock_credit_account_svc, mock_balance_svc) -> None:
    # Arrange
    session = MagicMock()
    balance_svc = MagicMock()
    credit_account_svc = MagicMock()
    current_time = 7654321
    cancellation_time = 7000001

    subscription = Subscription(
        organization_id=ORGANIZATION_ID,
        renewal_day_of_month=12,
        product_id=uuid4(),
        status=SubscriptionStatus.CANCELLED,
        updated=cancellation_time,
    )

    cancelled_balances = {
        "account1": MagicMock(available=100),
        "account2": MagicMock(available=200),
        "account3": MagicMock(available=300),
    }
    current_balances = {
        "account1": MagicMock(available=50),  # less than cancelled
        "account2": MagicMock(available=250),  # more than cancelled, should not trigger resume
        # 'account3' is missing (expired in the meantime), should trigger resume with full amount
    }

    balance_svc.get_credit_accounts_balances.side_effect = (
        lambda subscription, organization_id, _db_session, date: cancelled_balances
        if date == subscription.updated
        else current_balances
    )
    mock_balance_svc.return_value = balance_svc
    mock_credit_account_svc.return_value = credit_account_svc

    subscription_service = SubscriptionService(session)

    with patch("service.subscription.get_current_milliseconds_timestamp") as timestamp_mock:
        timestamp_mock.return_value = current_time

        result_subscription = subscription_service._resume_handler(subscription)

        assert result_subscription.status == SubscriptionStatus.ACTIVE
        expected_calls = [
            call(
                account_id="account1",
                cancellation_time=cancellation_time,
                current_time=current_time,
                credits_amount=50,
            ),
            call(
                account_id="account3",
                cancellation_time=cancellation_time,
                current_time=current_time,
                credits_amount=300,
            ),
        ]
        credit_account_svc.resume_credit_account.assert_has_calls(expected_calls, any_order=True)
        assert credit_account_svc.resume_credit_account.call_count == 2
        assert result_subscription.updated == current_time


@pytest.mark.parametrize("target_state", [SubscriptionStatus.FAILED, SubscriptionStatus.CANCELLED])
def test_transition_from_active(target_state):
    # Arrange
    session = MagicMock()
    mock_subscription = Subscription(
        id=uuid4(),
        organization_id=ORGANIZATION_ID,
        product_id=uuid4(),
        renewal_day_of_month=22,
        status=SubscriptionStatus.ACTIVE,
        created=12345,
        updated=12345,
    )
    subscription_service = SubscriptionService(session)

    # Act
    updated_subscription = subscription_service.transition(
        subscription=mock_subscription,
        new_status=target_state,
        organization_id=ORGANIZATION_ID,
        _db_session=session,
    )

    # Assert
    assert updated_subscription.status == target_state


@patch("service.subscription.SubscriptionRepository")
@patch("service.subscription.ProductService")
def test_transition_failed_into_active(mock_product_svc, mock_subscription_repo):
    # Arrange
    session = MagicMock()
    product_id = uuid4()
    mock_subscription = Subscription(
        id=uuid4(),
        organization_id=ORGANIZATION_ID,
        product_id=product_id,
        renewal_day_of_month=22,
        status=SubscriptionStatus.FAILED,
        created=12345,
        updated=12345,
    )

    subscription_repo = MagicMock()
    subscription_repo._update_credit_accounts_expiration.return_value = None
    product_svc = MagicMock()
    product_svc.get_product_by_id.return_value = Product(
        id=product_id, name="Default product", product_policies=[], created=123, updated=123
    )
    mock_subscription_repo.return_value = subscription_repo
    mock_product_svc.return_value = product_svc

    subscription_service = SubscriptionService(session)

    # Act
    updated_subscription = subscription_service.transition(
        subscription=mock_subscription,
        new_status=SubscriptionStatus.ACTIVE,
        organization_id=ORGANIZATION_ID,
        _db_session=session,
    )

    # Assert
    assert updated_subscription.status == SubscriptionStatus.ACTIVE


@patch("service.subscription.SubscriptionService._create_handler")
def test_transition_new_into_active(mock_subscription_create):
    # Arrange
    session = MagicMock()
    mock_subscription = Subscription(
        id=uuid4(),
        organization_id=ORGANIZATION_ID,
        product_id=uuid4(),
        status=SubscriptionStatus.NEW,
    )
    subscription_service = SubscriptionService(session)

    # Act
    subscription_service.transition(
        subscription=mock_subscription,
        new_status=SubscriptionStatus.ACTIVE,
        organization_id=ORGANIZATION_ID,
        _db_session=session,
    )

    # Assert
    mock_subscription_create.assert_called_once_with(mock_subscription)


@patch("service.subscription.CreditAccountService")
@patch("service.subscription.SubscriptionRepository")
def test_invalid_transition(mock_subscription_repo, mock_credit_account_svc):
    # Arrange
    session = MagicMock()
    mock_subscription = Subscription(
        id=uuid4(),
        organization_id=ORGANIZATION_ID,
        product_id=uuid4(),
        renewal_day_of_month=22,
        status=SubscriptionStatus.CANCELLED,
        created=12345,
        updated=12345,
    )

    subscription_repo = MagicMock()
    credit_account_svc = MagicMock()
    mock_subscription_repo.return_value = subscription_repo
    mock_credit_account_svc.return_value = credit_account_svc

    subscription_service = SubscriptionService(session)

    # Act & Assert
    with pytest.raises(InvalidStateTransitionException, match="Cannot transition from CANCELLED to 'FAILED'."):
        subscription_service.transition(
            subscription=mock_subscription,
            new_status=SubscriptionStatus.FAILED,
            organization_id=ORGANIZATION_ID,
            _db_session=session,
        )


def test_create_organization_quota() -> None:
    # Arrange
    session = MagicMock()
    subscription_service = SubscriptionService(session)
    subscription_quota = SubscriptionQuotaModel(
        subscription_id=uuid4(),
        service_name="service_name",
        quota_name="quota_name",
        quota_type=QuotaType.MAX_USERS_COUNT,
        limit=100,
    )

    # Act
    with patch.object(SubscriptionRepository, "create_subscription_quota", autospec=True) as mock_subscription_repo:
        result = subscription_service._create_organization_subscription_quota(
            _db_session=session,
            subscription_uuid=subscription_quota.subscription_id,
            service_name=subscription_quota.service_name,
            quota_name=subscription_quota.quota_name,
            quota_type=subscription_quota.quota_type,
            limit=subscription_quota.limit,
        )

    # Assert
    assert result.subscription_id == subscription_quota.subscription_id
    assert result.service_name == subscription_quota.service_name
    assert result.quota_name == subscription_quota.quota_name
    assert result.quota_type == subscription_quota.quota_type
    assert result.limit == subscription_quota.limit
    mock_subscription_repo.assert_called_once()


def test_update_subscription_quota(organization_id) -> None:
    # Arrange
    session = MagicMock()
    subscription_service = SubscriptionService(session)
    mock_subscription = Subscription(
        id=uuid4(),
        organization_id=organization_id,
        product_id=uuid4(),
        renewal_day_of_month=22,
        status=SubscriptionStatus.ACTIVE,
        created=12345,
        updated=12345,
    )
    subscription_quota = SubscriptionQuotaModel(
        subscription_id=mock_subscription.id,
        service_name="service_name",
        quota_name="quota_name",
        quota_type=QuotaType.MAX_TRAINING_JOBS,
        limit=10,
    )
    updated_subscription_quota = SubscriptionQuotaModel(
        subscription_id=mock_subscription.id,
        service_name="new_service_name",
        quota_name="new_quota_name",
        quota_type=QuotaType.MAX_TRAINING_JOBS,
        limit=100,
    )

    # Act
    with patch.object(
        SubscriptionRepository, "get_subscription_quota_by_type", autospec=True
    ) as mock_subscription_quota:
        mock_subscription_quota.return_value = subscription_quota
        quota_lock = f"{organization_id}_{subscription_quota.quota_type}"
        result = subscription_service.provisioning_organization_subscription_quota(
            _db_session=session,
            subscription=mock_subscription,
            quota_lock=quota_lock,
            service_name=updated_subscription_quota.service_name,
            quota_type=updated_subscription_quota.quota_type,
            quota_name=updated_subscription_quota.quota_name,
            limit=updated_subscription_quota.limit,
        )

    # Assert
    assert result.service_name == updated_subscription_quota.service_name
    assert result.quota_name == updated_subscription_quota.quota_name
    assert result.limit == updated_subscription_quota.limit
    mock_subscription_quota.assert_called_once()


@pytest.mark.parametrize(
    "subscription, custom_quota, default_quotas, expected_result",
    [
        (None, None, [], None),
        (
            Subscription(
                id=UUID("96ace5cf-c999-4f31-ab91-9edb8d9d560a"),
                organization_id=ORGANIZATION_ID,
                product_id=UUID("920c0c85-70d2-4d53-a25f-80db9ec4c2fc"),
                renewal_day_of_month=12,
                status=SubscriptionStatus.ACTIVE,
                created=12345,
                updated=12345,
            ),
            None,
            [],
            None,
        ),
        (
            Subscription(
                id=UUID("96ace5cf-c999-4f31-ab91-9edb8d9d560a"),
                organization_id=ORGANIZATION_ID,
                product_id=UUID("920c0c85-70d2-4d53-a25f-80db9ec4c2fc"),
                renewal_day_of_month=12,
                status=SubscriptionStatus.ACTIVE,
                created=12345,
                updated=12345,
            ),
            None,
            [
                ProductQuota(
                    product_id=UUID("920c0c85-70d2-4d53-a25f-80db9ec4c2fc"),
                    service_name="trainings",
                    quota_name="Max number of concurrent training jobs",
                    quota_type="MAX_TRAINING_JOBS",
                    limit=10,
                )
            ],
            SubscriptionQuotaResponse(
                id=None,
                organization_id=ORGANIZATION_ID,
                service_name="trainings",
                quota_name="Max number of concurrent training jobs",
                quota_type="MAX_TRAINING_JOBS",
                limit=10,
                created=None,
                updated=None,
            ),
        ),
        (
            Subscription(
                id=UUID("96ace5cf-c999-4f31-ab91-9edb8d9d560a"),
                organization_id=ORGANIZATION_ID,
                product_id=UUID("920c0c85-70d2-4d53-a25f-80db9ec4c2fc"),
                renewal_day_of_month=12,
                status=SubscriptionStatus.ACTIVE,
                created=12345,
                updated=12345,
            ),
            SubscriptionQuotaModel(
                id=UUID("96ace5cf-c999-7777-aaaa-9edb8d9d560a"),
                subscription_id=UUID("96ace5cf-c999-4f31-ab91-9edb8d9d560a"),
                service_name="jobs microservice",
                quota_name="Updated max number of concurrent training jobs",
                quota_type="MAX_TRAINING_JOBS",
                limit=50,
                created=12092024,
                updated=12092024,
            ),
            [
                ProductQuota(
                    product_id=UUID("920c0c85-70d2-4d53-a25f-80db9ec4c2fc"),
                    service_name="trainings",
                    quota_name="Max number of concurrent training jobs",
                    quota_type="MAX_TRAINING_JOBS",
                    limit=10,
                )
            ],
            SubscriptionQuotaResponse(
                id=UUID("96ace5cf-c999-7777-aaaa-9edb8d9d560a"),
                organization_id=ORGANIZATION_ID,
                service_name="jobs microservice",
                quota_name="Updated max number of concurrent training jobs",
                quota_type="MAX_TRAINING_JOBS",
                limit=50,
                created=12092024,
                updated=12092024,
            ),
        ),
    ],
    ids=["No active subscriptions", "No default quotas", "No custom quota", "Custom quota"],
)
@patch("service.subscription.SubscriptionRepository.get_subscription_quota_by_type")
@patch("service.subscription.ProductRepository.get_product_quotas")
@patch("service.subscription.SubscriptionService.get_active_subscription")
def test_get_org_quota_by_type(
    mock_get_subscription,
    mock_product_repo,
    mock_subscription_repo,
    subscription,
    custom_quota,
    default_quotas,
    expected_result,
):
    # Arrange
    session = MagicMock()
    subscription_service = SubscriptionService(session)
    mock_get_subscription.return_value = subscription
    mock_product_repo.return_value = default_quotas
    mock_subscription_repo.return_value = custom_quota

    # Act
    result = subscription_service.get_org_quota_by_type(
        organization_id=ORGANIZATION_ID, quota_type=QuotaType.MAX_TRAINING_JOBS
    )

    # Assert
    assert result == expected_result
    mock_get_subscription.assert_called_once_with(organization_id=ORGANIZATION_ID)
