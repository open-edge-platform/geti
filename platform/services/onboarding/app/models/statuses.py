# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE


from enum import Enum


class Status(str, Enum):
    ACTIVE = "ACT"
    REGISTERED = "RGS"
    SUSPENDED = "SSP"
    REQUESTED = "REQ"
