# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE


from pydantic import BaseModel, Field

from users_handler.users_handler import UserRole, UserType
from users_handler.validation import MAX_INPUT_LENGTH


class UserModel(BaseModel):
    uid: str = Field(max_length=MAX_INPUT_LENGTH)
    name: str = Field(max_length=MAX_INPUT_LENGTH)
    mail: str = Field(max_length=MAX_INPUT_LENGTH)
    registered: bool
    roles: list[UserRole] | None = Field(None, exclude=False)

    @classmethod
    def map_from_ldap(cls, user: UserType):
        return cls(
            uid=user["uid"],
            name=user["name"],  # type: ignore
            mail=user["mail"],  # type: ignore
            registered=user["registered"],
            roles=user["roles"],
        )
