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

"""Utils for multi-threading and concurrency"""

import threading


class TimeoutLock:
    """
    Wrapper around threading.Lock or threading.RLock to use the timeout functionality in
    a context manager.

    :param timeout: Timeout in seconds
    :param use_rlock: boolean if RLock should be used instead of a Lock

    Usage:
        >>> lock = TimeoutLock(timeout=3)
        >>> try:
        >>>     with lock:
        >>>         ...  # success
        >>> except TimeoutError:
        >>>     ...      # failure
    """

    def __init__(self, timeout: float, use_rlock: bool = False) -> None:
        self._lock: threading.Lock | threading.RLock
        if use_rlock:
            self._lock = threading.RLock()
        else:
            self._lock = threading.Lock()
        self._timeout = timeout

    def acquire(self) -> bool:
        """Acquire the lock explicitly"""
        return self._lock.acquire(timeout=self._timeout)

    def release(self) -> None:
        """Release the lock explicitly"""
        self._lock.release()

    def __enter__(self):
        """
        Called when entering the context.

        :return: the acquired threading.Lock object
        :raises TimeoutError: if the lock cannot be acquired within timeout
        """
        lock_acquired = self._lock.acquire(timeout=self._timeout)
        if lock_acquired:
            return self._lock
        raise TimeoutError(f"Failed to acquire lock within timeout ({self._timeout})")

    def __exit__(self, exc_type, exc_val, exc_tb):  # noqa: ANN001
        """Called when leaving the context"""
        self._lock.release()
