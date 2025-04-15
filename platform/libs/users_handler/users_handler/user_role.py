"""User Role representation."""

from geti_spicedb_tools import AccessResourceTypes
from typing_extensions import TypedDict

# INTEL CONFIDENTIAL
#
# Copyright (C) 2021 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and your use of them is governed by
# the express license under which they were provided to you ("License"). Unless the License provides otherwise,
# you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is, with no express or implied warranties,
# other than those that are expressly stated in the License.


class UserRole(TypedDict):
    """Represents a user role, with respect to a specific resource."""

    role: str
    resource_type: AccessResourceTypes
    resource_id: str
