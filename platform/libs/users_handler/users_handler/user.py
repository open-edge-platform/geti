"""This module implements the User entity."""

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import abc


class UserEntity(metaclass=abc.ABCMeta):
    """
    Base class for users, see `User` for an implementation.
    """

    __name: str
    __is_admin: bool

    @property
    def name(self) -> str:
        """
        Returns the user name
        """
        return self.__name

    @name.setter
    def name(self, value: str):
        self.__name = value

    @property
    def is_admin(self) -> bool:
        """
        Return information if current user is Administrator
        """
        return self.__is_admin

    @is_admin.setter
    def is_admin(self, value: bool):
        self.__is_admin = value


class User(UserEntity):
    """
    This class represents a user

    :param name: user name that's uniquely identifying
    :param is_admin: boolean information if user is administrator or not
    :param uid: id of user
    """

    def __init__(self, is_admin: bool = False, **kwargs) -> None:
        self.is_admin = is_admin
        self.name = kwargs.get("name")  # type: ignore
        self.uid = kwargs.get("uid")

    def __repr__(self) -> str:
        return f"User(name='{self.name}')"

    def __eq__(self, other: object):  # noqa: Q000, RUF100
        if not isinstance(other, User):
            return False
        return self.name == other.name and self.uid == other.uid

    @classmethod
    def from_dict(cls, body: dict) -> "User":  # noqa: Q000, RUF100
        """
        Returns User base on id and name
        """
        return cls(uid=body["id"], name=body["name"])


class NullUser(User):
    """Representation of 'user not found'"""

    def __init__(self) -> None:
        super().__init__(name="")

    def __repr__(self) -> str:
        return "NullUser()"
