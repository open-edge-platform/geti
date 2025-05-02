# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module contains utility functions related to Enums."""

from enum import Enum


def get_enum_names(enum_cls: type[Enum]) -> list[str]:
    """Returns a list containing the names of all members of the Enum class passed as `enum_cls`.

    :param enum_cls: The Enum class to get the names of its members.
    :return: The list of names of all members of the Enum class passed as `enum_cls`.
    """
    return [member.name for member in enum_cls]
