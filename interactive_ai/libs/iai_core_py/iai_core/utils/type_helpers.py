# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
This module implements utilities to deal with types (conversions and type-checking)
"""

from collections.abc import Sequence
from typing import TypeVar

T = TypeVar("T")
SequenceOrSet = Sequence[T] | set[T] | frozenset[T]


def str2bool(text: str) -> bool:
    """
    Converts a string to a boolean based on common true/false representations.
    Recognizes the following as True: {"y", "yes", "t", "true", "on", "1"}
    Recognizes the following as False: {"n", "no", "f", "false", "off", "0"}
    Raises ValueError for any other inputs.
    This is similar to the behavior of distutils.util.strtobool.

    :param text: string to convert to boolean
    :return: boolean of the input string
    :raises ValueError: if the logical value cannot be determined

    """

    TRUE_SET = {"y", "yes", "t", "true", "on", "1"}
    FALSE_SET = {"n", "no", "f", "false", "off", "0"}
    buf_input = text.lower()
    if buf_input in TRUE_SET:
        return True
    if buf_input in FALSE_SET:
        return False
    raise ValueError(f"Cannot convert {text} to boolean. Expected one of {TRUE_SET} or {FALSE_SET}")
