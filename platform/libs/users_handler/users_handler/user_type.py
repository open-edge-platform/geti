"""User Interface."""

from typing_extensions import TypedDict

from users_handler.user_role import UserRole

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


class UserType(TypedDict):
    """User Interface"""

    uid: str
    name: str | None
    mail: str | None
    roles: list[UserRole]
    group: int
    registered: bool
    email_token: str | None
