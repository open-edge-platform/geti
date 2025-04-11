# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging
from collections.abc import Sequence
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import Row, text
from sqlalchemy.orm import Session

from db.model.balance import AccountBalance, BalanceSnapshot
from db.repository.common import BaseRepository
from utils.time import get_current_milliseconds_timestamp

logger = logging.getLogger(__name__)


@dataclass
class AccountBalanceData:
    account_id: UUID
    available_balance: int
    incoming_balance: int
    snapshot_id: UUID | None = None


class BalanceRepository(BaseRepository):
    def __init__(self, session: Session):
        self.session = session

    def get_balance(self, subscription_id: UUID, current_date: int, cycle_start_date: int) -> Sequence[Row]:
        """
        Returns a table with the information about incoming and available balances
        for each asset account from the subscription.
        """
        query = text(
            """
            SELECT  account_id             AS account_id,
                    SUM(incoming_balance)  AS incoming_balance,
                    SUM(available_balance) AS available_balance,
                    SUM(blocked_balance)   AS blocked_balance
            FROM (
            
                -- Incoming and available balance from the latest snapshot:
                SELECT  balance.account_id        AS account_id,
                        balance.incoming_balance  AS incoming_balance,
                        balance.available_balance AS available_balance,
                        0                         AS blocked_balance
                FROM "AccountBalance" balance
                    JOIN "CreditAccount" acc ON acc.id = balance.account_id
                    JOIN (
                        SELECT id FROM "BalanceSnapshot"
                            WHERE subscription_id = :subscription_id
                            AND date <= :current_date
                            ORDER BY date LIMIT 1
                    ) AS snapshot ON snapshot.id = balance.snapshot_id
                    WHERE acc.subscription_id = :subscription_id
                    AND (acc.renewable_amount IS NULL OR acc.renewable_amount = 0) 
                    AND (acc.expires > :current_date OR acc.expires IS NULL)

                UNION
                
                -- Incoming balance for all types of credit accounts 
                SELECT  asset_tx.account_id                         AS account_id, 
                        SUM(asset_tx.debit) - SUM(asset_tx.credit)  AS incoming_balance,
                        0                                           AS available_balance,
                        0                                           AS blocked_balance
                FROM (
                    SELECT * FROM "Transactions" tx JOIN "CreditAccount" acc ON acc.id = tx.account_id
                    WHERE acc.subscription_id = :subscription_id
                        AND acc.type = 'ASSET'
                        AND (acc.expires > :current_date or acc.expires IS NULL)
                        AND tx.created >= (
                        SELECT CASE
                            WHEN (acc.renewable_amount IS NULL or acc.renewable_amount = 0) THEN
                                COALESCE((
                                    SELECT date FROM "BalanceSnapshot" 
                                        WHERE subscription_id = :subscription_id
                                        AND date <= :current_date
                                        ORDER BY date LIMIT 1), 0)  
                            ELSE :renewal_date
                        END)
                        AND tx.created <= :current_date
                ) AS asset_tx
                JOIN (
                    SELECT * FROM "Transactions" tx JOIN "CreditAccount" acc on acc.id = tx.account_id
                        WHERE acc.type = 'SAAS'
                            AND tx.created <= :current_date
                    ) AS saas_tx
                ON asset_tx.tx_id = saas_tx.tx_id
                GROUP BY asset_tx.account_id

                UNION

                -- Available balance for all types of credit accounts
                SELECT  account_id,
                        0                          as incoming_balance,
                        (sum(debit) - sum(credit)) as available_balance,
                        0                          as blocked_balance
                FROM "Transactions" tx join "CreditAccount" acc on acc.id = tx.account_id
                WHERE acc.subscription_id = :subscription_id
                    AND acc.type = 'ASSET'
                    AND (acc.expires > :current_date or acc.expires IS NULL)
                    AND tx.created >= (
                        SELECT CASE
                            WHEN (acc.renewable_amount IS NULL OR acc.renewable_amount = 0) THEN 
                                COALESCE((
                                    SELECT date FROM "BalanceSnapshot" 
                                        WHERE subscription_id = :subscription_id
                                            AND date <= :current_date 
                                        ORDER BY date LIMIT 1), 0)
                            ELSE :renewal_date
                        END)
                    AND tx.created <= :current_date    
                GROUP BY tx.account_id
                
                UNION
                
                -- Blocked balance for all types of credit accounts
                SELECT  asset_to_lease_tx.account_id,
                        0                             AS incoming_balance,
                        0                             AS available_balance,
                        SUM(asset_to_lease_tx.credit) AS blocked_balance
                FROM (
                        (SELECT * FROM "Transactions" tx JOIN "CreditAccount" acc ON tx.account_id = acc.id
                            WHERE acc.subscription_id = :subscription_id
                                AND acc.type = 'ASSET'
                                AND (acc.expires > :current_date or acc.expires IS NULL)
                                AND tx.tx_group_id IS NOT NULL  -- lease tx type
                                AND tx.created >= (
                                    SELECT CASE
                                        WHEN (acc.renewable_amount IS NULL OR acc.renewable_amount = 0) THEN 
                                            (:current_date - 7 * 24 * 60 * 60 * 1000)  -- last 7 days
                                        ELSE :renewal_date
                                    END)
                                AND tx.created <= :current_date
                                AND tx.credit > 0  -- from asset to lease
                        ) AS asset_to_lease_tx
                        LEFT JOIN (
                            SELECT * FROM "Transactions" tx JOIN "CreditAccount" acc ON tx.account_id = acc.id
                                WHERE acc.subscription_id = :subscription_id
                                    AND acc.type = 'LEASE'
                                    AND tx.created >= (
                                        SELECT CASE
                                            WHEN (acc.renewable_amount IS NULL OR acc.renewable_amount = 0) THEN 
                                                (:current_date - 7 * 24 * 60 * 60 * 1000)  -- last 7 days
                                            ELSE :renewal_date
                                        END)
                                    AND tx.created <= :current_date
                                    AND tx.credit > 0  -- from lease to saas or back to asset
                        ) AS closed_lease_tx ON asset_to_lease_tx.tx_group_id = closed_lease_tx.tx_group_id
                    ) WHERE closed_lease_tx.tx_group_id IS NULL                          
                GROUP BY asset_to_lease_tx.account_id
                
            ) AS account_balance GROUP BY account_id;
            """
        )
        return self.session.execute(
            statement=query,
            params={"subscription_id": subscription_id, "current_date": current_date, "renewal_date": cycle_start_date},
        ).all()

    def create_snapshot(self, subscription_id: UUID, date: int | None = None) -> BalanceSnapshot:
        """Creates new Balance snapshot. If date is not specified, takes UTC timestamp of the current time"""
        if date is None:
            date = get_current_milliseconds_timestamp()

        snapshot = BalanceSnapshot(date=date, subscription_id=subscription_id)

        self.session.add(snapshot)
        self.session.flush()

        return snapshot

    def create_balance(self, details: list[AccountBalanceData]) -> list[AccountBalance]:
        balance_list = [
            AccountBalance(
                snapshot_id=acc_balance.snapshot_id,
                account_id=acc_balance.account_id,
                incoming_balance=acc_balance.incoming_balance,
                available_balance=acc_balance.available_balance,
            )
            for acc_balance in details
        ]

        self.session.bulk_save_objects(balance_list)
        self.session.flush()
        return balance_list
