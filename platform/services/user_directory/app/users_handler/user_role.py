"""User Interface."""

from geti_spicedb_tools import AccessResourceTypes
from typing_extensions import TypedDict

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE


class UserRole(TypedDict):
    """Represents a user role, with respect to a specific resource."""

    role: str
    resource_type: AccessResourceTypes
    resource_id: str
