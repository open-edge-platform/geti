# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging
from collections.abc import Mapping
from uuid import UUID

from sqlalchemy.orm import Session

from db.model.subscription import Subscription
from db.repository.account import AccountRepository
from db.repository.balance import AccountBalanceData, BalanceRepository
from db.repository.common import advisory_lock, transactional
from db.repository.subscription import SubscriptionRepository
from rest.schema.balance import BalanceResponse
from utils.renewal_date_calculation import get_prev_renewal_date
from utils.time import get_current_milliseconds_timestamp, unix_milliseconds_to_date

logger = logging.getLogger(__name__)


class BalanceService:
    def __init__(self, session: Session):
        self.session = session
        self.balance_repository = BalanceRepository(session)
        self.account_repository = AccountRepository(session)
        self.subscription_repository = SubscriptionRepository(session)

    @transactional
    @advisory_lock("organization_id")
    def get_credit_accounts_balances(
        self,
        subscription: Subscription,
        organization_id: str,
        _db_session: Session,
        date: int | None = None,
    ) -> Mapping[UUID, BalanceResponse]:
        """Returns list of credit accounts containing calculated balances that belong to specified organization"""
        if not date:
            date = get_current_milliseconds_timestamp()

        prev_renewal_date = get_prev_renewal_date(
            renewal_day=subscription.renewal_day_of_month, current_date=unix_milliseconds_to_date(date)
        )
        logger.debug(
            f"Calculating balance for organisation_id:{organization_id}, "
            f"date: {date}, subscription cycle start date: {prev_renewal_date}"
        )

        account_balances = self.balance_repository.get_balance(
            subscription_id=subscription.id, current_date=date, cycle_start_date=prev_renewal_date
        )

        result = {
            acc_id: BalanceResponse(available=available, incoming=incoming, blocked=blocked)
            for (acc_id, incoming, available, blocked) in account_balances
        }

        logger.debug(
            f"Calculated balance for organisation_id:{organization_id}, "
            f"date: {date}, subscription cycle start date: {prev_renewal_date}"
            f"balance: {result}"
        )

        return result

    def get_organization_balance(self, active_subscription: Subscription, date: int | None = None) -> BalanceResponse:
        account_balances = self.get_credit_accounts_balances(
            subscription=active_subscription,
            organization_id=active_subscription.organization_id,
            _db_session=self.session,
            date=date,
        )
        total_incoming = 0
        total_available = 0
        total_blocked = 0

        for balance in account_balances.values():
            total_incoming += balance.incoming
            total_available += balance.available
            total_blocked += balance.blocked
        return BalanceResponse(incoming=total_incoming, available=total_available, blocked=total_blocked)

    @transactional
    @advisory_lock("organization_id")
    def create_organization_snapshot(
        self, _db_session: Session, subscription: Subscription, organization_id: str
    ) -> None:
        """
        Create a balance snapshot for a specific organization.
        """
        # Fetch balances
        # todo: pass a date parameter to support time travel requests

        logger.debug(f"Creating balance snapshot for organisation_id:{organization_id}")
        account_balances = self.get_credit_accounts_balances(
            subscription=subscription, organization_id=organization_id, _db_session=self.session
        )
        new_snapshot = self.balance_repository.create_snapshot(subscription_id=subscription.id)

        details = [
            AccountBalanceData(
                snapshot_id=new_snapshot.id,
                account_id=account_id,
                available_balance=balance.available,
                incoming_balance=balance.incoming,
            )
            for (account_id, balance) in account_balances.items()
        ]

        self.balance_repository.create_balance(details)
        logger.debug(f"Balance snapshot for organisation_id has been created :{organization_id}")

    def create_organization_snapshots(self, _db_session: Session) -> None:
        """
        Creates Balance snapshots for all accounts
        """
        active_subscriptions = self.subscription_repository.get_all_active_subscriptions()
        for subscription in active_subscriptions:
            self.create_organization_snapshot(
                _db_session=_db_session, subscription=subscription, organization_id=subscription.organization_id
            )
