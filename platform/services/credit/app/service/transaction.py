# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging
import sys
from typing import TYPE_CHECKING, NamedTuple
from uuid import UUID, uuid4

from sqlalchemy import Row
from sqlalchemy.orm import Session

from db.model.credit_account import CreditAccount
from db.model.subscription import Subscription
from db.repository.account import AccountRepository
from db.repository.common import advisory_lock, transactional
from db.repository.subscription import SubscriptionRepository
from db.repository.transaction import TransactionDetails, TransactionRepository
from exceptions.custom_exceptions import InsufficientBalanceException, NoDatabaseResult
from kafka_events.message import MeteringEvent
from rest.schema.balance import BalanceResponse
from rest.schema.transactions import (
    AggregateItem,
    AggregatesResponse,
    AggregatesResult,
    GroupItem,
    ResourcesAmount,
    TransactionInfo,
)
from service.balance import BalanceService
from utils.enums import AggregatesKey, CreditAccountType
from utils.renewal_date_calculation import get_next_renewal_date
from utils.time import date_to_unix_milliseconds, get_current_date, get_current_milliseconds_timestamp

if TYPE_CHECKING:
    from sqlalchemy import Result

logger = logging.getLogger(__name__)


class LeaseCreditsRecord(NamedTuple):
    credit: int
    created: int
    project_id: str | None
    service_name: str
    account_id: UUID


class LeaseRequestData(NamedTuple):
    service_name: str
    requests: dict
    project_id: str | None


def _sort_key(credit_account: CreditAccount, renewal_day: int) -> int:
    """
    Generate a sort key for a given credit account based on its expiration and renewal dates.

    This function determines the smallest upcoming timestamp at which the account will require action,
    either due to expiration or renewal. The logic proceeds as follows:

    1. If the account has an expiration date, it's used as the initial sort timestamp.
    2. If the account has a renewal day of the month set, calculate the next potential renewal date.
       Only consider this renewal date if it's in the future relative to the current date.
    3. If the renewal date is valid and sooner than the expiration date (if set),
       use the renewal date as the sort key.
    4. If neither an expiration date nor a renewal date is applicable (or if both are past),
       assign a sys.maxsize value to ensure the account is sorted towards the end.

    Args:
        credit_account (CreditAccount): The credit account for which to generate a sort key.

    Returns:
        int: A Unix timestamp in milliseconds indicating the nearest future date when the account expires
             or needs renewal. If neither is applicable, returns sys.maxsize.
    """
    # TODO this method probably should go to account repository / ORM model definition
    current_date = get_current_date()
    sort_timestamp = sys.maxsize  # Default for accounts that neither expire nor renew

    # Set initial sort_timestamp if the account has an expiration date
    if credit_account.expires:
        sort_timestamp = credit_account.expires

    # Check if the account has a renewal day of month and calculate the renewal timestamp if applicable
    if credit_account.renewable_amount is not None and credit_account.renewable_amount > 0:
        renewal_date = get_next_renewal_date(renewal_day, current_date)

        if renewal_date > date_to_unix_milliseconds(current_date) and (
            sort_timestamp == sys.maxsize or renewal_date < sort_timestamp
        ):
            sort_timestamp = renewal_date

    return sort_timestamp


