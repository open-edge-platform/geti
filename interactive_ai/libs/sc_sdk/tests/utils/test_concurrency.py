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

import pytest

from sc_sdk.utils.concurrency import TimeoutLock


@pytest.mark.ScSdkComponent
class TestTimeoutLock:
    def test_timeout_lock(self) -> None:
        """
        Test the TimeoutLock class

        Steps:
         1. Instantiate the lock
         2. Check that the lock can be explicitly acquired and released
         3. Check that the lock can be acquired via context manager, and
            implicitly released
         4. Check that a TimeoutError is raised when the lock is already taken
        """
        timeout_lock = TimeoutLock(timeout=0.001)
        assert not timeout_lock._lock.locked()  # type: ignore

        timeout_lock.acquire()
        assert timeout_lock._lock.locked()  # type: ignore
        timeout_lock.release()
        assert not timeout_lock._lock.locked()  # type: ignore

        with timeout_lock:
            assert timeout_lock._lock.locked()  # type: ignore
        assert not timeout_lock._lock.locked()  # type: ignore

        timeout_lock.acquire()
        with pytest.raises(TimeoutError), timeout_lock:
            pass
        timeout_lock.release()
