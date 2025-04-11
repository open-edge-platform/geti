# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE


from pydantic import BaseModel

from rest.schema.common import ListModel


class TransactionInfo(BaseModel):
    credits: int
    project_id: str | None = None
    service_name: str
    milliseconds_timestamp: int


class TransactionsResponse(ListModel):
    transactions: list[TransactionInfo]


class GroupItem(BaseModel):
    key: str
    value: str | int


class ResourcesAmount(BaseModel):
    images: int = 0
    frames: int = 0


class AggregatesResult(BaseModel):
    credits: int
    resources: ResourcesAmount


class AggregateItem(BaseModel):
    group: list[GroupItem]
    result: AggregatesResult


class AggregatesResponse(BaseModel):
    aggregates: list[AggregateItem]
