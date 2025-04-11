# INTEL CONFIDENTIAL
#
# Copyright (C) 2023 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and
# your use of them is governed by the express license under which they were provided to
# you ("License"). Unless the License provides otherwise, you may not use, modify, copy,
# publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is,
# with no express or implied warranties, other than those that are expressly stated
# in the License.
"""
This module contains util functions for iteration
"""

import itertools
from collections.abc import Callable, Iterable, Iterator
from functools import reduce
from typing import Any

MAX_CHUNK_SIZE = 10000


def grouper(iterable: Iterable[Any], chunk_size: int = MAX_CHUNK_SIZE) -> Iterator[list[Any]]:
    """
    Groups items from an iterable into chunks of size "chunk_size".

    :param iterable: An iterable containing the items to be grouped.
    :param chunk_size: The desired size of each chunk.
    :yields: A list containing each chunk of items.
    :raises: ValueError if chunk_size <= 0
    """
    if chunk_size <= 0:
        raise ValueError("Invalid chunk_size, only values > 0 are allowed.")
    iterator = iter(iterable)
    while chunk := list(itertools.islice(iterator, chunk_size)):
        yield chunk


def multi_map(iterable: Iterable[Any], *functions: Callable[[Any], Any]) -> Iterable[Any]:
    """
    Enhanced version of map(...) that supports multiple functions to be applied in cascade on the given iterable.

    :param iterable: Iterable containing the items to be mapped
    :param functions: One or more unary functions to transform the input elements individually.
        These functions are applied in cascade, in the same order as declared.
    :return: Iterable with the input elements after applying the transformation(s)
    """
    return reduce(lambda acc, fn: map(fn, acc), functions, iterable)
