# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from uuid import UUID

from pydantic import BaseModel, Field

from rest.schema.balance import BalanceResponse
from rest.schema.common import MAX_INT_32, ListModel
from utils.enums import CreditSystemTimeBoundaries


class CreditAccount(BaseModel):
    id: UUID
    organization_id: str
    name: str
    renewable_amount: int | None = None  # renewable quota, for the welcoming one-off account it's None
    renewal_day_of_month: int | None = None
    created: int
    updated: int
    expires: int | None = None  # renewable account doesn't have an expiration timestamp by default
    balance: BalanceResponse


class CreditAccountsResponse(ListModel):
    credit_accounts: list[CreditAccount]


class CreditAccountPostPayload(BaseModel):
    name: str = Field(max_length=80, min_length=1)
    init_amount: int = Field(
        ...,
        ge=0,
        le=MAX_INT_32,
        description="The `init_amount` must be greater than or equal zero and less than or equal to 2147483647.",
    )
    renewable_amount: int | None = Field(
        default=None,
        ge=0,
        le=MAX_INT_32,
        description="The `renewable_amount` must be greater than or equal zero and less than or equal to 2147483647.",
    )  # for the welcoming one-off account it's None
    expires: int | None = Field(
        default=None,
        ge=CreditSystemTimeBoundaries.START.value,
        le=CreditSystemTimeBoundaries.END.value,
        description="The expiration date should be provided in milliseconds and "
        "be in [April 1, 2024; April 2, 2224] time interval.",
    )  # renewable account doesn't have an expiration timestamp by default


class CreditAccountPutPayload(BaseModel):
    name: str = Field(max_length=80, min_length=1)
    renewable_amount: int | None = Field(
        default=None,
        ge=0,
        le=MAX_INT_32,
        description="The `renewable_amount` must be greater than or equal zero and less than or equal to 2147483647.",
    )  # for the welcoming one-off account it's None
    expires: int | None = Field(
        default=None,
        ge=CreditSystemTimeBoundaries.START.value,
        le=CreditSystemTimeBoundaries.END.value,
        description="The expiration date should be provided in milliseconds and "
        "be in [April 1, 2024; April 2, 2224] time interval.",
    )
