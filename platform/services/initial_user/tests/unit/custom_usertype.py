# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
