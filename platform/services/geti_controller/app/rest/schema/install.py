# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from pydantic import BaseModel


class InstallRequest(BaseModel):
    version_number: str


class InstallResponse(BaseModel):
    detail: str
