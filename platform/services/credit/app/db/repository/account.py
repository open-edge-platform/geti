# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging
from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError, NoResultFound, StatementError
from sqlalchemy.orm import Session

from db.model.credit_account import CreditAccount
from db.repository.common import BaseRepository
from exceptions.custom_exceptions import NoDatabaseResult
from utils.enums import CreditAccountType
from utils.time import get_current_milliseconds_timestamp

logger = logging.getLogger(__name__)


class AccountRepository(BaseRepository):
    def __init__(self, session: Session):
        self.session = session

    def get_account(self, account_id: UUID) -> CreditAccount:
        """Retrieves active credit account with specified account id"""
        try:
            stmt = (
                select(CreditAccount)
                .filter_by(id=account_id)
                .filter(
                    or_(
                        CreditAccount.expires.is_(None),
                        CreditAccount.expires > get_current_milliseconds_timestamp(),
                    )
                )
            )
            return self.session.scalars(statement=stmt).one()
        except NoResultFound:
            raise NoDatabaseResult(f"Credit account with ID {account_id} not found.")

    def get_renewable_asset_accounts(self, expiration_threshold: int, subscription_id: UUID) -> Sequence[CreditAccount]:
        """Get all renewable, active (not expired within a certain threshold) asset credit accounts"""
        stmt = (
            select(CreditAccount)
            .filter(CreditAccount.subscription_id == subscription_id)
            .filter(CreditAccount.type == CreditAccountType.ASSET)
            .filter(CreditAccount.renewable_amount.is_not(None))
            .filter(CreditAccount.renewable_amount > 0)
            .filter(
                or_(
                    CreditAccount.expires.is_(None),
                    CreditAccount.expires > expiration_threshold,
                )
            )
        )
        return self.session.scalars(statement=stmt).all()

    def retrieve_saas_account(self) -> CreditAccount:
        """Returns SaaS provider account (common for all organizations)"""
        stmt = select(CreditAccount).where(CreditAccount.type == CreditAccountType.SAAS)  # type: ignore
        result = self.session.execute(statement=stmt)
        return result.scalars().one()

    def create(self, credit_account: CreditAccount) -> None:
        """
        Create a new credit account with specified details.
        """
        logger.debug(f"Create credit account called with {repr(credit_account)}")
        self.session.add(credit_account)
        try:
            self.session.flush()
        except (IntegrityError, StatementError) as err:
            logger.error(f"{err.params} - {err.orig}")
            raise RuntimeError("Credit Account creation failed. Check logs for more info:") from err

    def get_organization_accounts(
        self,
        subscription_id: UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[int, Sequence[CreditAccount]]:
        """
        Retrieves a sequence of active credit accounts assigned to the specified subscription.
        Note:
            This method executes a database query to fetch credit accounts belonging to the specified organization's
            subscription, with optional pagination (skip and limit) and filtering by account type.
            The returned tuple contains both the total count of matched accounts and the list of retrieved accounts.
        """

        stmt = (
            select(CreditAccount)
            .filter_by(subscription_id=subscription_id, type=CreditAccountType.ASSET)
            .filter(or_(CreditAccount.expires.is_(None), CreditAccount.expires > get_current_milliseconds_timestamp()))
            .order_by(CreditAccount.name.asc())
        )
        result = self.session.scalars(stmt).all()
        total_matched = len(result)
        result_accounts = result[skip : skip + limit]

        return total_matched, result_accounts
