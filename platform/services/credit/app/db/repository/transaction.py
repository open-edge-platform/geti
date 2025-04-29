# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, cast
from uuid import UUID

from sqlalchemy import Result, Row, asc, desc, select, text
from sqlalchemy.orm import Session

from db.model.credit_account import CreditAccount
from db.model.subscription import Subscription
from db.model.transaction import Transactions
from db.repository.common import BaseRepository
from utils.enums import AggregatesKey, CreditAccountType

logger = logging.getLogger(__name__)


@dataclass
class TransactionDetails:
    debit: int
    credit: int
    project_id: str | None = None
    service_name: str | None = None
    requests: dict | None = None
    created: int | None = None


class TransactionRepository(BaseRepository):
    def __init__(self, session: Session):
        self.session = session

    def create_transaction(
        self, details: TransactionDetails, account: CreditAccount, tx_id: str, tx_group_id: str | None = None
    ) -> UUID:
        transaction = Transactions(
            tx_id=tx_id,
            tx_group_id=tx_group_id,
            account_id=account.id,
            debit=details.debit,
            credit=details.credit,
            project_id=details.project_id,
            service_name=details.service_name,
            requests=details.requests,
            created=details.created,
        )

        self.session.add(transaction)
        self.session.flush()  # save without releasing the lock
        return transaction.id

    def get_lease_transactions_and_accounts_data(self, lease_id: str) -> Result:
        """
        Returns a table with the information about leased from the asset accounts credits,
        sorted by the account's expiration date in descending order.
        """
        query = text(
            """
            SELECT t.credit, t.created, t.project_id, t.service_name, t.account_id, ca.expires FROM "Transactions" t 
            JOIN "CreditAccount" ca ON t.account_id = ca.id 
            WHERE t.tx_group_id = :lease_id AND t.credit > 0 AND ca.type = :type
            ORDER BY ca.expires DESC
            """
        )
        return self.session.execute(statement=query, params={"lease_id": lease_id, "type": CreditAccountType.ASSET})

    def get_lease_transaction_balance(self, lease_id: str) -> Row:
        """
        Calculates lease transactions balance for the provided lease id.
        Returns a row with columns 'account_id' and 'running_balance'.
        """
        query = text(
            """
            SELECT t.account_id, (sum(t.debit) - sum(t.credit)) as running_balance
            FROM "Transactions" t
            JOIN "CreditAccount" ca ON t.account_id = ca.id
            WHERE t.tx_group_id = :lease_id AND ca.type = :type
            GROUP BY t.account_id
            """
        )
        return self.session.execute(
            statement=query, params={"lease_id": lease_id, "type": CreditAccountType.LEASE}
        ).one()

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
    ) -> tuple[int, list[Transactions]]:
        """
        Retrieves transactions from the organization's lease account to the SaaS account within specified time range.
        Returns:
            tuple: Total matched transactions count and the list of transactions.
        """
        # Subquery to filter transactions related to lease accounts
        lease_transactions_subq = (
            select(Transactions.tx_group_id)
            .distinct()
            .join(CreditAccount, Transactions.account_id == CreditAccount.id)
            .join(Subscription, CreditAccount.subscription_id == Subscription.id)
            .where(CreditAccount.type == CreditAccountType.LEASE, Subscription.organization_id == organization_id)
            .subquery("lease_transactions_subq")
        )

        # Main query to retrieve transactions
        query = (
            select(Transactions)
            .join(lease_transactions_subq, Transactions.tx_group_id == lease_transactions_subq.c.tx_group_id)
            .join(CreditAccount)
            .where(
                CreditAccount.type == CreditAccountType.SAAS,
                Transactions.created < to_date,
                Transactions.created >= from_date,
            )
        )

        if project_id:
            query = query.filter(Transactions.project_id == project_id)

        if usage_type:
            query = query.filter(Transactions.service_name == usage_type)

        for field, direction in sort:
            if direction == "asc":
                query = query.order_by(asc(getattr(Transactions, field)))
            else:
                query = query.order_by(desc(getattr(Transactions, field)))

        result: list[Transactions] = cast("list[Transactions]", self.session.scalars(query).all())

        total_matched = len(result)
        result_transactions = result[skip : skip + limit]

        return total_matched, result_transactions

    def aggregate_transactions(
        self,
        organization_id: str,
        aggregates_keys: list[AggregatesKey],
        from_date: int,
        to_date: int,
        projects: list[str] | None = None,
    ) -> Sequence[Row[Any]]:
        """
        Calculates credit and resource consumption for completed transactions for an organization
        with a specific identifier. Aggregates transactions by keys within a date range,
        optionally filtered by projects, where projects is a list of project ids.

        Args:
            organization_id (str)
                the identifier of the organization for which the aggregation will be calculated.
            aggregates_keys (list[AggregatesKey]):
                A list of enumeration members representing the grouping keys for aggregation, i.e. project, service_name
                and date.
            from_date (int):
                The start timestamp of the date range for which to aggregate transactions, inclusive,
                in milliseconds since the epoch.
            to_date (int):
                The end timestamp of the date range for which to aggregate transactions, exclusive,
                in milliseconds since the epoch.
            projects (list[str], optional):
                A list of project ids to filter the transactions. If None, transactions from all projects are included.

        Returns:
            A list of rows containing aggregated completed transactions,
            where each row is a sequence of values corresponding to column names and aggregation
            values of credits and resources spent.

        Raises:
            ValueError: If no valid fields are provided for grouping.
        """
        allowed_group_by_fields = {a_key.value for a_key in AggregatesKey}
        group_by_fields = {field.value for field in aggregates_keys if field.value in allowed_group_by_fields}
        if not group_by_fields:
            raise ValueError(f"No valid fields provided for grouping. Accepted keys are: {allowed_group_by_fields}")

        consumption_columns_names = ", ".join([f"consumption.{field}" for field in group_by_fields])
        requests_agg_columns_names = ", ".join([f"agg.{field}" for field in group_by_fields])
        requests_columns_names = ", ".join([f"requests.{field}" for field in group_by_fields])
        join_conditions = " AND ".join([f"requests.{field} = total.{field}" for field in group_by_fields])
        query_template = """
            WITH
                lease_transactions_subq AS (
                SELECT DISTINCT transactions.tx_group_id
                FROM "Transactions" transactions
                JOIN "CreditAccount" credit_account ON credit_account.id = transactions.account_id
                JOIN "Subscription" subscription ON credit_account.subscription_id = subscription.id
                WHERE credit_account.type = :lease_account
                    AND subscription.organization_id = :org_id
                    AND transactions.created < :to_date
                    AND transactions.created >= :from_date
                    AND transactions.credit > 0
                ),
                consumption AS (
                    SELECT
                        transactions.tx_group_id,
                        transactions.project_id AS {project},
                        transactions.service_name AS {service_name},
                        (transactions.created - transactions.created % (60 * 60 * 24 * 1000)) AS {date},
                        transactions.credit,
                        requests_json.key,
                        (requests_json.value :: numeric) AS value
                    FROM "Transactions" transactions
                    JOIN lease_transactions_subq ON transactions.tx_group_id = lease_transactions_subq.tx_group_id
                    JOIN "CreditAccount" credit_account ON credit_account.id = transactions.account_id
                    JOIN jsonb_each_text(transactions.requests) AS requests_json ON TRUE
                    WHERE credit_account.type = :saas_account
                        AND transactions.debit > 0
                        AND (:projects IS NULL OR transactions.project_id = ANY(:projects))
                        AND transactions.created < :to_date
                        AND transactions.created >= :from_date
                ),
                requests AS (
                    SELECT
                        {requests_agg_columns_names},
                        jsonb_object_agg(agg.key, agg.sum) AS resources
                    FROM (
                        SELECT
                            {consumption_columns_names},
                            consumption.key,
                            SUM(consumption.value)
                        FROM consumption
                        GROUP BY
                            {consumption_columns_names},
                            consumption.key
                        ) AS agg
                    GROUP BY {requests_agg_columns_names}
                ),
                total AS (
                    SELECT
                        {consumption_columns_names},
                        SUM(value) credits
                    FROM consumption
                    GROUP BY {consumption_columns_names}
                )
            SELECT
                {requests_columns_names},
                requests.resources,
                total.credits
            FROM requests
            JOIN total ON {join_conditions};
        """
        query_text = query_template.format(
            date=AggregatesKey.DATE.value,
            project=AggregatesKey.PROJECT.value,
            service_name=AggregatesKey.SERVICE_NAME.value,
            requests_columns_names=requests_columns_names,
            consumption_columns_names=consumption_columns_names,
            requests_agg_columns_names=requests_agg_columns_names,
            join_conditions=join_conditions,
        )
        params = {
            "org_id": organization_id,
            "from_date": from_date,
            "to_date": to_date,
            "projects": projects if projects else None,
            "saas_account": CreditAccountType.SAAS.value,
            "lease_account": CreditAccountType.LEASE.value,
        }
        query = text(query_text).bindparams(**params)

        return self.session.execute(query).fetchall()
