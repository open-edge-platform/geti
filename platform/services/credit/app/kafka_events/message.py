# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from dataclasses import dataclass


@dataclass
class ResourceConsumption:
    unit: str
    amount: int


@dataclass
class MeteringEvent:
    """Expected metering message schema"""

    service_name: str
    workspace_id: str
    lease_id: str
    consumption: list[ResourceConsumption]
    date: int | None
    project_id: str | None = None
