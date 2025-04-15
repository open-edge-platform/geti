# INTEL CONFIDENTIAL
#
# Copyright (C) 2024 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and your use of them is governed by
# the express license under which they were provided to you ("License"). Unless the License provides otherwise,
# you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is, with no express or implied warranties,
# other than those that are expressly stated in the License.

from users_handler.users_handler import UserType


def custom_mock_usertype(
    uid: str = "example-uid",
    mail: str | None = None,
) -> UserType:
    """
    Creates a UserType class with custom, yet optional arguments
    """
    example_user_type = UserType(
        uid=uid,
        name="User Name",
        mail=mail,
        registered=True,
        roles=[],
        group=100,
        email_token=None,
    )
    return example_user_type
