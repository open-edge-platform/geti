# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE


from pydantic import BaseModel


class PlatformVersion(BaseModel):
    version: str
    k3s_version: str
    nvidia_drivers_version: str | None
    intel_drivers_version: str | None
    is_current: bool


class PlatformVersionsResponse(BaseModel):
    versions: list[PlatformVersion]
