# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.orm import Session

from db.model import Subscription
from db.model.credit_account import CreditAccount
from db.repository.account import AccountRepository
from db.repository.common import advisory_lock, transactional
from db.repository.subscription import SubscriptionRepository
from rest.schema.balance import BalanceResponse
from rest.schema.credit_accounts import CreditAccount as CreditAccountSchema
from service.balance import BalanceService
from service.transaction import TransactionService
from utils.enums import CreditAccountType
from utils.renewal_date_calculation import get_next_renewal_date, get_renewal_days
from utils.time import get_current_milliseconds_timestamp, unix_milliseconds_to_date
from utils.validation import is_whitespace_or_empty_string

logger = logging.getLogger(__name__)


@dataclass
class CreditAccountDetails:
    name: str
    account_type: CreditAccountType
    init_amount: int | None = None
    renewable_amount: int | None = None
    expires: int | None = None


class CreditAccountService:
    def __init__(self, session: Session):
        self.session = session
        self.credit_account_repository = AccountRepository(session=session)
        self.balance_service = BalanceService(session=session)
        self.subscription_repository = SubscriptionRepository(session=session)
        self.transaction_service = TransactionService(session=session)

    @staticmethod
    def _validate_expiration_timestamp(expiration_timestamp: int) -> None:
        current_milliseconds_timestamp = get_current_milliseconds_timestamp()
        if expiration_timestamp < current_milliseconds_timestamp:
            error_message = (
                "Invalid expiration timestamp. "
                f"The passed value: {expiration_timestamp} should be greater than: {current_milliseconds_timestamp}"
            )
            raise ValueError(error_message)

    @transactional
    def _create_account(self, details: CreditAccountDetails, subscription: Subscription, _db_session: Session) -> UUID:
        new_account = CreditAccount(
            subscription_id=subscription.id,
            name=details.name,
            type=details.account_type,
            renewable_amount=details.renewable_amount,
            expires=details.expires,
        )
        self.credit_account_repository.create(credit_account=new_account)
        if details.account_type == CreditAccountType.ASSET and details.init_amount:
            logger.debug(
                f"Adding the initial amount of credits: {details.init_amount} to the account: {new_account.id}"
            )
            self.transaction_service.fill_account(
                receiver_acc_id=new_account.id,
                amount=details.init_amount,
                _db_session=self.session,
                organization_id=subscription.organization_id,
            )
        return new_account.id

    def create_credit_account(self, details: CreditAccountDetails, subscription: Subscription) -> UUID:
        """
        Create a new credit account for specified credit account details
        """
        if details.expires is not None:
            self._validate_expiration_timestamp(expiration_timestamp=details.expires)

        return self._create_account(details=details, subscription=subscription, _db_session=self.session)

    def _update_account(
        self,
        account: CreditAccount,
        name: str,
        renewable_amount: int | None = None,
        expires: int | None = None,
    ) -> CreditAccountSchema:
        account.name = name
        account.expires = expires if expires is not None else account.expires
        account.renewable_amount = renewable_amount if renewable_amount is not None else account.renewable_amount

        # todo: do we need to return balance on update?
        accounts_balances = self.balance_service.get_credit_accounts_balances(
            subscription=account.subscription,
            organization_id=account.subscription.organization_id,
            date=get_current_milliseconds_timestamp(),
            _db_session=self.session,
        )

        result_response = CreditAccountSchema(
            id=account.id,
            organization_id=account.subscription.organization_id,
            name=account.name,
            renewable_amount=account.renewable_amount,
            created=account.created,
            updated=account.updated,
            balance=accounts_balances.get(account.id, BalanceResponse(available=0, incoming=0, blocked=0)),
            expires=expires,
        )
        if account.renewable_amount is not None and account.renewable_amount > 0:
            result_response.renewal_day_of_month = unix_milliseconds_to_date(account.subscription.next_renewal_date).day

        return result_response

    @transactional
    @advisory_lock("organization_id")
    def update_credit_account(
        self,
        _db_session: Session,
        account_id: UUID,
        organization_id: str,
        name: str,
        renewable_amount: int | None = None,
        expires: int | None = None,
    ) -> CreditAccountSchema:
        if is_whitespace_or_empty_string(input_str=name):
            raise ValueError("Passed name of credit account cannot be empty.")
        if expires is not None:
            self._validate_expiration_timestamp(expiration_timestamp=expires)

        account = self.credit_account_repository.get_account(account_id=account_id)
        if renewable_amount is not None and not account.renewable_amount:
            error_message = (
                f"Cannot set {renewable_amount=} for the credit account {account.name} "
                f"with id {account.id} and organization id {organization_id}: account is not renewable."
            )
            raise ValueError(error_message)

        return self._update_account(account=account, name=name, renewable_amount=renewable_amount, expires=expires)

    def _get_organization_accounts_list(
        self,
        subscription: Subscription,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[int, list[CreditAccountSchema]]:
        total_count, organization_accounts = self.credit_account_repository.get_organization_accounts(
            subscription_id=subscription.id, skip=skip, limit=limit
        )
        subscription_renewal_day = unix_milliseconds_to_date(subscription.next_renewal_date).day

        response = []
        accounts_balances = self.balance_service.get_credit_accounts_balances(
            subscription=subscription,
            organization_id=subscription.organization_id,
            _db_session=self.session,
            date=get_current_milliseconds_timestamp(),
        )

        for account in organization_accounts:
            credit_account_response = CreditAccountSchema(
                id=account.id,
                organization_id=subscription.organization_id,
                name=account.name,
                renewable_amount=account.renewable_amount,
                created=account.created,
                updated=account.updated,
                expires=account.expires,
                balance=accounts_balances.get(account.id, BalanceResponse(available=0, incoming=0, blocked=0)),
            )
            if account.renewable_amount is not None and account.renewable_amount > 0:
                credit_account_response.renewal_day_of_month = subscription_renewal_day

            response.append(credit_account_response)

        return total_count, response

    def get_organization_accounts(
        self,
        subscription: Subscription,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[int, list[CreditAccountSchema]]:
        if skip < 0 or limit < 0:
            raise ValueError("skip and limit must be non-negative.")
        return self._get_organization_accounts_list(subscription=subscription, skip=skip, limit=limit)

    @transactional
    @advisory_lock("organization_id")
    def _rollover_subscription(
        self,
        _db_session: Session,
        organization_id: str,
        subscription: Subscription,
        renewal_date: int,
    ):
        next_cycle_start_date = get_next_renewal_date(
            subscription.renewal_day_of_month, unix_milliseconds_to_date(renewal_date)
        )
        logger.debug(
            f"Rolling over the subscription for the organization: {organization_id}."
            f"The subscription cycle start date: {next_cycle_start_date}"
        )

        renewable_accounts = self.credit_account_repository.get_renewable_asset_accounts(
            expiration_threshold=next_cycle_start_date, subscription_id=subscription.id
        )
        # If a renewable account has not been rolled over, its incoming balance should be zero.
        balance = self.balance_service.get_credit_accounts_balances(
            subscription=subscription,
            organization_id=organization_id,
            _db_session=self.session,
            date=next_cycle_start_date,
        )
        for account in renewable_accounts:
            if balance.get(account.id) is not None:
                logger.debug(
                    f"Account {account.id} has already been rolled over on date: {next_cycle_start_date}, skipping"
                )
                continue

            self.transaction_service.fill_account(
                receiver_acc_id=account.id,
                amount=account.renewable_amount,
                created=next_cycle_start_date,
                _db_session=_db_session,
                organization_id=organization_id,
            )

    def rollover_credit_accounts(self, start_date_time: int, end_date_time: int, renewal_date: int) -> None:
        """
        Performs credit accounts renewal.
        Processes accounts where current month's renewal date falls into the desired time range.
        """

        renewal_days = get_renewal_days(start_date_time, end_date_time)
        subscriptions = self.subscription_repository.get_subscriptions_by_renewal_dates_range(renewal_days)

        for subscription in subscriptions:
            self._rollover_subscription(
                _db_session=self.session,
                organization_id=subscription.organization_id,
                subscription=subscription,
                renewal_date=renewal_date,
            )

    def resume_credit_account(
        self, account_id: UUID, cancellation_time: int, current_time: int, credits_amount: int
    ) -> None:
        """
        Method intended to be used during activation of a previously cancelled subscription.
        Extends credit account's expiration time (if applicable) and
        ensures the balance available during the cancellation is restored.
        """
        account = self.credit_account_repository.get_account(account_id=account_id)
        if account.expires and account.expires > cancellation_time:
            account.expires += current_time - cancellation_time
            account.updated = current_time
        self.transaction_service.fill_account(
            receiver_acc_id=account.id,
            amount=credits_amount,
            _db_session=self.session,
            organization_id=account.subscription.organization_id,
        )
