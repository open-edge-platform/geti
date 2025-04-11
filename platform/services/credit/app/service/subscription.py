# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging
from collections.abc import Callable, Sequence
from uuid import UUID

from sqlalchemy.orm import Session

from db.model import Subscription
from db.model.product import ProductQuota
from db.model.subscription import SubscriptionQuota as SubscriptionQuotaModel
from db.repository.common import advisory_lock, transactional
from db.repository.product import ProductRepository
from db.repository.subscription import SubscriptionQuotaFilters, SubscriptionRepository
from exceptions.custom_exceptions import InvalidStateTransitionException, NoDatabaseResult
from rest.schema.product import Product
from rest.schema.subscription import SubscriptionQuota, SubscriptionResponse
from service.balance import BalanceService
from service.credit_account import CreditAccountDetails, CreditAccountService
from service.product import ProductService
from utils.enums import CreditAccountType, QuotaType, SubscriptionStatus
from utils.time import get_current_day, get_current_milliseconds_timestamp

logger = logging.getLogger(__name__)

# type alias for the state transition handler
StateTransitionHandler = Callable[[Subscription], Subscription]


class SubscriptionService:
    def __init__(self, session: Session):
        self.subscription_repository = SubscriptionRepository(session)
        self.product_repository = ProductRepository(session)
        self.product_svc = ProductService(session)
        self.credit_account_svc = CreditAccountService(session)
        self.balance_service = BalanceService(session)
        self.session = session

        self.state_machine: dict[tuple[str, str], StateTransitionHandler] = {
            (SubscriptionStatus.NEW, SubscriptionStatus.ACTIVE): self._create_handler,
            (SubscriptionStatus.FAILED, SubscriptionStatus.ACTIVE): self._restore_handler,
            (SubscriptionStatus.ACTIVE, SubscriptionStatus.FAILED): self._fail_handler,
            (SubscriptionStatus.ACTIVE, SubscriptionStatus.CANCELLED): self._cancel_handler,
            (SubscriptionStatus.CANCELLED, SubscriptionStatus.ACTIVE): self._resume_handler,
        }

    @staticmethod
    def _fail_handler(subscription: Subscription) -> Subscription:
        """Handles failed state for Subscription status transition"""
        subscription.status = SubscriptionStatus.FAILED
        subscription.updated = get_current_milliseconds_timestamp()
        return subscription

    @staticmethod
    def _cancel_handler(subscription: Subscription) -> Subscription:
        """Transitions a subscription into a cancelled state"""
        subscription.status = SubscriptionStatus.CANCELLED
        subscription.updated = get_current_milliseconds_timestamp()
        return subscription

    def _create_handler(self, subscription: Subscription) -> Subscription:
        """Creates a subscription in an active state and its corresponding asset accounts"""
        product: Product = self.product_svc.get_product_by_id(subscription.product_id)
        subscription.status = SubscriptionStatus.ACTIVE
        new_subscription = self.subscription_repository.create(new_subscription=subscription)

        lease_acc_details = CreditAccountDetails(
            name="Lease account",
            account_type=CreditAccountType.LEASE,
        )
        self.credit_account_svc.create_credit_account(details=lease_acc_details, subscription=new_subscription)

        for policy in product.product_policies:
            asset_acc_details = CreditAccountDetails(
                name=policy.account_name,
                account_type=CreditAccountType.ASSET,
                init_amount=policy.init_amount,
                renewable_amount=policy.renewable_amount,
            )
            if policy.expires_in:
                asset_acc_details.expires = get_current_milliseconds_timestamp() + policy.expires_in
            self.credit_account_svc.create_credit_account(details=asset_acc_details, subscription=new_subscription)
        return new_subscription

    def _restore_handler(self, existing_subscription: Subscription) -> Subscription:
        """Transitions received failed subscription into an active state, updating corresponding asset accounts"""
        product: Product = self.product_svc.get_product_by_id(existing_subscription.product_id)
        existing_subscription.renewal_day_of_month = get_current_day()
        existing_subscription.status = SubscriptionStatus.ACTIVE
        existing_subscription.updated = get_current_milliseconds_timestamp()
        self._update_credit_accounts_expiration(product=product, subscription=existing_subscription)
        return existing_subscription

    @staticmethod
    def _update_credit_accounts_expiration(product: Product, subscription: Subscription) -> None:
        """Updates credit account expiration after previously failed subscription activation"""
        expirable_accounts_policies = [policy for policy in product.product_policies if policy.expires_in is not None]
        for policy in expirable_accounts_policies:
            existing_account = next(
                (account for account in subscription.credit_accounts if account.name == policy.account_name), None
            )
            if existing_account is not None:
                current_time = get_current_milliseconds_timestamp()
                existing_account.expires = current_time + policy.expires_in
                existing_account.updated = current_time

    def _resume_handler(self, subscription: Subscription) -> Subscription:
        """
        Transitions previously cancelled subscription into an active state.
        Resumes usage of its asset accounts.
        Accounts expired before the cancellation are not restored.
        """
        subscription.status = SubscriptionStatus.ACTIVE
        cancellation_time = subscription.updated
        current_time = get_current_milliseconds_timestamp()
        cancelled_balances = self.balance_service.get_credit_accounts_balances(
            subscription=subscription,
            organization_id=subscription.organization_id,
            _db_session=self.session,
            date=cancellation_time,
        )
        current_balances = self.balance_service.get_credit_accounts_balances(
            subscription=subscription,
            organization_id=subscription.organization_id,
            _db_session=self.session,
            date=current_time,
        )

        for account_id, cancelled_balance in cancelled_balances.items():
            current_balance = current_balances.get(account_id)
            if current_balance is None or current_balance.available < cancelled_balance.available:
                credits_amount_to_add = cancelled_balance.available - (
                    current_balance.available if current_balance else 0
                )
                self.credit_account_svc.resume_credit_account(
                    account_id=account_id,
                    cancellation_time=cancellation_time,
                    current_time=current_time,
                    credits_amount=credits_amount_to_add,
                )

        subscription.updated = current_time
        return subscription

    @transactional
    @advisory_lock("organization_id")
    def transition(
        self,
        subscription: Subscription,
        new_status: SubscriptionStatus,
        organization_id: str,  # noqa: ARG002
        _db_session: Session,
    ) -> Subscription:
        """State machine handler, defining the correct action for the requested subscription status"""
        if subscription.status == new_status:
            logger.warning(
                f"Subscription {subscription.id} already has status {subscription.status}. No changes performed."
            )
            return subscription

        handler = self.state_machine.get((subscription.status, new_status))

        if handler is None:
            raise InvalidStateTransitionException(f"Cannot transition from {subscription.status} to '{new_status}'.")

        return handler(subscription)

    def get_active_product_subscription(self, organization_id: str, product_id: UUID) -> Subscription | None:
        """
        Returns existing active subscription for the provided product, or None if no such subscription found
        """
        subscriptions: Sequence[Subscription] = self.subscription_repository.get_by_organization(organization_id)
        return next(
            (sub for sub in subscriptions if sub.product_id == product_id and sub.status == SubscriptionStatus.ACTIVE),
            None,
        )

    def get_active_subscription(self, organization_id: str) -> Subscription | None:
        """
        Returns the organization's active subscription, or None if no such subscription found
        """
        subscriptions: Sequence[Subscription] = self.subscription_repository.get_by_organization(organization_id)
        return next(
            (sub for sub in subscriptions if sub.status == SubscriptionStatus.ACTIVE),
            None,
        )

    def get_current_quotas(
        self,
        organization_id: str,
        subscription_filters: SubscriptionQuotaFilters,
        skip: int = 0,
        limit: int | None = None,
    ) -> tuple[int, list[SubscriptionQuota]]:
        """

        :param organization_id: ID of the organization for which quotas are returned
        :param subscription_filters: Filters containing generic subscription quota parameters like quota_name,
        quota_type, service_name
        :param skip: Pagination parameter - Offsets results by specified amount of quotas
        :param limit: Pagination parameter - Limit the amount of subscription quotas returned
        :return: Number of total matched quotas and list of paginated subscription quotas
        """
        logger.debug(f"Get current quotas request received for {organization_id=} and {subscription_filters=}")
        subscription = self.get_active_subscription(organization_id=organization_id)
        if not subscription:
            error_msg = f"Organization {organization_id=} doesn't have quotas defined yet: no active subscription"
            logger.info(error_msg)
            raise NoDatabaseResult(error_msg)  # wrapped into 404 Not Found by the exception handler

        logger.debug(f"Returned active subscription: {subscription}")
        default_product_quotas = self.product_repository.get_product_quotas(product_id=subscription.product_id)
        logger.debug(f"Returned default product quotas: {default_product_quotas}")

        total_matched, subscription_quotas = self.subscription_repository.get_subscription_quotas(
            subscription, subscription_filters
        )
        logger.debug(f"Retrieved subscription quotas: {subscription_quotas=}")

        result_quotas = []

        # Case where organization doesn't have any subscription quotas defined - returning product quotas
        if subscription_quotas == {}:
            result_quotas.extend(
                [
                    SubscriptionQuota(
                        id=None,
                        organization_id=organization_id,
                        service_name=quota.service_name,
                        quota_name=quota.quota_name,
                        quota_type=quota.quota_type,
                        limit=quota.limit,
                        created=None,
                        updated=None,
                    )
                    for quota in default_product_quotas
                ]
            )
        else:
            result_quotas.extend(subscription_quotas)
            subscription_quotas_types = [sub.quota_type for sub in subscription_quotas]
            for quota in default_product_quotas:
                if quota.quota_type not in subscription_quotas_types:
                    result_quotas.append(quota)

        response = []
        for quota in result_quotas:
            if isinstance(quota, ProductQuota):
                response.append(
                    SubscriptionQuota(
                        id=quota.id,
                        organization_id=organization_id,
                        service_name=quota.service_name,
                        quota_name=quota.quota_name,
                        quota_type=quota.quota_type,
                        limit=quota.limit,
                        created=None,
                        updated=None,
                    )
                )
            else:
                response.append(
                    SubscriptionQuota(
                        id=quota.id,
                        organization_id=organization_id,
                        service_name=quota.service_name,
                        quota_name=quota.quota_name,
                        quota_type=quota.quota_type,
                        limit=quota.limit,
                        created=quota.created,
                        updated=quota.updated,
                    )
                )

        response = sorted(response, key=lambda quota: quota.quota_type)[skip : (skip + (limit or total_matched))]

        return total_matched, response

    def get_org_quota_by_type(self, organization_id: str, quota_type: QuotaType) -> SubscriptionQuota | None:
        """
        Returns the current organization quota of the requested type or None if no such quota exists
        """
        subscription = self.get_active_subscription(organization_id=organization_id)
        if not subscription:
            logger.error(f"Organization {organization_id=} doesn't have quotas defined yet: no active subscription")
            return None

        custom_quota: SubscriptionQuotaModel = self.subscription_repository.get_subscription_quota_by_type(
            subscription_id=subscription.id, quota_type=quota_type
        )
        if not custom_quota:
            default_product_quotas: Sequence[ProductQuota] = self.product_repository.get_product_quotas(
                product_id=subscription.product_id
            )
            default_quota = next((q for q in default_product_quotas if q.quota_type == quota_type), None)
            if not default_quota:
                logger.error(f"Organization {organization_id} doesn't have a quota of type {quota_type}")
                return None
            return SubscriptionQuota(
                organization_id=organization_id,
                service_name=default_quota.service_name,
                quota_name=default_quota.quota_name,
                quota_type=default_quota.quota_type,
                limit=default_quota.limit,
            )

        return SubscriptionQuota(
            id=custom_quota.id,
            organization_id=organization_id,
            service_name=custom_quota.service_name,
            quota_name=custom_quota.quota_name,
            quota_type=custom_quota.quota_type,
            limit=custom_quota.limit,
            created=custom_quota.created,
            updated=custom_quota.updated,
        )

    def get_product_subscription(self, organization_id: str, product_id: UUID) -> Subscription | None:
        """
        Returns existing subscription for the provided product, or None if no such subscription found
        """
        subscriptions: Sequence[Subscription] = self.subscription_repository.get_by_organization(organization_id)
        return next(
            (sub for sub in subscriptions if sub.product_id == product_id),
            None,
        )

    def get_product_subscriptions(self, organization_id: str, product_id: UUID) -> Sequence[Subscription]:
        """
        Returns existing organization's subscriptions for the provided product.
        Normally there's only one organization subscription per one product,
        this method is only used in a migration script
        """
        subscriptions: Sequence[Subscription] = self.subscription_repository.get_by_organization(organization_id)
        return [sub for sub in subscriptions if sub.product_id == product_id]

    def get_all_org_subscriptions(
        self, organization_id: str, skip: int, limit: int
    ) -> tuple[int, list[SubscriptionResponse]]:
        """
        Returns the total number of all subscriptions, belonging to the specified organization,
         and a limited list of these subscriptions
        """
        subscriptions: Sequence[Subscription] = self.subscription_repository.get_by_organization(organization_id)
        total_matched = len(subscriptions)
        result_subscriptions = subscriptions[skip : skip + limit]

        result_response = []
        for sub in result_subscriptions:
            subscription_response = SubscriptionResponse(
                id=sub.id,
                organization_id=sub.organization_id,
                workspace_id=sub.workspace_id,
                product_id=sub.product_id,
                status=sub.status,
                created=sub.created,
                updated=sub.updated,
            )
            if sub.status == SubscriptionStatus.ACTIVE:
                subscription_response.next_renewal_date = sub.next_renewal_date
                subscription_response.previous_renewal_date = (
                    sub.previous_renewal_date if sub.previous_renewal_date > sub.updated else None
                )
            result_response.append(subscription_response)

        return total_matched, result_response

    def _create_organization_subscription_quota(
        self,
        _db_session: Session,
        subscription_uuid: UUID,
        service_name: str,
        quota_type: str,
        quota_name: str,
        limit: int,
    ) -> SubscriptionQuotaModel:
        logger.debug("Create a new subscription quota for subscription with id: %s", subscription_uuid)
        subscription_quota = SubscriptionQuotaModel(
            subscription_id=subscription_uuid,
            service_name=service_name,
            quota_type=quota_type,
            quota_name=quota_name,
            limit=limit,
        )
        self.subscription_repository.create_subscription_quota(subscription_quota=subscription_quota)
        logger.debug(f"Organization quota was successfully created with ID: {subscription_quota.id}")

        return subscription_quota

    @transactional
    @advisory_lock("quota_lock")
    def provisioning_organization_subscription_quota(
        self,
        _db_session: Session,
        subscription: Subscription,
        quota_lock: str,  # noqa: ARG002
        service_name: str,
        quota_name: str,
        quota_type: QuotaType,
        limit: int,
    ) -> SubscriptionQuotaModel:
        subscription_quota = self.subscription_repository.get_subscription_quota_by_type(
            subscription_id=subscription.id, quota_type=quota_type
        )

        if subscription_quota:
            logger.debug(f"Trying to update the subscription quota with ID: {subscription_quota.id}")
            subscription_quota.service_name = service_name
            subscription_quota.quota_name = quota_name
            subscription_quota.limit = limit

            logger.info(
                f"Quota for the organization {subscription.organization_id} has been updated: {service_name=},"
                f"{quota_type=}, {quota_name=}, new {limit=}"
            )
            return subscription_quota

        logger.debug(f"Trying to create a new subscription quota for organization ID: {subscription.organization_id}")
        subscription_quota = self._create_organization_subscription_quota(
            _db_session=_db_session,
            subscription_uuid=subscription.id,
            service_name=service_name,
            quota_name=quota_name,
            quota_type=quota_type,
            limit=limit,
        )
        logger.info(
            f"Quota for the organization {subscription.organization_id} has been created: {service_name=},"
            f"{quota_type=}, {quota_name=}, new {limit=}"
        )
        return subscription_quota
