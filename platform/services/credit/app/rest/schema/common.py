# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from pydantic import BaseModel

MAX_INT_32 = 2**31 - 1


class NextPage(BaseModel):
    limit: int
    skip: int


class ListModel(BaseModel):
    total_matched: int
    next_page: NextPage | None = None
