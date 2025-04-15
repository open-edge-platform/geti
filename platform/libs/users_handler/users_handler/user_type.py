"""User Interface."""

from typing_extensions import TypedDict

from users_handler.user_role import UserRole

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE


class UserType(TypedDict):
    """User Interface"""

    uid: str
    name: str | None
    mail: str | None
    roles: list[UserRole]
    group: int
    registered: bool
    email_token: str | None
