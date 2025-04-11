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
"""This module time lru cache"""

import sys
import time
from functools import lru_cache, wraps

# Disable time based caching for test cases.
USE_CACHING = True
if "pytest" in sys.modules:
    USE_CACHING = False


def timed_lru_cache(_func=None, *, seconds: int = 5, maxsize: int = 128, typed: bool = False):  # noqa: ANN001, ANN201
    """
    Wrapper for lru cache that is only valid for the passed amount of seconds. If an
    item would be retrieved after the time has expired, the whole cache is cleared.

    :param seconds: Amount of seconds after which the cache is cleared
    :param maxsize: Amount of items to be kept in the lru cache
    :param typed:  If True, arguments of different types will be cached separately.
    """

    def wrapper_cache(func):  # noqa: ANN001
        func = lru_cache(maxsize=maxsize, typed=typed)(func)
        func.delta = seconds * 10**9
        func.expiration = time.monotonic_ns() + func.delta

        @wraps(func)
        def wrapped_func(*args, **kwargs):
            if time.monotonic_ns() >= func.expiration or not USE_CACHING:
                func.cache_clear()
                func.expiration = time.monotonic_ns() + func.delta
            return func(*args, **kwargs)

        wrapped_func.cache_info = func.cache_info
        wrapped_func.cache_clear = func.cache_clear
        return wrapped_func

    if _func is None:
        return wrapper_cache
    return wrapper_cache(_func)
