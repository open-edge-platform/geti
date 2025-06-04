# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from pydantic import BaseModel


class UpgradeRequest(BaseModel):
    version_number: str
    force_upgrade: bool = False


class UpgradeResponse(BaseModel):
    detail: str
