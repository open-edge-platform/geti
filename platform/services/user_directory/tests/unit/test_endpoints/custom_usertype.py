# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from collections.abc import Sequence

from spicedb_utils import AccessResourceTypes

from users_handler.users_handler import UserRole, UserType


def custom_mock_usertype(
    uid: str = "example-uid",
    name: str | None = None,
    mail: str | None = None,
    roles: Sequence[UserRole] = (
        UserRole(role="example_role", resource_type=AccessResourceTypes.PROJECT, resource_id="example_id"),
    ),
    group: int = 420,
    registered: bool = True,
    email_token: str | None = None,
) -> UserType:
    """
    Creates a UserType class with custom, yet optional arguments
    """
    example_user_type = UserType(
        uid=uid,
        mail=mail,
        roles=list(roles),
        group=group,
        registered=registered,
        name=name,
        email_token=email_token,
    )
    return example_user_type


def custom_mock_usermodel(
    uid: str,
    mail: str,
    name: str = "example_user_name",
    registered: bool = True,
    roles: Sequence[UserRole] = (
        UserRole(role="example_role", resource_type=AccessResourceTypes.PROJECT, resource_id="example_id"),
    ),
):
    """
    Creates an imitation of UserModel class with custom, yet optional arguments
    """
    example_user_model = {
        "uid": uid,
        "name": name,
        "mail": mail,
        "registered": registered,
        "roles": roles,
    }
    return example_user_model
