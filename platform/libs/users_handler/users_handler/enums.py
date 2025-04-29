"""Module enums"""

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
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
