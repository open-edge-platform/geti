"""Module enums"""

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from enum import Enum


class UserStatus(str, Enum):
    """Available user statuses for use in AccountService"""

    ACTIVATED = "ACT"
    REGISTERED = "RGS"
    DELETED = "DEL"
    SUSPENDED = "SSP"


class OrganizationStatus(str, Enum):
    """Available organization statuses for use in AccountService"""

    ACTIVATED = "ACT"
    REGISTERED = "RGS"
    DELETED = "DEL"
    SUSPENDED = "SSP"
