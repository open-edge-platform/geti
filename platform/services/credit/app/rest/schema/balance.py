# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from pydantic import BaseModel, Field

from rest.schema.common import MAX_INT_32


class BalanceResponse(BaseModel):
    incoming: int
    available: int
    blocked: int


class BalancePayload(BaseModel):
    add: int | None = Field(
        default=None,
        gt=0,
        le=MAX_INT_32,
        description="The `add` field must be greater than zero and less than or equal to 2147483647.",
    )
    subtract: int | None = Field(
        default=None,
        gt=0,
        le=MAX_INT_32,
        description="The `subtract` field must be greater than zero and less than or equal to 2147483647.",
    )