class TransactionService:
    def __init__(self, session: Session):
        self.session = session
        self.account_repository = AccountRepository(session)
        self.balance_service = BalanceService(session)
        self.transaction_repository = TransactionRepository(session)
        self.subscription_repository = SubscriptionRepository(session)

    def _perform_transaction(
        self,
        from_acc: CreditAccount,
        target_acc: CreditAccount,
        target_details: TransactionDetails,
        tx_group_id: str | None = None,
    ) -> None:
        """
        Transfers credits from one credit account to another.
         `tx_id` is supposed to link direct transaction between credit accounts of different types.
         `tx_group_id` is used as a logical identifier to group lease related transactions.
        """
        tx_id = str(uuid4())
        logger.debug(f"Performing transaction with {tx_id=}, {tx_group_id=}")

        if target_details.created is None:
            target_details.created = get_current_milliseconds_timestamp()

        self.transaction_repository.create_transaction(
            details=target_details, account=target_acc, tx_id=tx_id, tx_group_id=tx_group_id
        )
        logger.debug(f"Transaction to {target_acc.id} created with {target_details=}")
        target_details.credit, target_details.debit = target_details.debit, target_details.credit
        self.transaction_repository.create_transaction(
            details=target_details, account=from_acc, tx_id=tx_id, tx_group_id=tx_group_id
        )
        logger.debug(f"Transaction from {from_acc.id} created with {target_details=}")

    @transactional
    @advisory_lock("organization_id")
    def fill_account(
        self, receiver_acc_id: UUID, amount: int, _db_session: Session, organization_id: str, created: int | None = None
    ) -> None:
        """
        Adds credits to the specified organization's credit account,
        making a transaction from the SaaS account to the asset account
        """
        if amount <= 0:
            raise ValueError(f"Credits amount is expected to be a positive integer number, received amount: {amount}")
        target_account = self.account_repository.get_account(receiver_acc_id)
        if target_account.type != CreditAccountType.ASSET:
            raise ValueError(
                f"Invalid account type - fill/refill operation is only permitted "
                f"for {CreditAccountType.ASSET} accounts, "
                f"got {target_account.type}"
            )

        service_acc = self.account_repository.retrieve_saas_account()
        logger.debug(f"Retrieved SaaS service account with id {service_acc.id}")
        details = TransactionDetails(debit=amount, credit=0, created=created)
        self._perform_transaction(from_acc=service_acc, target_acc=target_account, target_details=details)
        logger.info(
            f"Added new credits to the organization {organization_id}, asset account id: {receiver_acc_id}. "
            f"Credits amount: {amount}."
        )

    @transactional
    @advisory_lock("organization_id")
    def withdraw_credits(
        self, account_id: UUID, amount: int, _db_session: Session, subscription: Subscription, organization_id: str
    ) -> None:
        """
        Withdraws credits from the specified organization's credit account,
        making a transaction from the asset account to the SaaS account
        """
        if amount <= 0:
            raise ValueError(f"Credits amount is expected to be a positive integer number, received amount: {amount}")
        asset_account = self.account_repository.get_account(account_id)
        if asset_account.type != CreditAccountType.ASSET:
            raise ValueError(
                f"Invalid account type - withdraw credits operation is only permitted "
                f"for {CreditAccountType.ASSET} accounts, got {asset_account.type}"
            )
        accounts_balances = self.balance_service.get_credit_accounts_balances(
            subscription=subscription, organization_id=organization_id, _db_session=self.session
        )
        account_balance = accounts_balances.get(
            asset_account.id, BalanceResponse(incoming=0, available=0, blocked=0)
        ).available

        if account_balance < amount:
            raise ValueError(
                f"Cannot withdraw {amount} credits from the account {account_id}: available balance "
                f"is only {account_balance}"
            )
        saas_account = self.account_repository.retrieve_saas_account()
        target_details = TransactionDetails(debit=amount, credit=0)
        self._perform_transaction(from_acc=asset_account, target_acc=saas_account, target_details=target_details)
        logger.info(
            f"Withdraw credits from the organization {organization_id}, asset account id: {account_id}. "
            f"Credits amount: {amount}."
        )

    @transactional
    @advisory_lock("organization_id")
    def acquire_lease(
        self, details: LeaseRequestData, subscription: Subscription, organization_id: str, _db_session: Session
    ) -> str:
        """
        Creates a reservation on the asset accounts credits that are sent to the organization's lease account

        :param details: contains lease details for created transactions
        :param subscription: organization's active subscription
        :param organization_id: the parameter to use as the advisory lock key
        :return: lease id
        """

        if not details.requests:
            raise ValueError("Missing lease requests")

        lease_sum = sum(details.requests.values())  # Total amount from all requests
        organization_balance = self.balance_service.get_organization_balance(active_subscription=subscription)
        if organization_balance.available < lease_sum:
            raise InsufficientBalanceException(organization_balance.available, required=lease_sum)

        lease_account: CreditAccount | None = next(
            (account for account in subscription.credit_accounts if account.type == CreditAccountType.LEASE), None
        )
        if not lease_account:
            raise NoDatabaseResult(f"Lease account for organization with id {organization_id} does not exist")

        current_time = get_current_milliseconds_timestamp()
        asset_accounts = sorted(
            [
                account
                for account in subscription.credit_accounts
                if account.type == CreditAccountType.ASSET and (not account.expires or account.expires > current_time)
            ],
            key=lambda x: _sort_key(credit_account=x, renewal_day=subscription.renewal_day_of_month),
        )

        lease_id = str(uuid4())
        remaining_requests = details.requests.copy()
        accounts_balances = self.balance_service.get_credit_accounts_balances(
            subscription=subscription, organization_id=organization_id, _db_session=self.session
        )
        for account in asset_accounts:
            account_balance = accounts_balances.get(
                account.id, BalanceResponse(incoming=0, available=0, blocked=0)
            ).available
            if account_balance <= 0:
                continue  # Skip this account if no available balance

            processed_requests = {}
            for unit, amount in remaining_requests.items():
                if amount <= 0:
                    continue  # Skip if no more requests for this unit

                available_for_unit = min(amount, account_balance)
                processed_requests[unit] = available_for_unit
                remaining_requests[unit] -= available_for_unit
                account_balance -= available_for_unit
                if account_balance <= 0:
                    break  # Stop if the account balance is depleted

            if processed_requests:
                tx_details = TransactionDetails(
                    debit=sum(processed_requests.values()),
                    credit=0,
                    project_id=details.project_id,
                    service_name=details.service_name,
                    requests=processed_requests,
                )
                self._perform_transaction(
                    from_acc=account, target_acc=lease_account, target_details=tx_details, tx_group_id=lease_id
                )
        return lease_id

    @transactional
    @advisory_lock("organization_id")
    def _cancel_lease(
        self, lease_id: str, subscription: Subscription, organization_id: str, _db_session: Session
    ) -> None:
        """
        Transfers reserved on the lease account credits back to the source asset accounts

        :param lease_id: transaction id of the lease (common for asset and lease account)
        :param organization_id: the parameter to use as the advisory lock key

        """
        if self._is_lease_closed(lease_id):
            logger.info(f"The lease with {lease_id=} for the organization {organization_id} had been closed already.")
            return

        lease_account = next(
            account for account in subscription.credit_accounts if account.type == CreditAccountType.LEASE
        )
        # get information about lease credits and their source asset accounts
        result: Result = self.transaction_repository.get_lease_transactions_and_accounts_data(lease_id)

        result_records: list[LeaseCreditsRecord] = []
        leased_credits = 0
        for row in result:
            leased_credits += row.credit
            result_records.append(
                LeaseCreditsRecord(
                    credit=row.credit,
                    created=row.created,
                    project_id=row.project_id,
                    service_name=row.service_name,
                    account_id=row.account_id,
                )
            )
        logger.info(
            f"Cancelling lease {lease_id} for the project {result_records[0].project_id}, "
            f"organization {subscription.organization_id}."
        )
        self._return_unused_credits(
            lease_id=lease_id,
            lease_acc=lease_account,
            return_amount=leased_credits,
            records=result_records,
        )

    def cancel_lease(self, lease_id: str, _db_session: Session) -> None:
        """
        Transfers reserved on the lease account credits back to the source asset accounts

        :param lease_id: transaction group id of the lease (common for asset and lease account)

        """
        subscription = self.subscription_repository.get_by_lease_id(lease_id)
        return self._cancel_lease(
            lease_id=lease_id,
            subscription=subscription,
            organization_id=subscription.organization_id,
            _db_session=_db_session,
        )

    def _is_lease_closed(self, lease_id: str) -> bool:
        """
        Checks whether the lease had been closed already.
        Sum of all debits and credits in lease account transactions with the same lease_id (tx_group_id)
        for closed leases should be equal to 0.
        """
        result: Row = self.transaction_repository.get_lease_transaction_balance(lease_id)
        return result.running_balance == 0

    @transactional
    @advisory_lock("organization_id")
    def finalize_lease(self, metering_data: MeteringEvent, organization_id: str, _db_session: Session) -> None:
        """
        Based on received metering data, makes corresponding transactions:

        - from organization's lease account to SaaS credit account -
        in case when actual credits consumption is equal to the existing lease;

        - from organization's lease account to SaaS credit account AND
        from the lease account back to the source credit account,
        in case when actual credits consumption is smaller than the existing lease.
        """
        if self._is_lease_closed(metering_data.lease_id):
            logger.info(f"The lease with id {metering_data.lease_id} had been closed already.")
            return

        # create transaction from lease to SaaS with consumed_credits amount
        subscription = self.subscription_repository.get_by_lease_id(metering_data.lease_id)
        lease_acc = next(account for account in subscription.credit_accounts if account.type == CreditAccountType.LEASE)
        saas_acc = self.account_repository.retrieve_saas_account()
        consumed_credits = sum(rec.amount for rec in metering_data.consumption)
        requests = {rec.unit: rec.amount for rec in metering_data.consumption}

        target_details = TransactionDetails(
            debit=consumed_credits,
            credit=0,
            project_id=metering_data.project_id,
            service_name=metering_data.service_name,
            requests=requests,
        )
        self._perform_transaction(
            from_acc=lease_acc, target_acc=saas_acc, target_details=target_details, tx_group_id=metering_data.lease_id
        )
        logger.info(
            f"{consumed_credits} credits has been transferred from {organization_id} "
            f"organization's lease account to the SaaS account."
        )

        # get information about lease credits and their source asset accounts
        result: Result = self.transaction_repository.get_lease_transactions_and_accounts_data(metering_data.lease_id)

        result_records: list[LeaseCreditsRecord] = []
        leased_credits = 0
        for row in result:
            leased_credits += row.credit
            result_records.append(
                LeaseCreditsRecord(
                    credit=row.credit,
                    created=row.created,
                    project_id=row.project_id,
                    service_name=row.service_name,
                    account_id=row.account_id,
                )
            )

        if leased_credits > consumed_credits:
            self._return_unused_credits(
                lease_id=metering_data.lease_id,
                lease_acc=lease_acc,
                return_amount=leased_credits - consumed_credits,
                records=result_records,
            )
        logger.info(
            f"Lease {metering_data.lease_id} for the project {result_records[0].project_id}, "
            f"organization {organization_id} has been closed successfully."
        )

    def _return_unused_credits(
        self,
        lease_id: str,
        lease_acc: CreditAccount,
        return_amount: int,
        records: list[LeaseCreditsRecord],
    ):
        """
        Returns unused leased credits to the source asset accounts.

        :param records: the list containing information about leased credits and their source accounts,
        sorted by account's expiration date in descending order.
        This list might contain more than one record in case when leased credits were taken
        from more than one credit account (single account's balance wasn't sufficient).

        Return credits transactions are made with the same `created` timestamp as in original lease transactions
        in order to ensure correct balance calculation timeframes.
        """

        logger.info(
            f"Lease {lease_id} has {return_amount} credits reserved, but not used. "
            f"Returning unused credits to the source asset accounts."
        )
        for rec in records:
            target_acc: CreditAccount = self.account_repository.get_account(rec.account_id)
            if return_amount <= rec.credit:
                target_details = TransactionDetails(
                    debit=return_amount,
                    credit=0,
                    project_id=rec.project_id,
                    service_name=rec.service_name,
                    created=rec.created,
                )
                logger.info(f"Returning {target_details.debit} credits to the credit account with id {target_acc.id}.")
                self._perform_transaction(
                    from_acc=lease_acc, target_acc=target_acc, target_details=target_details, tx_group_id=lease_id
                )
                break
            return_amount -= rec.credit
            target_details = TransactionDetails(
                debit=rec.credit,
                credit=0,
                project_id=rec.project_id,
                service_name=rec.service_name,
                created=rec.created,
            )
            logger.info(f"Returning {target_details.debit} credits to the credit account with id {target_acc.id}.")
            self._perform_transaction(
                from_acc=lease_acc,
                target_acc=target_acc,
                target_details=target_details,
                tx_group_id=lease_id,
            )

    def get_transactions(  # noqa: PLR0913
        self,
        organization_id: str,
        skip: int,
        limit: int,
        from_date: int,
        to_date: int,
        sort: list[tuple[str, str]],
        project_id: str | None,
        usage_type: str | None,
    ) -> tuple[int, list[TransactionInfo]]:
        """
        Retrieves transactions from the organization's lease account to the SaaS account within specified time range
        and returns final credits consumption information.
        """
        total_matched, db_transactions = self.transaction_repository.get_transactions(
            organization_id=organization_id,
            skip=skip,
            limit=limit,
            from_date=from_date,
            to_date=to_date,
            sort=sort,
            project_id=project_id,
            usage_type=usage_type,
        )

        transactions = [
            TransactionInfo(
                credits=record.debit,
                project_id=record.project_id,
                service_name=record.service_name,
                milliseconds_timestamp=record.created,
            )
            for record in db_transactions
        ]

        return total_matched, transactions

    @staticmethod
    def _process_resources_amount(resources_dict: dict) -> ResourcesAmount:
        resource_amount = ResourcesAmount()
        resource_amount_fields = resource_amount.dict()
        for key, value in resources_dict.items():
            if key in resource_amount_fields:
                setattr(resource_amount, key, getattr(resource_amount, key) + value)
        return resource_amount

    def _parse_row_to_aggregate_response(self, aggregate_keys: list[AggregatesKey], aggregation_result: list[Row]):
        if aggregation_result:
            aggregate_response = []
            for row in aggregation_result:
                group_items = [GroupItem(key=a_key.value, value=getattr(row, a_key.value)) for a_key in aggregate_keys]
                total_credits = row.credits
                resources_amount = self._process_resources_amount(resources_dict=row.resources)
                aggregate_result = AggregatesResult(credits=total_credits, resources=resources_amount)
                aggregate_item = AggregateItem(group=group_items, result=aggregate_result)
                aggregate_response.append(aggregate_item)
            return AggregatesResponse(aggregates=aggregate_response)
        return AggregatesResponse(aggregates=[])

    def aggregate_transactions(
        self,
        organization_id: str,
        aggregate_keys: list[AggregatesKey],
        from_date: int,
        to_date: int,
        projects: list[str] | None = None,
    ) -> AggregatesResponse:
        """
        Retrieves credit consumption for organization grouped by various dimensions such as project and service, date.
        Aggregation is calculated only for completed transactions, i.e. from the organisation's leasing account to
        the SaaS account within a specified time range and an optional project filter that
        lists the project identifiers for which aggregates are calculated.
        """

        aggregation_result = self.transaction_repository.aggregate_transactions(
            organization_id=organization_id,
            aggregates_keys=aggregate_keys,
            from_date=from_date,
            to_date=to_date,
            projects=projects,
        )

        return self._parse_row_to_aggregate_response(
            aggregate_keys=aggregate_keys, aggregation_result=aggregation_result
        )
