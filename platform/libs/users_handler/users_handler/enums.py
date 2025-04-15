"""Module enums"""

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
from enum import IntEnum


class UserRoles(IntEnum):
    """Available roles from v1.0.
    Still used in migration scripts"""

    ADMIN = 0


class LdapAttr:
    """LDAP attributes mapping"""

    cn = "cn"
    uid = "uid"
    name = "sn"
    mail = "mail"
    group = "gidNumber"
    email_token = "labeledURI"  # noqa: S105
    registered = "l"
    user_password = "userPassword"  # noqa: S105
